"""Test cơ bản cho SBI Smart Agent (chạy ở demo mode, không gọi mạng).

Lưu ý: phải bỏ ANTHROPIC_API_KEY khỏi môi trường TRƯỚC khi import app để
buộc hệ thống chạy demo mode (truy hồi câu trả lời từ dataset).
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.pop("ANTHROPIC_API_KEY", None)  # ép demo mode
os.environ.pop("SBI_LEADS_WEBHOOK_URL", None)  # không gọi webhook khi test
os.environ["SBI_USE_FIRESTORE"] = "0"  # ép FileStore khi test
os.environ["SBI_USE_SECRET_MANAGER"] = "0"  # tắt Secret Manager khi test
os.environ["SBI_ADMIN_TOKEN"] = "test-token"  # bật admin để test

# Dùng file tạm (slate sạch) để không tạo rác trong repo
_tmp = Path(tempfile.gettempdir())
_leads = _tmp / "sbi_test_leads.jsonl"
_qa = _tmp / "sbi_test_qa_overrides.jsonl"
_cfg = _tmp / "sbi_test_app_settings.json"
_stats = _tmp / "sbi_test_stats.json"
for _f in (_leads, _qa, _cfg, _stats):
    _f.unlink(missing_ok=True)
os.environ["SBI_LEADS_FILE"] = str(_leads)
os.environ["SBI_QA_OVERRIDES_FILE"] = str(_qa)
os.environ["SBI_SETTINGS_FILE"] = str(_cfg)
os.environ["SBI_STATS_FILE"] = str(_stats)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ADMIN = {"X-Admin-Token": "test-token"}

from fastapi.testclient import TestClient  # noqa: E402

from app.knowledge import (  # noqa: E402
    build_system_prompt,
    get_suggested_questions,
    load_qa_items,
)
from app.main import app  # noqa: E402

client = TestClient(app)


# ----------------------------- Tri thức -----------------------------


def test_load_qa_items():
    items = load_qa_items()
    assert len(items) == 50, "Phải nạp đủ 50 cặp Q&A"
    assert all(it.question and it.answer for it in items)
    assert all(it.id.startswith("sbi-") for it in items)


def test_system_prompt_contains_knowledge():
    prompt = build_system_prompt()
    assert "SBI" in prompt
    assert "131 tín chỉ" in prompt  # một dữ kiện đặc trưng trong dataset
    assert "QUY TẮC TRẢ LỜI" in prompt


def test_admissions_topics_present():
    """Các chủ đề tuyển sinh hay được hỏi đã có trong kho tri thức."""
    questions = " ".join(it.question.lower() for it in load_qa_items())
    for kw in ["học phí", "phương thức", "điểm chuẩn", "học bổng", "hồ sơ", "liên hệ"]:
        assert kw in questions, f"Thiếu Q&A về '{kw}'"


def test_suggestions_not_empty():
    assert len(get_suggested_questions()) > 0


# ----------------------------- API -----------------------------


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["api_key_configured"] is False  # demo mode


def test_suggestions_endpoint():
    r = client.get("/api/suggestions")
    assert r.status_code == 200
    assert isinstance(r.json()["suggestions"], list)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "SBI Smart Agent" in r.text


def test_chat_demo_mode_returns_answer():
    r = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "Chương trình SBI là gì?"}]},
    )
    assert r.status_code == 200
    text = r.text.strip()
    assert len(text) > 0
    # demo mode truy hồi đúng nội dung về bằng cấp / tín chỉ
    assert "Thương mại điện tử" in text or "tín chỉ" in text


def test_chat_out_of_scope_guides_to_contact():
    r = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "xqzptlmn 99999 zzz"}]},
    )
    assert r.status_code == 200
    assert len(r.text.strip()) > 0


# ----------------------------- Lead capture -----------------------------


def test_lead_valid():
    r = client.post(
        "/api/lead",
        json={
            "name": "Nguyễn Văn A",
            "phone": "0901234567",
            "email": "a@example.com",
            "note": "Quan tâm học phí",
            "context": [{"role": "user", "content": "Học phí bao nhiêu?"}],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["id"].startswith("lead-")


def test_lead_missing_name():
    r = client.post("/api/lead", json={"name": "", "phone": "0901234567"})
    assert r.status_code == 422


def test_lead_invalid_phone():
    r = client.post("/api/lead", json={"name": "Trần B", "phone": "123"})
    assert r.status_code == 422


# ----------------------------- Admin -----------------------------


def test_admin_requires_token():
    assert client.get("/api/admin/qa").status_code == 401
    assert client.get("/api/admin/leads").status_code == 401


def test_admin_check():
    r = client.get("/api/admin/check", headers=ADMIN)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["storage"] == "file"


def test_admin_qa_add_edit_delete():
    # Thêm mới
    r = client.post(
        "/api/admin/qa",
        headers=ADMIN,
        json={"category": "tuyen_sinh", "question": "Câu hỏi kiểm thử?", "answer": "Trả lời kiểm thử."},
    )
    assert r.status_code == 200
    new_id = r.json()["item"]["id"]
    assert new_id.startswith("sbi-x")

    # Có trong danh sách với nguồn "custom"
    items = {it["id"]: it for it in client.get("/api/admin/qa", headers=ADMIN).json()["items"]}
    assert items[new_id]["source"] == "custom"

    # Cập nhật -> phản ánh vào system prompt
    r = client.post(
        "/api/admin/qa",
        headers=ADMIN,
        json={"id": new_id, "category": "tuyen_sinh", "question": "Câu hỏi kiểm thử?", "answer": "Đã cập nhật nội dung."},
    )
    assert r.status_code == 200
    assert "Đã cập nhật nội dung." in build_system_prompt()

    # Xoá
    assert client.delete(f"/api/admin/qa/{new_id}", headers=ADMIN).status_code == 200
    after = {it["id"] for it in client.get("/api/admin/qa", headers=ADMIN).json()["items"]}
    assert new_id not in after


def test_admin_qa_validation():
    r = client.post("/api/admin/qa", headers=ADMIN, json={"question": "x", "answer": ""})
    assert r.status_code == 422


def test_admin_leads_list():
    r = client.get("/api/admin/leads", headers=ADMIN)
    assert r.status_code == 200
    assert isinstance(r.json()["leads"], list)


def test_admin_page_served():
    r = client.get("/admin")
    assert r.status_code == 200


# ----------------------------- Admin: cấu hình -----------------------------


def test_admin_settings_get():
    r = client.get("/api/admin/settings", headers=ADMIN)
    assert r.status_code == 200
    body = r.json()
    assert body["api_key"]["configured"] is False  # demo, chưa có key
    assert body["api_key"]["secret_manager_available"] is False
    assert body["model"]
    assert isinstance(body["available_models"], list) and body["available_models"]
    assert body["storage"] == "file"


def test_admin_settings_set_model():
    r = client.post(
        "/api/admin/settings", headers=ADMIN, json={"model": "claude-haiku-4-5-20251001"}
    )
    assert r.status_code == 200
    assert r.json()["model"] == "claude-haiku-4-5-20251001"
    # phản ánh ở lần đọc sau
    assert client.get("/api/admin/settings", headers=ADMIN).json()["model"] == "claude-haiku-4-5-20251001"
    # trả lại mặc định để không ảnh hưởng test khác
    client.post("/api/admin/settings", headers=ADMIN, json={"model": "claude-sonnet-4-6"})


def test_admin_settings_api_key_without_secret_manager():
    # Secret Manager bị tắt khi test -> phải báo 503 rõ ràng, không phải 500
    r = client.post("/api/admin/settings", headers=ADMIN, json={"api_key": "sk-ant-test"})
    assert r.status_code == 503


def test_admin_settings_validation():
    assert client.post("/api/admin/settings", headers=ADMIN, json={"temperature": 5}).status_code == 422
    assert client.post("/api/admin/settings", headers=ADMIN, json={"max_tokens": 0}).status_code == 422


def test_admin_test_connection_demo():
    r = client.post("/api/admin/settings/test", headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["ok"] is False  # chưa có key


def test_admin_settings_requires_token():
    assert client.get("/api/admin/settings").status_code == 401


# ----------------------- Thống kê & câu hỏi liên quan -----------------------


def test_related_endpoint():
    r = client.post("/api/related", json={"question": "Học phí chương trình bao nhiêu?"})
    assert r.status_code == 200
    rel = r.json()["related"]
    assert isinstance(rel, list) and 1 <= len(rel) <= 3
    assert all(isinstance(q, str) and q for q in rel)


def test_related_handles_empty():
    r = client.post("/api/related", json={"question": ""})
    assert r.status_code == 200
    assert isinstance(r.json()["related"], list)


def test_question_recorded_in_stats():
    # Hỏi cùng một câu nhiều lần -> lượt đếm tăng
    for _ in range(3):
        client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "Cơ hội việc làm sau khi tốt nghiệp thế nào?"}]},
        )
    body = client.get("/api/admin/stats", headers=ADMIN).json()
    assert body["total_questions"] >= 3
    assert body["distinct_questions"] >= 1
    assert body["top"] and body["top"][0]["count"] >= 1
    assert "question" in body["top"][0] and "count" in body["top"][0]


def test_stats_requires_token():
    assert client.get("/api/admin/stats").status_code == 401


def test_suggestions_reflect_faq():
    r = client.get("/api/suggestions")
    assert r.status_code == 200
    sug = r.json()["suggestions"]
    assert isinstance(sug, list) and 0 < len(sug) <= 6

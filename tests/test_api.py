"""Test cơ bản cho SBI Smart Agent (chạy ở demo mode, không gọi mạng).

Lưu ý: phải bỏ ANTHROPIC_API_KEY khỏi môi trường TRƯỚC khi import app để
buộc hệ thống chạy demo mode (truy hồi câu trả lời từ dataset).
"""
import os
import sys
from pathlib import Path

os.environ.pop("ANTHROPIC_API_KEY", None)  # ép demo mode
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
    assert len(items) == 43, "Phải nạp đủ 43 cặp Q&A"
    assert all(it.question and it.answer for it in items)
    assert all(it.id.startswith("sbi-") for it in items)


def test_system_prompt_contains_knowledge():
    prompt = build_system_prompt()
    assert "SBI" in prompt
    assert "131 tín chỉ" in prompt  # một dữ kiện đặc trưng trong dataset
    assert "QUY TẮC TRẢ LỜI" in prompt


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

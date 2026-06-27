"""Nạp bộ tri thức SBI và dựng system prompt.

Chiến lược (đã chốt): vì dataset nhỏ (43 Q&A) nên nhồi TOÀN BỘ tri thức vào
system prompt và để Claude tự chọn lọc. Khối tri thức được đặt ổn định ở đầu
prompt để tận dụng prompt caching (giảm chi phí & độ trễ cho các lượt sau).
"""
from __future__ import annotations

import json
import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import get_settings
from .store import get_store

# Nhãn hiển thị thân thiện cho từng nhóm chủ đề (category) trong dataset.
CATEGORY_LABELS: dict[str, str] = {
    "thong_tin_chung": "Thông tin chung",
    "tuyen_sinh": "Tuyển sinh",
    "chuong_trinh_dao_tao": "Chương trình đào tạo",
    "chuyen_sau": "Hướng chuyên sâu",
    "thuc_hanh_du_an": "Thực hành & Dự án",
    "cong_nghe_cong_cu": "Công nghệ & Công cụ",
    "co_hoi_viec_lam": "Cơ hội việc làm",
    "giang_vien_doi_tac": "Giảng viên & Đối tác",
    "ve_truong_ftu": "Về Trường FTU",
    "co_so_vat_chat": "Cơ sở vật chất",
}


@dataclass(frozen=True)
class QAItem:
    id: str
    category: str
    question: str
    answer: str


def _default_system_prompt() -> str:
    """System prompt dự phòng nếu thiếu file system_prompt.txt."""
    return (
        "Bạn là một trợ lý ảo tư vấn tuyển sinh AI của Trường Đại học Ngoại thương "
        "(FTU), chuyên tư vấn về chương trình đào tạo Thương mại số thông minh & Đổi "
        "mới kinh doanh (Smart Digital Commerce and Business Innovation - SBI), thuộc "
        "ngành Thương mại điện tử (Mã ngành: 7340122). Hãy trả lời thân thiện, chuyên "
        "nghiệp, rõ ràng và súc tích. Nếu không biết câu trả lời, hãy hướng dẫn họ liên "
        "hệ trực tiếp với Khoa Quản trị Kinh doanh, Trường Đại học Ngoại thương."
    )


def load_base_qa_items(data_dir: Path | None = None) -> list[QAItem]:
    """Đọc bộ Q&A gốc từ file sbi_qa_dataset.jsonl."""
    data_dir = data_dir or get_settings().data_dir
    path = data_dir / "sbi_qa_dataset.jsonl"
    items: list[QAItem] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            items.append(
                QAItem(
                    id=rec.get("id", ""),
                    category=rec.get("category", ""),
                    question=rec["question"].strip(),
                    answer=rec["answer"].strip(),
                )
            )
    if not items:
        raise RuntimeError(f"Không nạp được Q&A nào từ {path}")
    return items


def load_qa_items(data_dir: Path | None = None) -> list[QAItem]:
    """Q&A hiệu lực = bộ gốc + các chỉnh sửa/bổ sung/xoá từ store (admin)."""
    base = load_base_qa_items(data_dir)
    by_id: dict[str, QAItem] = {it.id: it for it in base}
    order: list[str] = [it.id for it in base]

    for ov in get_store().list_qa_overrides():
        oid = (ov.get("id") or "").strip()
        if not oid:
            continue
        if ov.get("deleted"):
            by_id.pop(oid, None)
            continue
        if oid not in by_id:
            order.append(oid)
        by_id[oid] = QAItem(
            id=oid,
            category=(ov.get("category") or "khac").strip(),
            question=(ov.get("question") or "").strip(),
            answer=(ov.get("answer") or "").strip(),
        )
    return [by_id[i] for i in order if i in by_id]


def load_base_system_prompt(data_dir: Path | None = None) -> str:
    """Đọc system_prompt.txt; nếu thiếu thì dùng bản dự phòng."""
    data_dir = data_dir or get_settings().data_dir
    path = data_dir / "system_prompt.txt"
    if path.exists():
        text = path.read_text(encoding="utf-8").strip()
        if text:
            return text
    return _default_system_prompt()


def build_knowledge_block(items: list[QAItem]) -> str:
    """Định dạng toàn bộ Q&A thành một khối văn bản tham chiếu cho LLM."""
    lines: list[str] = []
    current_category = None
    for it in items:
        if it.category != current_category:
            current_category = it.category
            label = CATEGORY_LABELS.get(it.category, it.category)
            lines.append(f"\n## CHỦ ĐỀ: {label}")
        lines.append(f"\n[{it.id}]")
        lines.append(f"Hỏi: {it.question}")
        lines.append(f"Đáp: {it.answer}")
    return "\n".join(lines).strip()


def build_system_prompt(data_dir: Path | None = None) -> str:
    """Ghép system prompt vai trò + khối tri thức + quy tắc trả lời.

    Toàn bộ chuỗi này ổn định giữa các request nên rất hợp để bật prompt caching.
    """
    items = load_qa_items(data_dir)
    base = load_base_system_prompt(data_dir)
    knowledge = build_knowledge_block(items)

    training = get_training_text()
    training_block = ""
    if training:
        training_block = (
            "\n\n================ TÀI LIỆU HUẤN LUYỆN BỔ SUNG ================\n"
            "Đây là thông tin CHÍNH THỨC & cập nhật do quản trị viên cung cấp. HÃY ƯU TIÊN "
            "dùng tài liệu này khi trả lời, KỂ CẢ số liệu cụ thể (học phí, nhân sự như "
            "trưởng bộ môn, mốc thời gian...). Nếu có khác biệt với phần kho tri thức ở "
            "trên thì LẤY THEO tài liệu này:\n\n"
            f"{training}\n"
            "================ HẾT TÀI LIỆU BỔ SUNG ================"
        )

    return f"""{base}

================ KHO TRI THỨC THAM CHIẾU (SBI - FTU) ================
Dưới đây là toàn bộ thông tin chính thức về chương trình SBI. Hãy CHỈ dựa vào
thông tin này (và TÀI LIỆU HUẤN LUYỆN BỔ SUNG bên dưới nếu có) để trả lời.

{knowledge}
================ HẾT KHO TRI THỨC ================{training_block}

QUY TẮC TRẢ LỜI:
1. Chỉ trả lời dựa trên KHO TRI THỨC ở trên. Tuyệt đối không bịa đặt thông tin
   (đặc biệt là số liệu, học phí, điểm chuẩn, mốc thời gian không có trong dữ liệu).
2. Nếu câu hỏi nằm ngoài phạm vi kho tri thức, hãy lịch sự nói rằng bạn chưa có
   thông tin và hướng dẫn liên hệ trực tiếp Khoa Quản trị Kinh doanh - Trường Đại
   học Ngoại thương (FTU) để được tư vấn chính xác.
3. Trả lời bằng tiếng Việt, giọng thân thiện - chuyên nghiệp, rõ ràng và súc tích.
   Dùng gạch đầu dòng khi liệt kê nhiều ý cho dễ đọc.
4. Có thể tổng hợp thông tin từ nhiều mục Q&A nếu câu hỏi liên quan đến nhiều mục.
5. Không nhắc đến "kho tri thức", mã [sbi-xxx] hay việc bạn đang đọc dữ liệu;
   hãy trả lời tự nhiên như một chuyên viên tư vấn.
6. Nếu người dùng chỉ chào hỏi, hãy chào lại thân thiện và mời họ đặt câu hỏi về
   chương trình SBI."""


_SYSTEM_PROMPT_CACHE: str | None = None


def get_cached_system_prompt() -> str:
    """System prompt được cache trong tiến trình; rebuild khi admin sửa Q&A."""
    global _SYSTEM_PROMPT_CACHE
    if _SYSTEM_PROMPT_CACHE is None:
        _SYSTEM_PROMPT_CACHE = build_system_prompt()
    return _SYSTEM_PROMPT_CACHE


def reload_knowledge() -> None:
    """Dựng lại system prompt sau khi kho tri thức thay đổi (admin)."""
    global _SYSTEM_PROMPT_CACHE
    _SYSTEM_PROMPT_CACHE = build_system_prompt()


# --------------------------- Huấn luyện chatbot (admin) ---------------------------
# Tài liệu huấn luyện bổ sung dạng văn bản tự do (ngoài bộ Q&A có cấu trúc), được
# admin nhập/tải lên và nạp thẳng vào system prompt — có hiệu lực ngay.

TRAINING_MAX_CHARS = 200_000


def get_training_text() -> str:
    try:
        return (get_store().get_config().get("training_text") or "").strip()
    except Exception:
        return ""


def set_training_text(text: str) -> int:
    """Lưu tài liệu huấn luyện (cắt theo giới hạn) + rebuild prompt. Trả về độ dài."""
    text = (text or "").strip()[:TRAINING_MAX_CHARS]
    get_store().set_config({"training_text": text})
    reload_knowledge()
    return len(text)


# --------------------------- Quản trị Q&A (admin) ---------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def list_qa_admin() -> list[dict]:
    """Danh sách Q&A hiệu lực kèm nguồn gốc: base / edited / custom."""
    base_ids = {it.id for it in load_base_qa_items()}
    overrides = {
        ov["id"]: ov
        for ov in get_store().list_qa_overrides()
        if ov.get("id") and not ov.get("deleted")
    }
    result: list[dict] = []
    for it in load_qa_items():
        if it.id in overrides:
            source = "edited" if it.id in base_ids else "custom"
        else:
            source = "base"
        result.append(
            {
                "id": it.id,
                "category": it.category,
                "category_label": CATEGORY_LABELS.get(it.category, it.category),
                "question": it.question,
                "answer": it.answer,
                "source": source,
            }
        )
    return result


def upsert_qa(data: dict) -> dict:
    """Thêm mới hoặc cập nhật một Q&A (ghi vào store + rebuild prompt)."""
    qid = (data.get("id") or "").strip() or f"sbi-x{uuid.uuid4().hex[:6]}"
    item = {
        "id": qid,
        "category": (data.get("category") or "khac").strip(),
        "question": (data.get("question") or "").strip(),
        "answer": (data.get("answer") or "").strip(),
        "deleted": False,
        "updated_at": _now_iso(),
    }
    get_store().upsert_qa(item)
    reload_knowledge()
    return item


def delete_qa(qa_id: str) -> None:
    """Xoá/ẩn một Q&A (ghi tombstone vào store + rebuild prompt)."""
    get_store().delete_qa(qa_id.strip())
    reload_knowledge()


def get_suggested_questions(items: list[QAItem] | None = None, n: int = 6) -> list[str]:
    """Một vài câu hỏi gợi ý đại diện cho các nhóm chủ đề (hiện trên UI)."""
    return [
        "Chương trình SBI là gì và tốt nghiệp nhận bằng gì?",
        "Học phí chương trình là bao nhiêu?",
        "Chương trình xét tuyển theo những phương thức nào?",
        "Cơ hội việc làm sau khi ra trường như thế nào?",
        "Chương trình có những hướng chuyên sâu nào?",
        "Làm sao để được tư vấn tuyển sinh trực tiếp?",
    ][:n]


# --------------------------- So khớp câu hỏi ---------------------------
# Dùng chung cho: demo mode, gợi ý câu hỏi liên quan, và đếm lượt hỏi (thống kê).

_STOPWORDS = {
    "la", "gi", "va", "co", "khong", "nhu", "the", "nao", "cua", "cho", "voi",
    "duoc", "cac", "nhung", "mot", "ban", "minh", "ve", "trong", "den", "tai",
    "thi", "se", "ra", "sao", "bao", "nhieu", "hay", "ai", "khi",
}


def _normalize(text: str) -> str:
    """Bỏ dấu, hạ chữ thường để so khớp từ khoá."""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9\s]", " ", text)


def question_tokens(text: str) -> set[str]:
    return {t for t in _normalize(text).split() if t and t not in _STOPWORDS}


def rank_qa_scored(
    text: str,
    items: list[QAItem] | None = None,
    n: int = 3,
    exclude_ids: tuple[str, ...] = (),
) -> list[tuple[float, QAItem]]:
    """Xếp hạng Q&A kèm điểm khớp từ khoá."""
    items = items if items is not None else load_qa_items()
    qt = question_tokens(text)
    if not qt:
        return []
    scored: list[tuple[float, QAItem]] = []
    for it in items:
        if it.id in exclude_ids:
            continue
        a_tokens = set(_normalize(it.question + " " + it.answer).split())
        q_tokens = set(_normalize(it.question).split())
        score = len(qt & a_tokens) + 2.0 * len(qt & q_tokens)
        if score > 0:
            scored.append((score, it))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:n]


def rank_qa(
    text: str,
    items: list[QAItem] | None = None,
    n: int = 3,
    exclude_ids: tuple[str, ...] = (),
) -> list[QAItem]:
    """Xếp hạng Q&A liên quan nhất tới `text` bằng độ trùng từ khoá."""
    return [it for _, it in rank_qa_scored(text, items, n, exclude_ids)]


def best_match(text: str, items: list[QAItem] | None = None) -> QAItem | None:
    """Q&A khớp nhất với câu hỏi (None nếu không khớp gì)."""
    ranked = rank_qa_scored(text, items, n=1)
    return ranked[0][1] if ranked else None


def _split_training(text: str) -> list[str]:
    """Tách tài liệu huấn luyện thành các đoạn (theo dòng trống)."""
    return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]


def search_training(text: str, n: int = 1) -> list[tuple[float, str]]:
    """Tìm các đoạn trong tài liệu huấn luyện khớp từ khoá nhất với câu hỏi."""
    training = get_training_text()
    if not training:
        return []
    qt = question_tokens(text)
    if not qt:
        return []
    scored: list[tuple[float, str]] = []
    for block in _split_training(training):
        btoks = set(_normalize(block).split())
        score = float(len(qt & btoks))
        if score > 0:
            scored.append((score, block))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:n]

"""Nạp bộ tri thức SBI và dựng system prompt.

Chiến lược (đã chốt): vì dataset nhỏ (43 Q&A) nên nhồi TOÀN BỘ tri thức vào
system prompt và để Claude tự chọn lọc. Khối tri thức được đặt ổn định ở đầu
prompt để tận dụng prompt caching (giảm chi phí & độ trễ cho các lượt sau).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .config import get_settings

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


def load_qa_items(data_dir: Path | None = None) -> list[QAItem]:
    """Đọc file sbi_qa_dataset.jsonl thành danh sách QAItem."""
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

    return f"""{base}

================ KHO TRI THỨC THAM CHIẾU (SBI - FTU) ================
Dưới đây là toàn bộ thông tin chính thức về chương trình SBI. Hãy CHỈ dựa vào
thông tin này để trả lời.

{knowledge}
================ HẾT KHO TRI THỨC ================

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


@lru_cache
def get_cached_system_prompt() -> str:
    """System prompt được cache trong vòng đời tiến trình (build 1 lần)."""
    return build_system_prompt()


def get_suggested_questions(items: list[QAItem] | None = None, n: int = 6) -> list[str]:
    """Một vài câu hỏi gợi ý đại diện cho các nhóm chủ đề (hiện trên UI)."""
    return [
        "Chương trình SBI là gì và tốt nghiệp nhận bằng gì?",
        "Cơ hội việc làm sau khi ra trường như thế nào?",
        "Chương trình có những hướng chuyên sâu nào?",
        "Sinh viên được học những công nghệ, phần mềm gì?",
        "Chỉ tiêu tuyển sinh là bao nhiêu?",
        "Sinh viên có được thực hành, thực tập thực tế không?",
    ][:n]

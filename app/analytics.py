"""Thống kê câu hỏi & gợi ý câu hỏi liên quan.

- `record_question()`: mỗi câu hỏi của người dùng được so khớp với một Q&A và
  tăng bộ đếm "số lượt đã hỏi" (lưu qua store: Firestore/file).
- `top_questions()` / `stats_summary()`: câu hỏi thường gặp + số lượt (cho /admin).
- `related_questions()`: 3 câu hỏi liên quan để gợi ý sau khi trả lời.
"""
from __future__ import annotations

import logging

from .knowledge import best_match, get_suggested_questions, rank_qa
from .store import get_store

logger = logging.getLogger("sbi.analytics")


def record_question(text: str) -> None:
    """Đếm lượt hỏi cho Q&A khớp nhất (bỏ qua câu ngoài phạm vi)."""
    text = (text or "").strip()
    if not text:
        return
    match = best_match(text)
    if match is None:
        logger.info("Câu hỏi ngoài phạm vi: %s", text[:120])
        return
    try:
        get_store().incr_question(match.id, match.question)
    except Exception as exc:  # thống kê không được làm hỏng luồng chat
        logger.warning("Không ghi được thống kê câu hỏi: %s", exc)


def _sorted_stats() -> list[dict]:
    try:
        stats = get_store().question_stats()
    except Exception as exc:
        logger.warning("Không đọc được thống kê: %s", exc)
        return []
    stats.sort(key=lambda r: int(r.get("count", 0) or 0), reverse=True)
    return stats


def top_questions(n: int = 10) -> list[dict]:
    return _sorted_stats()[:n]


def stats_summary(n: int = 10) -> dict:
    stats = _sorted_stats()
    return {
        "total_questions": sum(int(r.get("count", 0) or 0) for r in stats),
        "distinct_questions": len(stats),
        "top": stats[:n],
    }


def related_questions(text: str, n: int = 3) -> list[str]:
    """Tối đa `n` câu hỏi liên quan, loại trừ câu khớp nhất (vừa được trả lời)."""
    ranked = rank_qa(text, n=n + 3)
    questions = [it.question for it in ranked]
    answered = questions[0] if questions else None
    related = list(questions[1:])

    if len(related) < n:
        # Đệm thêm bằng câu thường gặp, rồi tới gợi ý tĩnh (tránh trùng/đã trả lời)
        extra = [r.get("question", "") for r in top_questions(10)]
        extra += get_suggested_questions()
        for q in extra:
            if q and q != answered and q not in related:
                related.append(q)
            if len(related) >= n:
                break
    return related[:n]

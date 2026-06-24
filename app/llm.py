"""Tầng giao tiếp với Claude API (Anthropic).

- Bật **prompt caching** cho khối system prompt (chứa toàn bộ tri thức) để
  giảm chi phí & độ trễ ở các lượt sau.
- Trả lời theo dạng **streaming** (sinh chữ dần) cho trải nghiệm mượt.
- Có **demo mode**: nếu chưa cấu hình ANTHROPIC_API_KEY, hệ thống tự truy hồi
  câu trả lời gần nhất từ dataset để app vẫn chạy được (phục vụ thử nghiệm UI).
"""
from __future__ import annotations

import re
from typing import AsyncIterator

from .config import Settings, get_settings
from .knowledge import best_match, get_cached_system_prompt, question_tokens
from .runtime import get_runtime_config

# ----------------------------- Demo mode (không cần API key) -----------------------------


def _demo_reply(user_message: str) -> str:
    """Truy hồi câu trả lời gần nhất bằng so khớp từ khoá (tái dùng matcher chung)."""
    if not question_tokens(user_message):
        return (
            "Xin chào! Mình là trợ lý tư vấn tuyển sinh chương trình SBI - Trường "
            "Đại học Ngoại thương (FTU). Bạn muốn tìm hiểu điều gì về chương trình ạ?"
        )
    match = best_match(user_message)
    if match is None:
        return (
            "Mình chưa có thông tin cho câu hỏi này trong dữ liệu hiện có. Bạn vui "
            "lòng liên hệ trực tiếp Khoa Quản trị Kinh doanh - Trường Đại học Ngoại "
            "thương (FTU) để được tư vấn chính xác nhé!"
        )
    return match.answer


# ----------------------------- Tích hợp Claude -----------------------------


def _build_messages(history: list[dict], settings: Settings) -> list[dict]:
    """Chuẩn hoá & cắt bớt lịch sử hội thoại theo cấu hình."""
    cleaned: list[dict] = []
    for m in history:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            cleaned.append({"role": role, "content": content})

    # Giữ lại N lượt gần nhất (mỗi lượt ~2 message).
    max_msgs = settings.max_history_turns * 2
    if len(cleaned) > max_msgs:
        cleaned = cleaned[-max_msgs:]

    # Claude yêu cầu message đầu tiên có role "user".
    while cleaned and cleaned[0]["role"] != "user":
        cleaned.pop(0)
    return cleaned


async def stream_reply(
    history: list[dict], settings: Settings | None = None
) -> AsyncIterator[str]:
    """Sinh câu trả lời theo từng chunk văn bản.

    `history` là danh sách message [{role, content}, ...], message cuối là câu
    hỏi mới của người dùng.
    """
    settings = settings or get_settings()
    messages = _build_messages(history, settings)
    if not messages:
        return

    rc = get_runtime_config()

    # --- Demo mode: chưa có API key ---
    if not rc.has_api_key:
        reply = _demo_reply(messages[-1]["content"])
        # Trả về theo từng cụm nhỏ để UI vẫn có hiệu ứng streaming.
        for chunk in re.findall(r"\S+\s*", reply):
            yield chunk
        return

    # --- Gọi Claude thật ---
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=rc.api_key)
    system_blocks = [
        {
            "type": "text",
            "text": get_cached_system_prompt(),
            "cache_control": {"type": "ephemeral"},  # bật prompt caching
        }
    ]

    async with client.messages.stream(
        model=rc.model,
        max_tokens=rc.max_tokens,
        temperature=rc.temperature,
        system=system_blocks,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text

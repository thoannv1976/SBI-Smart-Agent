"""SBI Smart Agent - FastAPI backend.

Phục vụ giao diện chat tĩnh và API hội thoại (streaming) nối với Claude.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import get_settings
from .knowledge import get_suggested_questions
from .llm import stream_reply

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sbi")

settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="SBI Smart Agent",
    description="Chatbot tư vấn tuyển sinh chương trình Thương mại số thông minh & "
    "Đổi mới kinh doanh (SBI) - Trường Đại học Ngoại thương (FTU).",
    version="1.0.0",
)

# Cho phép gọi từ trang khác (nếu sau này nhúng widget ở domain khác).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------- Schemas -------------------------------


class Message(BaseModel):
    role: str = Field(..., description='"user" hoặc "assistant"')
    content: str


class ChatRequest(BaseModel):
    messages: list[Message] = Field(..., description="Toàn bộ lịch sử hội thoại")


# ------------------------------- Routes -------------------------------


@app.get("/healthz")
def healthz() -> dict:
    """Health check cho Cloud Run."""
    return {
        "status": "ok",
        "model": settings.model,
        "api_key_configured": settings.has_api_key,
    }


@app.get("/api/suggestions")
def suggestions() -> dict:
    """Danh sách câu hỏi gợi ý hiển thị trên UI."""
    return {"suggestions": get_suggested_questions()}


@app.post("/api/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    """Nhận lịch sử hội thoại, trả về câu trả lời dạng streaming (text/plain)."""
    history = [m.model_dump() for m in req.messages]

    async def generate():
        try:
            async for chunk in stream_reply(history, settings):
                yield chunk
        except Exception as exc:  # không để lộ chi tiết lỗi cho người dùng cuối
            logger.exception("Lỗi khi sinh câu trả lời: %s", exc)
            yield (
                "\n\n⚠️ Xin lỗi, hệ thống đang gặp sự cố khi xử lý yêu cầu. "
                "Bạn vui lòng thử lại sau ít phút hoặc liên hệ Khoa Quản trị Kinh "
                "doanh - Trường Đại học Ngoại thương (FTU)."
            )

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Trang chủ
@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


# Tài nguyên tĩnh (css/js) phục vụ tại /static/*
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

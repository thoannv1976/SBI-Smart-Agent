"""SBI Smart Agent - FastAPI backend.

Phục vụ giao diện chat tĩnh và API hội thoại (streaming) nối với Claude.
"""
from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import apikey
from .analytics import (
    record_question,
    related_questions,
    stats_summary,
    top_questions,
)
from .config import get_settings
from .knowledge import (
    CATEGORY_LABELS,
    TRAINING_MAX_CHARS,
    delete_qa,
    get_suggested_questions,
    get_training_text,
    list_qa_admin,
    set_training_text,
    upsert_qa,
)
from .leads import save_lead
from .llm import stream_reply
from .portal import get_portal_config, set_portal_config
from .runtime import get_runtime_config
from .store import get_store

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


class RelatedRequest(BaseModel):
    question: str = Field("", description="Câu hỏi vừa được hỏi")


class TrainingRequest(BaseModel):
    text: str = Field("", description="Tài liệu huấn luyện bổ sung (văn bản)")


class PortalConfig(BaseModel):
    hero_title: str = ""
    hero_subtitle: str = ""
    youtube_channel_url: str = ""
    youtube_video_ids: list[str] = Field(default_factory=list)
    lms_url: str = ""
    featured_courses: list[dict] = Field(default_factory=list)
    obe_url: str = ""
    career_test_url: str = ""
    social: dict = Field(default_factory=dict)


class LeadRequest(BaseModel):
    name: str = Field(..., description="Họ và tên")
    phone: str = Field(..., description="Số điện thoại")
    email: str = Field("", description="Email (tuỳ chọn)")
    note: str = Field("", description="Nội dung quan tâm (tuỳ chọn)")
    source: str = Field("web", description="Nguồn lead")
    context: list[Message] = Field(
        default_factory=list, description="Vài tin nhắn gần nhất (tuỳ chọn)"
    )


class QARequest(BaseModel):
    id: str = Field("", description="Để trống nếu thêm mới")
    category: str = Field("khac", description="Mã nhóm chủ đề")
    question: str = Field(..., description="Câu hỏi")
    answer: str = Field(..., description="Câu trả lời")


class SettingsRequest(BaseModel):
    api_key: str = Field("", description="Claude API key (để trống nếu không đổi)")
    model: str = Field("", description="Model Claude (để trống nếu không đổi)")
    max_tokens: int | None = Field(None, description="Độ dài tối đa câu trả lời")
    temperature: float | None = Field(None, description="Độ sáng tạo 0..1")


# ----------------------------- Admin auth -----------------------------


def require_admin(x_admin_token: str = Header(default="")) -> None:
    """Bảo vệ các API /api/admin/* bằng token trong SBI_ADMIN_TOKEN."""
    if not settings.admin_token:
        raise HTTPException(
            status_code=503,
            detail="Trang quản trị chưa được bật. Hãy đặt biến SBI_ADMIN_TOKEN.",
        )
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Token quản trị không hợp lệ.")


# ------------------------------- Routes -------------------------------


@app.get("/healthz")
def healthz() -> dict:
    """Health check cho Cloud Run."""
    rc = get_runtime_config()
    return {
        "status": "ok",
        "model": rc.model,
        "api_key_configured": rc.has_api_key,
    }


@app.get("/api/suggestions")
def suggestions() -> dict:
    """Câu hỏi gợi ý: ưu tiên câu thường gặp (theo lượt hỏi), đệm bằng danh sách tĩnh."""
    merged: list[str] = []
    for q in [t.get("question", "") for t in top_questions(6)] + get_suggested_questions():
        if q and q not in merged:
            merged.append(q)
    return {"suggestions": merged[:6]}


@app.post("/api/related")
def related(req: RelatedRequest) -> dict:
    """Gợi ý tối đa 3 câu hỏi liên quan sau khi trả lời."""
    return {"related": related_questions(req.question, n=3)}


@app.get("/api/faq")
def faq() -> dict:
    """Câu hỏi thường gặp (công khai) kèm số lượt đã hỏi — cho cột FAQ ở trang chat."""
    items: list[dict] = []
    seen: set[str] = set()
    for t in top_questions(12):
        q = (t.get("question") or "").strip()
        if q and q not in seen:
            seen.add(q)
            items.append({"question": q, "count": int(t.get("count", 0) or 0)})
    # Đệm bằng câu gợi ý tĩnh (count 0) để cột không trống khi chưa có dữ liệu
    for q in get_suggested_questions(n=12):
        if q and q not in seen and len(items) < 12:
            seen.add(q)
            items.append({"question": q, "count": 0})
    return {"items": items}


@app.get("/api/portal")
def portal() -> dict:
    """Cấu hình cổng portal (công khai): video, khóa học, link tích hợp, mạng xã hội."""
    return get_portal_config()


@app.post("/api/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    """Nhận lịch sử hội thoại, trả về câu trả lời dạng streaming (text/plain)."""
    history = [m.model_dump() for m in req.messages]

    # Ghi nhận câu hỏi mới nhất để thống kê (offload sang thread, không chặn loop).
    if history and history[-1].get("role") == "user":
        await asyncio.to_thread(record_question, history[-1]["content"])

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


@app.post("/api/lead")
async def create_lead(req: LeadRequest) -> dict:
    """Nhận thông tin đăng ký tư vấn, kiểm tra hợp lệ rồi lưu lại."""
    name = req.name.strip()
    phone = req.phone.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Vui lòng nhập họ và tên.")
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 8 or len(digits) > 15:
        raise HTTPException(status_code=422, detail="Số điện thoại không hợp lệ.")

    payload = req.model_dump()
    payload["context"] = [m.model_dump() for m in req.context]
    lead = await save_lead(payload, settings)
    logger.info("Đã nhận lead %s (%s)", lead["id"], name)
    return {
        "ok": True,
        "id": lead["id"],
        "message": "Cảm ơn bạn! Đội ngũ tư vấn tuyển sinh SBI sẽ liên hệ lại trong thời gian sớm nhất.",
    }


# ------------------------------- Admin API -------------------------------


@app.get("/api/admin/check", dependencies=[Depends(require_admin)])
def admin_check() -> dict:
    """Xác thực token + trả về thông tin nền tảng lưu trữ."""
    return {"ok": True, "storage": get_store().backend}


@app.get("/api/admin/leads", dependencies=[Depends(require_admin)])
async def admin_list_leads() -> dict:
    leads = await asyncio.to_thread(get_store().list_leads)
    return {"count": len(leads), "leads": leads}


@app.get("/api/admin/stats", dependencies=[Depends(require_admin)])
async def admin_stats() -> dict:
    """Thống kê câu hỏi: tổng lượt, số câu khác nhau, top câu thường gặp."""
    return await asyncio.to_thread(stats_summary, 20)


@app.get("/api/admin/portal", dependencies=[Depends(require_admin)])
def admin_get_portal() -> dict:
    return get_portal_config()


@app.post("/api/admin/portal", dependencies=[Depends(require_admin)])
async def admin_set_portal(req: PortalConfig) -> dict:
    cfg = await asyncio.to_thread(set_portal_config, req.model_dump())
    return {"ok": True, "portal": cfg}


# --------------------------- Huấn luyện chatbot ---------------------------


def _extract_pdf(data: bytes) -> str:
    import io

    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


@app.get("/api/admin/training", dependencies=[Depends(require_admin)])
def admin_get_training() -> dict:
    return {"text": get_training_text(), "max_chars": TRAINING_MAX_CHARS}


@app.post("/api/admin/training", dependencies=[Depends(require_admin)])
async def admin_set_training(req: TrainingRequest) -> dict:
    length = await asyncio.to_thread(set_training_text, req.text)
    return {"ok": True, "length": length, "max_chars": TRAINING_MAX_CHARS}


@app.post("/api/admin/training/extract", dependencies=[Depends(require_admin)])
async def admin_training_extract(file: UploadFile = File(...)) -> dict:
    """Trích xuất văn bản từ tệp .txt/.md/.pdf để admin đưa vào ô huấn luyện."""
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Tệp quá lớn (tối đa 10MB).")
    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        try:
            text = await asyncio.to_thread(_extract_pdf, data)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Không đọc được PDF: {exc}")
    else:
        text = data.decode("utf-8", errors="ignore")
    return {"text": text[:TRAINING_MAX_CHARS], "filename": file.filename}


@app.get("/api/admin/qa", dependencies=[Depends(require_admin)])
async def admin_list_qa() -> dict:
    items = await asyncio.to_thread(list_qa_admin)
    return {"count": len(items), "items": items, "categories": CATEGORY_LABELS}


@app.post("/api/admin/qa", dependencies=[Depends(require_admin)])
async def admin_upsert_qa(req: QARequest) -> dict:
    if not req.question.strip() or not req.answer.strip():
        raise HTTPException(status_code=422, detail="Cần nhập cả câu hỏi và câu trả lời.")
    item = await asyncio.to_thread(upsert_qa, req.model_dump())
    return {"ok": True, "item": item}


@app.delete("/api/admin/qa/{qa_id}", dependencies=[Depends(require_admin)])
async def admin_delete_qa(qa_id: str) -> dict:
    await asyncio.to_thread(delete_qa, qa_id)
    return {"ok": True}


@app.get("/api/admin/settings", dependencies=[Depends(require_admin)])
def admin_get_settings() -> dict:
    rc = get_runtime_config()
    return {
        "api_key": apikey.api_key_status(settings),
        "model": rc.model,
        "max_tokens": rc.max_tokens,
        "temperature": rc.temperature,
        "available_models": list(settings.available_models),
        "storage": get_store().backend,
    }


@app.post("/api/admin/settings", dependencies=[Depends(require_admin)])
async def admin_set_settings(req: SettingsRequest) -> dict:
    if req.max_tokens is not None and not (1 <= req.max_tokens <= 8192):
        raise HTTPException(status_code=422, detail="max_tokens phải trong khoảng 1..8192.")
    if req.temperature is not None and not (0.0 <= req.temperature <= 1.0):
        raise HTTPException(status_code=422, detail="temperature phải trong khoảng 0..1.")

    # 1) API key (nếu có nhập) -> Secret Manager
    if req.api_key.strip():
        try:
            await asyncio.to_thread(apikey.set_api_key, req.api_key, settings)
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        except Exception as exc:
            logger.exception("Lỗi ghi API key vào Secret Manager")
            raise HTTPException(status_code=500, detail=f"Không ghi được API key: {exc}")

    # 2) Cấu hình khác -> store (Firestore/file)
    cfg: dict = {}
    if req.model.strip():
        cfg["model"] = req.model.strip()
    if req.max_tokens is not None:
        cfg["max_tokens"] = int(req.max_tokens)
    if req.temperature is not None:
        cfg["temperature"] = float(req.temperature)
    if cfg:
        await asyncio.to_thread(get_store().set_config, cfg)

    rc = get_runtime_config()
    return {
        "ok": True,
        "api_key": apikey.api_key_status(settings),
        "model": rc.model,
        "max_tokens": rc.max_tokens,
        "temperature": rc.temperature,
    }


@app.post("/api/admin/settings/test", dependencies=[Depends(require_admin)])
async def admin_test_connection() -> dict:
    """Gọi thử Claude bằng key hiện tại để xác nhận kết nối."""
    rc = get_runtime_config()
    if not rc.has_api_key:
        return {"ok": False, "message": "Chưa cấu hình API key."}
    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=rc.api_key)
        await client.messages.create(
            model=rc.model,
            max_tokens=4,
            messages=[{"role": "user", "content": "ping"}],
        )
        return {"ok": True, "message": f"Kết nối thành công (model {rc.model})."}
    except Exception as exc:
        return {"ok": False, "message": f"Kết nối thất bại: {exc}"}


# Trang quản trị
@app.get("/admin")
def admin_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "admin.html")


# Trang chủ (cổng portal)
@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


# Trang chat đầy đủ (cũng được nhúng vào widget của cổng)
@app.get("/chat")
def chat_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "chat.html")


# Tài nguyên tĩnh (css/js) phục vụ tại /static/*
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

"""Lead capture - lưu thông tin "đăng ký tư vấn" của khách quan tâm.

Chiến lược lưu trữ (ưu tiên tin cậy trên Cloud Run, nơi filesystem là tạm thời):
1. **Structured log** (luôn chạy): in một dòng JSON sạch ra stdout → Google
   Cloud Logging tự bắt thành jsonPayload, có thể lọc & xuất ra dễ dàng.
2. **Google Sheet webhook** (tuỳ chọn): nếu cấu hình SBI_LEADS_WEBHOOK_URL
   (một Google Apps Script Web App), lead sẽ được POST sang để ghi vào Sheet.
3. **File cục bộ** (best-effort): ghi thêm vào data/leads.jsonl cho local dev.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone

from .config import Settings, get_settings

logger = logging.getLogger("sbi.leads")


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _truncate_history(history: list[dict] | None, max_msgs: int = 6) -> list[dict]:
    """Lấy vài tin nhắn gần nhất làm ngữ cảnh kèm theo lead (giúp tư vấn viên)."""
    if not history:
        return []
    out = []
    for m in history[-max_msgs:]:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            out.append({"role": role, "content": content[:500]})
    return out


async def save_lead(data: dict, settings: Settings | None = None) -> dict:
    """Chuẩn hoá, lưu trữ lead và trả về bản ghi đã tạo."""
    settings = settings or get_settings()

    lead = {
        "id": f"lead-{int(time.time())}-{uuid.uuid4().hex[:6]}",
        "name": (data.get("name") or "").strip(),
        "phone": (data.get("phone") or "").strip(),
        "email": (data.get("email") or "").strip(),
        "note": (data.get("note") or "").strip(),
        "source": (data.get("source") or "web").strip(),
        "created_at": _now_iso(),
        "context": _truncate_history(data.get("context")),
    }

    # 1) Structured log -> Cloud Logging (luôn, không bao giờ mất)
    try:
        print(json.dumps({"event": "lead", **lead}, ensure_ascii=False), flush=True)
    except Exception:  # pragma: no cover - logging không được làm hỏng request
        logger.exception("Không in được structured log cho lead")

    # 2) File cục bộ (best-effort, chủ yếu cho local dev)
    try:
        settings.leads_file.parent.mkdir(parents=True, exist_ok=True)
        with open(settings.leads_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(lead, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("Không ghi được lead ra file %s: %s", settings.leads_file, exc)

    # 3) Webhook Google Sheet (tuỳ chọn)
    if settings.leads_webhook_url:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(settings.leads_webhook_url, json=lead)
        except Exception as exc:
            logger.warning("Gửi lead tới webhook thất bại: %s", exc)

    return lead

"""Quản lý Claude API key qua Google Secret Manager.

- `resolve_api_key()`: đọc key lúc chạy (Secret Manager → fallback biến môi trường),
  có cache TTL để key mới (do admin nạp) có hiệu lực mà KHÔNG cần deploy lại.
- `set_api_key()`: ghi key mới thành một version mới trong Secret Manager.
- `api_key_status()`: trạng thái key (đã cấu hình chưa, hiển thị che, nguồn).

Khi không có Secret Manager (chạy local/test): tự bỏ qua, dùng biến môi trường.
"""
from __future__ import annotations

import logging
import time

from .config import Settings, get_settings

logger = logging.getLogger("sbi.apikey")

_TTL = 300.0  # giây - thời gian cache key đọc từ Secret Manager
_cache: dict = {"value": "", "ts": 0.0}


# --------------------------------------------------------------------------
def _sm_enabled(settings: Settings) -> bool:
    mode = (settings.use_secret_manager or "auto").strip().lower()
    if mode in ("0", "false", "no", "off"):
        return False
    if not settings.gcp_project:
        return False
    if mode in ("1", "true", "yes", "on"):
        return True
    try:  # auto: cần thư viện
        import google.cloud.secretmanager  # noqa: F401

        return True
    except Exception:
        return False


def _read_sm(settings: Settings) -> str:
    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = (
            f"projects/{settings.gcp_project}/secrets/"
            f"{settings.api_key_secret}/versions/latest"
        )
        resp = client.access_secret_version(name=name)
        return resp.payload.data.decode("utf-8").strip()
    except Exception as exc:
        logger.info("Chưa đọc được API key từ Secret Manager: %s", exc)
        return ""


def _read_cached(settings: Settings) -> str:
    now = time.time()
    if _cache["ts"] and now - _cache["ts"] < _TTL:
        return _cache["value"]
    _cache["value"] = _read_sm(settings)
    _cache["ts"] = now
    return _cache["value"]


def invalidate_cache() -> None:
    _cache["ts"] = 0.0
    _cache["value"] = ""


# --------------------------------------------------------------------------
def resolve_api_key(settings: Settings | None = None) -> str:
    """Key đang hiệu lực: ưu tiên Secret Manager, fallback biến môi trường."""
    settings = settings or get_settings()
    if _sm_enabled(settings):
        key = _read_cached(settings)
        if key:
            return key
    return (settings.anthropic_api_key or "").strip()


def set_api_key(value: str, settings: Settings | None = None) -> None:
    """Ghi key mới vào Secret Manager (tạo secret nếu chưa có)."""
    settings = settings or get_settings()
    value = (value or "").strip()
    if not value:
        raise ValueError("API key trống.")
    if not _sm_enabled(settings):
        raise RuntimeError(
            "Secret Manager chưa sẵn sàng (thiếu project GCP hoặc thư viện). "
            "Hãy đặt key qua biến môi trường ANTHROPIC_API_KEY."
        )
    from google.api_core import exceptions as gexc
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{settings.gcp_project}"
    secret_path = f"{parent}/secrets/{settings.api_key_secret}"
    try:
        client.get_secret(name=secret_path)
    except gexc.NotFound:
        client.create_secret(
            parent=parent,
            secret_id=settings.api_key_secret,
            secret={"replication": {"automatic": {}}},
        )
    client.add_secret_version(
        parent=secret_path, payload={"data": value.encode("utf-8")}
    )
    invalidate_cache()
    logger.info("Đã cập nhật API key mới trong Secret Manager.")


def mask(key: str) -> str:
    key = (key or "").strip()
    if not key:
        return ""
    if len(key) <= 12:
        return key[:3] + "…"
    return f"{key[:7]}…{key[-4:]}"


def api_key_status(settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    sm = _sm_enabled(settings)
    sm_key = _read_cached(settings) if sm else ""
    env_key = (settings.anthropic_api_key or "").strip()
    key = sm_key or env_key
    source = "secret_manager" if sm_key else ("env" if env_key else "none")
    return {
        "configured": bool(key),
        "masked": mask(key),
        "source": source,
        "secret_manager_available": sm,
        "secret_name": settings.api_key_secret if sm else "",
    }

"""Xác thực quản trị bằng mật khẩu (có thể đổi trong /admin).

- Mật khẩu được lưu dạng **hash** (PBKDF2-HMAC-SHA256, có salt) trong store
  (Firestore/file), không lưu plaintext.
- Khi chưa đặt mật khẩu: dùng mật khẩu **mặc định** `Abc@123456`.
- Biến môi trường `SBI_ADMIN_TOKEN` (nếu có) luôn được chấp nhận làm mật khẩu
  khôi phục — hữu ích khi quên mật khẩu đã đổi.
"""
from __future__ import annotations

import hashlib
import hmac
import os

from .config import get_settings
from .store import get_store

DEFAULT_PASSWORD = "Abc@123456"
_ITER = 120_000


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITER)
    return f"pbkdf2_sha256${_ITER}${salt}${dk.hex()}"


def _verify_hash(password: str, stored: str) -> bool:
    try:
        _algo, iters, salt, digest = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(dk.hex(), digest)
    except Exception:
        return False


def _stored_hash() -> str:
    try:
        return (get_store().get_config().get("admin_password_hash") or "").strip()
    except Exception:
        return ""


def verify_password(provided: str) -> bool:
    """Kiểm tra mật khẩu: hash đã lưu → mặc định (nếu chưa đặt) → token khôi phục."""
    provided = provided or ""
    if not provided:
        return False
    settings = get_settings()
    # Token môi trường luôn hợp lệ (khôi phục)
    if settings.admin_token and hmac.compare_digest(provided, settings.admin_token):
        return True
    stored = _stored_hash()
    if stored:
        return _verify_hash(provided, stored)
    # Chưa đặt mật khẩu riêng -> dùng mặc định
    return hmac.compare_digest(provided, DEFAULT_PASSWORD)


def set_password(new_password: str) -> None:
    new_password = (new_password or "").strip()
    if len(new_password) < 6:
        raise ValueError("Mật khẩu phải từ 6 ký tự trở lên.")
    get_store().set_config({"admin_password_hash": hash_password(new_password)})

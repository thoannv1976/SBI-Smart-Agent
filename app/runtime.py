"""Cấu hình hiệu lực lúc chạy = mặc định (biến môi trường) + override từ admin.

Gộp một chỗ để `llm.py` và các endpoint dùng chung: model, max_tokens,
temperature (lưu trong store) và API key (qua Secret Manager / env).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import apikey
from .config import get_settings
from .store import get_store


@dataclass
class RuntimeConfig:
    api_key: str
    model: str
    max_tokens: int
    temperature: float

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key.strip())


def get_runtime_config() -> RuntimeConfig:
    s = get_settings()
    try:
        cfg = get_store().get_config()
    except Exception:
        cfg = {}

    model = (cfg.get("model") or s.model).strip()
    try:
        max_tokens = int(cfg.get("max_tokens") or s.max_tokens)
    except (TypeError, ValueError):
        max_tokens = s.max_tokens
    try:
        temperature = (
            float(cfg["temperature"])
            if cfg.get("temperature") is not None
            else s.temperature
        )
    except (TypeError, ValueError):
        temperature = s.temperature

    return RuntimeConfig(
        api_key=apikey.resolve_api_key(s),
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )

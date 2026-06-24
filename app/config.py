"""Cấu hình ứng dụng - đọc toàn bộ từ biến môi trường (12-factor app).

Khi chạy local: tạo file `.env` (xem `.env.example`) rồi `export` hoặc dùng
`python-dotenv`. Khi chạy trên Cloud Run: nạp qua `--set-env-vars` / `--set-secrets`.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

# Nạp file .env nếu có (chỉ phục vụ chạy local; trên Cloud Run dùng env vars thật).
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv không bắt buộc ở môi trường production
    pass


# Thư mục gốc của dự án (…/SBI-Smart-Agent)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """Gom toàn bộ cấu hình runtime vào một nơi."""

    # --- Claude / Anthropic ---
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    # Model mặc định: Sonnet 4.6 (chất lượng cao). Đổi sang
    # "claude-haiku-4-5-20251001" để rẻ & nhanh hơn cho Q&A đơn giản.
    model: str = os.getenv("SBI_MODEL", "claude-sonnet-4-6")
    max_tokens: int = int(os.getenv("SBI_MAX_TOKENS", "1024"))
    # Nhiệt độ thấp để bám sát tri thức, hạn chế "bịa".
    temperature: float = float(os.getenv("SBI_TEMPERATURE", "0.2"))

    # Số lượt hội thoại gần nhất giữ lại làm ngữ cảnh (mỗi lượt = user + assistant).
    max_history_turns: int = int(os.getenv("SBI_MAX_HISTORY_TURNS", "12"))

    # --- Dữ liệu ---
    data_dir: Path = Path(os.getenv("SBI_DATA_DIR", str(BASE_DIR / "data")))

    # --- Lead capture (đăng ký tư vấn) ---
    # (Tuỳ chọn) URL Google Apps Script Web App để ghi lead vào Google Sheet.
    leads_webhook_url: str = os.getenv("SBI_LEADS_WEBHOOK_URL", "")
    # File lưu lead cục bộ — chủ yếu phục vụ local dev. Trên Cloud Run filesystem
    # là tạm thời (mất khi instance tái tạo) nên nguồn lead tin cậy là Cloud
    # Logging (structured log) hoặc Google Sheet qua webhook ở trên.
    leads_file: Path = Path(
        os.getenv("SBI_LEADS_FILE", str(BASE_DIR / "data" / "leads.jsonl"))
    )
    # File lưu các Q&A do admin thêm/sửa/xoá (override lên dataset gốc) khi dùng
    # FileStore (local dev). Khi bật Firestore thì dùng collection thay cho file.
    qa_overrides_file: Path = Path(
        os.getenv("SBI_QA_OVERRIDES_FILE", str(BASE_DIR / "data" / "qa_overrides.jsonl"))
    )
    # File cấu hình runtime (model/temperature...) do admin chỉnh, khi dùng
    # FileStore (local). Khi bật Firestore thì lưu vào collection cấu hình.
    settings_file: Path = Path(
        os.getenv("SBI_SETTINGS_FILE", str(BASE_DIR / "data" / "app_settings.json"))
    )
    # File đếm lượt hỏi theo từng Q&A (thống kê) khi dùng FileStore.
    stats_file: Path = Path(
        os.getenv("SBI_STATS_FILE", str(BASE_DIR / "data" / "stats.json"))
    )

    # --- Lưu trữ bền vững (Firestore) ---
    # "auto" (mặc định): bật Firestore nếu có thư viện + project GCP; ngược lại
    # dùng file cục bộ. Đặt "1"/"0" để ép bật/tắt.
    use_firestore: str = os.getenv("SBI_USE_FIRESTORE", "auto")
    firestore_project: str = os.getenv(
        "SBI_FIRESTORE_PROJECT", os.getenv("GOOGLE_CLOUD_PROJECT", "")
    )
    firestore_leads_collection: str = os.getenv("SBI_FS_LEADS", "sbi_leads")
    firestore_qa_collection: str = os.getenv("SBI_FS_QA", "sbi_qa_overrides")
    firestore_config_collection: str = os.getenv("SBI_FS_CONFIG", "sbi_config")
    firestore_stats_collection: str = os.getenv("SBI_FS_STATS", "sbi_stats")

    # --- Trang quản trị (/admin) ---
    # Token bảo vệ các API /api/admin/*. Để trống => admin bị TẮT (an toàn mặc định).
    admin_token: str = os.getenv("SBI_ADMIN_TOKEN", "")

    # --- API key qua Secret Manager (cho phép nạp key từ /admin) ---
    # "auto": dùng Secret Manager nếu có project GCP + thư viện; ngược lại bỏ qua.
    use_secret_manager: str = os.getenv("SBI_USE_SECRET_MANAGER", "auto")
    gcp_project: str = os.getenv(
        "SBI_GCP_PROJECT",
        os.getenv("SBI_FIRESTORE_PROJECT", os.getenv("GOOGLE_CLOUD_PROJECT", "")),
    )
    api_key_secret: str = os.getenv("SBI_API_KEY_SECRET", "anthropic-api-key")
    # Danh sách model cho admin chọn (hiển thị trong trang Cấu hình).
    available_models: tuple[str, ...] = (
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
        "claude-opus-4-8",
    )

    # --- Server ---
    # Cloud Run cấp PORT qua biến môi trường (mặc định 8080).
    port: int = int(os.getenv("PORT", "8080"))
    host: str = os.getenv("HOST", "0.0.0.0")

    @property
    def has_api_key(self) -> bool:
        return bool(self.anthropic_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Trả về singleton Settings (cache lại để không đọc env nhiều lần)."""
    return Settings()

"""Tầng lưu trữ bền vững cho lead và Q&A override.

Hai cài đặt:
- **FirestoreStore**: dùng Google Cloud Firestore (bền vững trên Cloud Run,
  dùng chung cho nhiều instance). Kích hoạt khi có thư viện + project GCP.
- **FileStore**: ghi ra file JSONL cục bộ (cho local dev / khi chưa bật Firestore).

`get_store()` tự chọn cài đặt phù hợp dựa trên cấu hình (SBI_USE_FIRESTORE).
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache

from .config import Settings, get_settings

logger = logging.getLogger("sbi.store")


# --------------------------------------------------------------------------
# FileStore - lưu vào file JSONL (local dev / fallback)
# --------------------------------------------------------------------------
class FileStore:
    backend = "file"

    def __init__(self, settings: Settings):
        self.leads_file = settings.leads_file
        self.qa_file = settings.qa_overrides_file

    # ----- Leads -----
    def add_lead(self, lead: dict) -> None:
        self.leads_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.leads_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(lead, ensure_ascii=False) + "\n")

    def list_leads(self, limit: int = 500) -> list[dict]:
        if not self.leads_file.exists():
            return []
        rows: list[dict] = []
        with open(self.leads_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        rows.reverse()  # mới nhất lên đầu
        return rows[:limit]

    # ----- Q&A overrides (compacted: 1 dòng / id, ghi đè toàn bộ) -----
    def _read_qa_map(self) -> dict[str, dict]:
        data: dict[str, dict] = {}
        if not self.qa_file.exists():
            return data
        with open(self.qa_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("id"):
                    data[rec["id"]] = rec
        return data

    def _write_qa_map(self, data: dict[str, dict]) -> None:
        self.qa_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.qa_file, "w", encoding="utf-8") as f:
            for rec in data.values():
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def list_qa_overrides(self) -> list[dict]:
        return list(self._read_qa_map().values())

    def upsert_qa(self, item: dict) -> None:
        data = self._read_qa_map()
        data[item["id"]] = item
        self._write_qa_map(data)

    def delete_qa(self, qa_id: str) -> None:
        data = self._read_qa_map()
        # Tombstone để vô hiệu hoá cả Q&A gốc lẫn Q&A tự thêm.
        data[qa_id] = {"id": qa_id, "deleted": True}
        self._write_qa_map(data)


# --------------------------------------------------------------------------
# FirestoreStore - lưu vào Google Cloud Firestore
# --------------------------------------------------------------------------
class FirestoreStore:
    backend = "firestore"

    def __init__(self, settings: Settings):
        from google.cloud import firestore  # import trễ (chỉ khi thực sự dùng)

        kwargs = {}
        if settings.firestore_project:
            kwargs["project"] = settings.firestore_project
        self._db = firestore.Client(**kwargs)
        self._leads = settings.firestore_leads_collection
        self._qa = settings.firestore_qa_collection

    # ----- Leads -----
    def add_lead(self, lead: dict) -> None:
        self._db.collection(self._leads).document(lead["id"]).set(lead)

    def list_leads(self, limit: int = 500) -> list[dict]:
        from google.cloud import firestore

        q = (
            self._db.collection(self._leads)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        return [doc.to_dict() for doc in q.stream()]

    # ----- Q&A overrides -----
    def list_qa_overrides(self) -> list[dict]:
        return [doc.to_dict() for doc in self._db.collection(self._qa).stream()]

    def upsert_qa(self, item: dict) -> None:
        self._db.collection(self._qa).document(item["id"]).set(item)

    def delete_qa(self, qa_id: str) -> None:
        self._db.collection(self._qa).document(qa_id).set(
            {"id": qa_id, "deleted": True}
        )


# --------------------------------------------------------------------------
# Factory
# --------------------------------------------------------------------------
def _should_use_firestore(settings: Settings) -> bool:
    mode = (settings.use_firestore or "auto").strip().lower()
    if mode in ("0", "false", "no", "off"):
        return False
    if mode in ("1", "true", "yes", "on"):
        return True
    # auto: cần có project GCP rồi thử import thư viện
    if not settings.firestore_project:
        return False
    try:
        import google.cloud.firestore  # noqa: F401

        return True
    except Exception:
        return False


@lru_cache
def get_store() -> FileStore | FirestoreStore:
    settings = get_settings()
    if _should_use_firestore(settings):
        try:
            store = FirestoreStore(settings)
            logger.info("Lưu trữ: Firestore (project=%s)", settings.firestore_project)
            return store
        except Exception as exc:  # fallback an toàn nếu khởi tạo Firestore lỗi
            logger.warning("Không khởi tạo được Firestore (%s) -> dùng FileStore", exc)
    logger.info("Lưu trữ: FileStore (local)")
    return FileStore(settings)

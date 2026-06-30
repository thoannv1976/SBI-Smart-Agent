"""Cấu hình cổng portal (trang chủ) — link tích hợp, video, khóa học, mạng xã hội.

Lưu trong store (Firestore/file) dưới khóa `portal` của config doc → admin sửa
được mà không cần deploy lại. Toàn bộ dữ liệu ở đây là công khai (chỉ là link).
"""
from __future__ import annotations

from .store import get_store

DEFAULTS: dict = {
    "hero_title": "Thương mại số thông minh & Đổi mới kinh doanh",
    "hero_subtitle": "Kết nối công nghệ – Khơi nguồn đổi mới – Kiến tạo giá trị bền vững.",
    "youtube_channel_url": "",
    "youtube_video_ids": [],
    "lms_url": "",
    "featured_courses": [],  # [{title, desc, url, thumbnail}]
    "featured_posts": [],    # [{title, desc, url, thumbnail}]
    "obe_url": "",
    "career_test_url": "",
    "social": {
        "facebook": "", "tiktok": "", "youtube": "",
        "zalo": "", "instagram": "", "website": "",
    },
}


def _s(v) -> str:
    return str(v or "").strip()


def get_portal_config() -> dict:
    try:
        stored = get_store().get_config().get("portal") or {}
    except Exception:
        stored = {}
    cfg = {**DEFAULTS, **stored}
    cfg["social"] = {**DEFAULTS["social"], **(stored.get("social") or {})}
    cfg["youtube_video_ids"] = list(stored.get("youtube_video_ids") or [])
    cfg["featured_courses"] = list(stored.get("featured_courses") or [])
    cfg["featured_posts"] = list(stored.get("featured_posts") or [])
    return cfg


def _clean_cards(items, limit: int = 12) -> list[dict]:
    """Làm sạch danh sách thẻ (khóa học / bài viết): {title, desc, url, thumbnail}."""
    out = []
    for c in (items or [])[:limit]:
        if not isinstance(c, dict):
            continue
        title, url = _s(c.get("title")), _s(c.get("url"))
        if not title and not url:
            continue
        out.append(
            {"title": title, "desc": _s(c.get("desc")), "url": url, "thumbnail": _s(c.get("thumbnail"))}
        )
    return out


def set_portal_config(data: dict) -> dict:
    """Làm sạch & lưu cấu hình cổng; trả về cấu hình sau khi lưu."""
    social_in = data.get("social") or {}
    social = {k: _s(social_in.get(k)) for k in DEFAULTS["social"]}

    clean = {
        "hero_title": _s(data.get("hero_title")) or DEFAULTS["hero_title"],
        "hero_subtitle": _s(data.get("hero_subtitle")) or DEFAULTS["hero_subtitle"],
        "youtube_channel_url": _s(data.get("youtube_channel_url")),
        "youtube_video_ids": [_s(v) for v in (data.get("youtube_video_ids") or []) if _s(v)][:3],
        "lms_url": _s(data.get("lms_url")),
        "featured_courses": _clean_cards(data.get("featured_courses")),
        "featured_posts": _clean_cards(data.get("featured_posts")),
        "obe_url": _s(data.get("obe_url")),
        "career_test_url": _s(data.get("career_test_url")),
        "social": social,
    }
    get_store().set_config({"portal": clean})
    return get_portal_config()

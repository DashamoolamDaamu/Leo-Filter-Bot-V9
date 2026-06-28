# database/admin_db.py
# Global bot settings (not per-group) stored in MongoDB.
# Used by the Admin Panel to toggle features on/off for all users.

import logging
import time
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME

logger = logging.getLogger(__name__)

_client = AsyncIOMotorClient(DATABASE_URI)
_db     = _client[DATABASE_NAME]
_col    = _db["bot_global_settings"]

# ── In-memory cache (avoids hitting MongoDB on every user request) ─────────────
_CACHE:    dict = {}
_CACHE_TS: float = 0.0
_CACHE_TTL: int  = 60   # seconds

# ── Default settings ──────────────────────────────────────────────────────────
DEFAULTS: dict = {
    # Feature toggles
    "maintenance_mode":     False,
    "maintenance_msg":      "🛠 The bot is under maintenance. Please try again shortly.",
    "browse_enabled":       True,
    "actor_search_enabled": True,
    "trending_enabled":     True,
    "ratings_enabled":      True,
    "streaming_enabled":    True,
    # Browse sub-features
    "browse_genres":        True,
    "browse_language":      True,
    "browse_year":          True,
    "browse_new":           True,
    "browse_trending":      True,
    "browse_toprated":      True,
    "browse_collections":   True,
    # Actor settings
    "actor_cache_ttl_days": 7,
    "actor_timeout_sec":    300,
}

# ── Human-readable labels for the admin UI ────────────────────────────────────
SETTING_LABELS: dict[str, str] = {
    "maintenance_mode":     "🛠 Maintenance Mode",
    "browse_enabled":       "🎬 Browse Menu",
    "actor_search_enabled": "🎭 Actor Search",
    "trending_enabled":     "🔥 Trending",
    "ratings_enabled":      "⭐ Movie Ratings",
    "streaming_enabled":    "▶ Streaming",
    "browse_genres":        "🎭 Genres",
    "browse_language":      "🌐 Language Browse",
    "browse_year":          "📅 Year Browse",
    "browse_new":           "🆕 New Releases",
    "browse_trending":      "🔥 Trending Browse",
    "browse_toprated":      "⭐ Top Rated Browse",
    "browse_collections":   "🎯 Collections",
}


async def _load() -> dict:
    global _CACHE, _CACHE_TS
    if time.monotonic() - _CACHE_TS < _CACHE_TTL and _CACHE:
        return _CACHE
    try:
        doc = await _col.find_one({"_id": "global"}) or {}
        merged = {**DEFAULTS, **{k: v for k, v in doc.items() if k != "_id"}}
        _CACHE    = merged
        _CACHE_TS = time.monotonic()
        return merged
    except Exception as e:
        logger.debug(f"[AdminDB] load: {e}")
        return dict(DEFAULTS)


async def get_setting(key: str) -> Any:
    cfg = await _load()
    return cfg.get(key, DEFAULTS.get(key))


async def get_all() -> dict:
    return await _load()


async def set_setting(key: str, value: Any):
    global _CACHE, _CACHE_TS
    try:
        await _col.update_one(
            {"_id": "global"},
            {"$set": {key: value}},
            upsert=True,
        )
        # Invalidate cache
        _CACHE = {}
        _CACHE_TS = 0.0
    except Exception as e:
        logger.debug(f"[AdminDB] set {key}: {e}")


async def toggle(key: str) -> bool:
    """Toggle a boolean setting. Returns new value."""
    current = await get_setting(key)
    new_val = not bool(current)
    await set_setting(key, new_val)
    return new_val


async def is_maintenance() -> bool:
    return bool(await get_setting("maintenance_mode"))


async def get_maintenance_msg() -> str:
    return str(await get_setting("maintenance_msg") or DEFAULTS["maintenance_msg"])

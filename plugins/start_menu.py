# plugins/start_menu.py
# Single source of truth for the start menu keyboard.
# Both commands.py and pm_filter.py import from here so the UI is always identical.

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils import temp


def build_start_markup() -> InlineKeyboardMarkup:
    """Return the premium home screen keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Browse",      callback_data="bm_main"),
            InlineKeyboardButton("🎭 Actors",      callback_data="actor_menu"),
        ],
        [
            InlineKeyboardButton("🆕 New",         callback_data="bm_new"),
            InlineKeyboardButton("🔥 Trending",    callback_data="bm_trending"),
        ],
        [
            InlineKeyboardButton("⭐ Top Rated",   callback_data="bm_toprated"),
            InlineKeyboardButton("🎯 Collections", callback_data="bm_collections"),
        ],
        [
            InlineKeyboardButton("📢 Updates",     url="https://t.me/movie_ottupdates"),
            InlineKeyboardButton("📣 Channel",     url="https://t.me/mn_movies2"),
        ],
        [
            InlineKeyboardButton("➕ Add Bot",      url=f"http://t.me/{temp.U_NAME}?startgroup=true"),
            InlineKeyboardButton("ℹ Help",         callback_data="help"),
        ],

    ])


def build_start_text(mention: str = "there") -> str:
    return (
        f"🎬 <b>Leo Advanced Filter Bot V9</b>\n\n"
        f"Hello {mention}!\n\n"
        "Search movies by typing their name, or use the menu below to browse by genre, actor, year, and more."
    )

# plugins/browse_menu.py
# Premium Browse Menu — fully database-driven.
# Covers: Genres (delegates to genre_browse), Language, Year,
#         New Releases, Trending, Top Rated, Collections.
# Every result flows through the existing dynamic filter wizard + Auto Filter UI.

import asyncio
import logging
import math
import re

from pyrogram import Client, filters
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.ia_filterdb import get_search_results
from database.ratings_db  import ensure_indexes as r_ensure, get_trending, get_top_rated, inc_view
from utils import get_size, get_settings, get_poster

logger = logging.getLogger(__name__)

FILES_PER_PAGE = 10

# ── Collection definitions ─────────────────────────────────────────────────────
# Each: (callback_code, display_name, emoji, search_terms)

COLLECTIONS = [
    ("marvel",   "Marvel",             "🦸", ["avengers", "iron man", "thor", "spider-man", "captain america", "black panther"]),
    ("dc",       "DC",                 "🦇", ["batman", "superman", "wonder woman", "justice league", "aquaman", "joker"]),
    ("hpotter",  "Harry Potter",       "⚡", ["harry potter", "fantastic beasts"]),
    ("mimposs",  "Mission Impossible", "🕶",  ["mission impossible"]),
    ("fastfury",  "Fast & Furious",    "🚗", ["fast furious", "fast and furious"]),
    ("johnwick", "John Wick",          "🔫", ["john wick"]),
    ("conjuring","Conjuring Universe", "👻", ["conjuring", "annabelle", "nun"]),
    ("finaldes", "Final Destination",  "💀", ["final destination"]),
]
_COL_MAP = {code: (name, emoji, terms) for code, name, emoji, terms in COLLECTIONS}

# ── In-memory browse result store ─────────────────────────────────────────────
BROWSE_RESULTS: dict = {}


def _year_from_fname(file_name: str) -> str | None:
    m = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', file_name or "")
    return m.group(1) if m else None


# ─── Top-level Browse Menu ────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^bm_main$"))
async def browse_main(bot, query):
    """Premium Browse sub-menu shown after clicking '🎬 Browse' on start."""
    await query.answer()
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Genres",       callback_data="genre_menu"),
         InlineKeyboardButton("🌐 Language",     callback_data="bm_lang")],
        [InlineKeyboardButton("📅 Year",         callback_data="bm_year"),
         InlineKeyboardButton("🆕 New Releases", callback_data="bm_new")],
        [InlineKeyboardButton("🔥 Trending",     callback_data="bm_trending"),
         InlineKeyboardButton("⭐ Top Rated",    callback_data="bm_toprated")],
        [InlineKeyboardButton("🎯 Collections",  callback_data="bm_collections")],
        [InlineKeyboardButton("⬅ Back",          callback_data="back_start")],
    ])
    try:
        await query.edit_message_text(
            "🎬 **Browse Movies**\n\nChoose a category:",
            reply_markup=markup,
        )
    except MessageNotModified:
        pass


# ─── Language Browse ──────────────────────────────────────────────────────────

_LANGUAGES = [
    ("Malayalam", "🇮🇳"), ("Tamil", "🇮🇳"), ("Hindi", "🇮🇳"),
    ("English",  "🌍"),  ("Telugu", "🇮🇳"), ("Kannada", "🇮🇳"),
    ("Bengali",  "🇮🇳"), ("Punjabi", "🇮🇳"),("Korean",  "🇰🇷"),
    ("Japanese", "🇯🇵"),  ("Spanish", "🇪🇸"), ("French",  "🇫🇷"),
]

@Client.on_callback_query(filters.regex(r"^bm_lang$"))
async def browse_lang(bot, query):
    await query.answer()
    rows = []
    row  = []
    for lang, flag in _LANGUAGES:
        row.append(InlineKeyboardButton(
            f"{flag} {lang}", callback_data=f"bml_{lang[:12]}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("⬅ Back", callback_data="bm_main")])
    try:
        await query.edit_message_text(
            "🌐 **Browse by Language**\n\nSelect a language:",
            reply_markup=InlineKeyboardMarkup(rows),
        )
    except MessageNotModified:
        pass


@Client.on_callback_query(filters.regex(r"^bml_\w+$"))
async def browse_lang_results(bot, query):
    lang = query.data[4:]
    uid  = query.from_user.id
    await query.answer(f"Searching {lang}…")

    try:
        await query.edit_message_text(f"🌐 **{lang}** — searching… ⏳")
    except MessageNotModified:
        pass

    files, _, _, _ = await get_search_results(
        lang, offset=0, max_results=500, filter=True, fast=True, return_time=True)

    await _launch_browse_filter(query, uid, files, f"🌐 Language: {lang}", back_cb="bm_lang")


# ─── Year Browse ──────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^bm_year$"))
async def browse_year(bot, query):
    await query.answer()
    import datetime
    current = datetime.datetime.now().year
    years = [str(y) for y in range(current, current - 15, -1)]
    rows = []
    row  = []
    for yr in years:
        row.append(InlineKeyboardButton(yr, callback_data=f"bmy_{yr}"))
        if len(row) == 4:
            rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("⬅ Back", callback_data="bm_main")])
    try:
        await query.edit_message_text(
            "📅 **Browse by Year**\n\nSelect a release year:",
            reply_markup=InlineKeyboardMarkup(rows),
        )
    except MessageNotModified:
        pass


@Client.on_callback_query(filters.regex(r"^bmy_\d{4}$"))
async def browse_year_results(bot, query):
    year = query.data[4:]
    uid  = query.from_user.id
    await query.answer(f"Searching {year}…")

    try:
        await query.edit_message_text(f"📅 **{year}** — searching… ⏳")
    except MessageNotModified:
        pass

    files, _, _, _ = await get_search_results(
        year, offset=0, max_results=500, filter=True, fast=True, return_time=True)

    # Further filter by year in filename
    files = [f for f in files if _year_from_fname(f.file_name) == year] or files

    await _launch_browse_filter(query, uid, files, f"📅 Year: {year}", back_cb="bm_year")


# ─── New Releases ─────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^bm_new$"))
async def browse_new(bot, query):
    uid = query.from_user.id
    await query.answer("Loading new releases…")
    try:
        await query.edit_message_text("🆕 **New Releases** — loading… ⏳")
    except MessageNotModified:
        pass

    import datetime
    cur_year = datetime.datetime.now().year

    # Collect files from recent 3 years using year found in filename
    all_files: dict = {}
    for yr in [str(cur_year), str(cur_year - 1), str(cur_year - 2)]:
        files, _, _, _ = await get_search_results(
            yr, offset=0, max_results=200, filter=True, fast=True, return_time=True)
        for f in files:
            fname_year = _year_from_fname(f.file_name)
            if fname_year in (yr, str(cur_year - 1), str(cur_year)):
                all_files[f.file_id] = f

    # Sort: newest year first, then alphabetically
    sorted_files = sorted(
        all_files.values(),
        key=lambda f: (_year_from_fname(f.file_name) or "0"),
        reverse=True,
    )

    if not sorted_files:
        return await query.edit_message_text(
            "🆕 **New Releases**\n\nNo recent files found.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅ Back", callback_data="bm_main")
            ]]),
        )

    await _launch_browse_filter(query, uid, sorted_files, "🆕 New Releases", back_cb="bm_main")


# ─── Trending ─────────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^bm_trending$"))
async def browse_trending(bot, query):
    uid = query.from_user.id
    await query.answer("Loading trending…")
    try:
        await query.edit_message_text("🔥 **Trending** — loading… ⏳")
    except MessageNotModified:
        pass

    trending = await get_trending(limit=30)
    all_files: dict = {}

    # Trending = top searched terms → find matching MongoDB files directly
    for item in trending:
        qkey = item.get("query_key", "").strip()
        if not qkey:
            continue
        try:
            files, _, _, _ = await get_search_results(
                qkey, offset=0, max_results=30, filter=True, fast=True, return_time=True)
            for f in files:
                all_files[f.file_id] = f
        except Exception:
            pass

    sorted_files = list(all_files.values())
    if not sorted_files:
        return await query.edit_message_text(
            "🔥 **Trending**\n\nNot enough searches yet. The list builds as users search!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅ Back", callback_data="bm_main")
            ]]),
        )

    await _launch_browse_filter(query, uid, sorted_files, "🔥 Trending", back_cb="bm_main")


# ─── Top Rated ────────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^bm_toprated$"))
async def browse_toprated(bot, query):
    uid = query.from_user.id
    await query.answer("Loading top rated…")
    try:
        await query.edit_message_text("⭐ **Top Rated** — loading… ⏳")
    except MessageNotModified:
        pass

    top = await get_top_rated(limit=30)
    all_files: dict = {}

    for item in top:
        imdb_id = item.get("_id", "")
        if not imdb_id:
            continue
        # Resolve IMDb ID → title → MongoDB files
        try:
            imdb_data = await get_poster(imdb_id, id=True)
            if imdb_data and imdb_data.get("title"):
                title = imdb_data["title"]
                files, _, _, _ = await get_search_results(
                    title, offset=0, max_results=20, filter=True, fast=True, return_time=True)
                for f in files:
                    all_files[f.file_id] = f
        except Exception:
            pass

    sorted_files = list(all_files.values())
    if not sorted_files:
        return await query.edit_message_text(
            "⭐ **Top Rated**\n\nNo rated movies available yet. Rate movies after watching!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅ Back", callback_data="bm_main")
            ]]),
        )

    await _launch_browse_filter(query, uid, sorted_files, "⭐ Top Rated", back_cb="bm_main")


# ─── Collections ─────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^bm_collections$"))
async def browse_collections(bot, query):
    await query.answer()
    rows = []
    row  = []
    for code, name, emoji, _ in COLLECTIONS:
        row.append(InlineKeyboardButton(
            f"{emoji} {name}", callback_data=f"bmc_{code}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("⬅ Back", callback_data="bm_main")])
    try:
        await query.edit_message_text(
            "🎯 **Collections**\n\nSelect a collection:",
            reply_markup=InlineKeyboardMarkup(rows),
        )
    except MessageNotModified:
        pass


@Client.on_callback_query(filters.regex(r"^bmc_\w+$"))
async def browse_collection_results(bot, query):
    code = query.data[4:]
    uid  = query.from_user.id

    entry = _COL_MAP.get(code)
    if not entry:
        return await query.answer("Unknown collection.", show_alert=True)

    name, emoji, terms = entry
    await query.answer(f"Searching {name}…")
    try:
        await query.edit_message_text(f"{emoji} **{name}** — searching… ⏳")
    except MessageNotModified:
        pass

    all_files: dict = {}
    for term in terms:
        files, _, _, _ = await get_search_results(
            term, offset=0, max_results=100, filter=True, fast=True, return_time=True)
        for f in files:
            all_files[f.file_id] = f

    await _launch_browse_filter(query, uid, list(all_files.values()), f"{emoji} {name}", back_cb="bm_collections")


# ─── Shared: launch wizard for browse result ──────────────────────────────────

async def _launch_browse_filter(
    query, uid: int, files: list, display_label: str, back_cb: str = "bm_main"
):
    """
    Show the Browse Filter Screen — all filters visible at once,
    with a "📂 Get Files" button. Replaces the step-by-step wizard.
    """
    from plugins.pm_filter import new_bf_session, build_bf_screen

    if not files:
        try:
            await query.edit_message_text(
                f"❌ **{display_label}**\n\nNo indexed files found.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅ Back", callback_data=back_cb)
                ]]),
            )
        except MessageNotModified:
            pass
        return

    bf_id  = new_bf_session(uid, files, display_label, back_cb)
    result = build_bf_screen(bf_id, uid)
    if not result:
        return

    text, markup = result
    try:
        await query.edit_message_text(text, reply_markup=markup)
    except MessageNotModified:
        pass


# Keep the old name as alias so existing callers still work
_launch_wizard_for_browse = _launch_browse_filter

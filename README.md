# 🎬 Leo Advanced Auto Filter Bot

A premium OTT-style Telegram movie discovery bot built on top of the open-source [ShobanaFilterBot](https://github.com/mn-bots/ShobanaFilterBot) by [MN-TG](https://github.com/mntgxo).

This is a customized fork that adds OTT-style browsing, actor/director search, dynamic multi-level filters, user ratings, trending, collections, and FileToLink streaming — while keeping the original auto-filter system fully intact.

---

## ✨ Main Features

| Feature | Description |
|---|---|
| 🔍 Auto Filter | Indexes files from Telegram channels and responds to search queries in groups |
| 🎬 Browse by Genre | 35+ genres with IMDb-backed metadata and smart filtering |
| 🌐 Browse by Language | Filter all indexed files by language |
| 📅 Browse by Year | Find files from a specific release year |
| 🆕 New Releases | Recently indexed files sorted by year |
| 🔥 Trending | Most-searched movies tracked in real time |
| ⭐ Top Rated | Ranked by user votes (👍/😐/👎) |
| 🎯 Collections | Marvel, DC, Harry Potter, John Wick, and more |
| 🎭 Actor / Director Search | Find all indexed movies by any actor or director |
| 🔍 Dynamic Filter Wizard | Step-by-step Language → Year → Quality → Season → Episode |
| ▶ Stream | FileToLink integration — web player + direct download |
| ⭐ Rating System | Per-user votes stored in MongoDB |
| 📊 IMDb Integration | Poster, metadata, cast, rating via custom API |

---

## 🏗 Architecture

```
ShobanaFilterBot-mnbots/
├── bot.py                    # Main entry point
├── info.py                   # All env var config
├── utils.py                  # Shared helpers (IMDb, get_poster, etc.)
├── Script.py                 # All user-facing text strings
├── plugins/
│   ├── start_menu.py         # ★ Shared start menu builder (single source of truth)
│   ├── pm_filter.py          # Core auto-filter + dynamic wizard
│   ├── commands.py           # /start, /help, file delivery
│   ├── browse_menu.py        # Browse: Language, Year, New, Trending, Top Rated, Collections
│   ├── genre_browse.py       # Browse by Genre (35+ genres)
│   ├── actor_search.py       # Actor/Director guided discovery
│   ├── user_states.py        # Conversation state (blocks auto-filter during actor search)
│   ├── webcode.py            # aiohttp streaming server (FileToLink)
│   └── ...                   # Other existing plugins (unchanged)
├── database/
│   ├── ia_filterdb.py        # Core file index (unchanged)
│   ├── ratings_db.py         # ★ Ratings, trending, top-rated
│   ├── actor_cache_db.py     # ★ Actor filmography cache (7-day TTL)
│   └── genre_cache_db.py     # ★ IMDb genre cache (30-day TTL)
├── streaming/
│   ├── stream_dl.py          # ByteStreamer (FileToLink port)
│   ├── stream_render.py      # Jinja2 template renderer
│   └── stream_utils.py       # URL generation
└── template/
    ├── req.html              # Vidstack web player
    └── dl.html               # Download redirect
```

---

## 🔧 Installation

### Prerequisites

- Python 3.10+
- MongoDB Atlas (free tier works)
- Telegram Bot Token
- API ID + Hash from [my.telegram.org](https://my.telegram.org)

### Clone & Install

```bash
git clone https://github.com/your-username/your-repo
cd your-repo
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Copy and fill in the environment variables below. All can be set as system env vars or in a `.env` file.

### Required Variables

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `API_ID` | Telegram API ID |
| `API_HASH` | Telegram API Hash |
| `DATABASE_URI` | MongoDB connection string |
| `DATABASE_NAME` | MongoDB database name (default: `Cluster0`) |
| `CHANNELS` | Space-separated channel IDs to index |
| `ADMINS` | Space-separated admin user IDs |

### Streaming Variables (Optional)

| Variable | Description |
|---|---|
| `STREAM_BASE_URL` | Public URL of your bot's web server |
| `BIN_CHANNEL` | Private channel ID for file streaming (bot must be admin) |

### Optional Variables

| Variable | Default | Description |
|---|---|---|
| `FILE_CHANNELS` | — | Space-separated file delivery channel IDs |
| `FILE_CHANNEL_SENDING_MODE` | `True` | Send files via channel instead of directly |
| `FILE_AUTO_DELETE_SECONDS` | `60` | Auto-delete delay for channel files |
| `PROTECT_CONTENT` | `False` | Protect file messages from forwarding |
| `CUSTOM_FILE_CAPTION` | — | Custom caption template for sent files |
| `LOG_CHANNEL` | — | Channel for bot logs |
| `PORT_CODE` | `8000` | Web server port |
| `KEEP_ALIVE_URL` | — | URL to ping for keep-alive |
| `AUTH_USERS` | — | Users allowed to use bot in PM |
| `AUTH_GROUPS` | — | Allowed group IDs |
| `IMDB` | `True` | Enable IMDb poster/metadata in results |
| `PM_SEARCH_GROUP_LINK` | — | Group link shown for PM search redirect |
| `DATABASE_URI2–5` | — | Additional MongoDB shards (up to 5 total) |

---

## 🚀 Deployment

### Koyeb (Recommended)

1. Push code to GitHub
2. Connect repo on [koyeb.com](https://koyeb.com)
3. Set environment variables in the Koyeb dashboard
4. Deploy — the `Procfile` handles startup

### Docker

```bash
docker-compose up -d
```

### Heroku

```bash
heroku create
heroku config:set BOT_TOKEN=xxx API_ID=xxx ...
git push heroku main
```

---

## 📋 Commands

### Public
| Command | Description |
|---|---|
| `/start` | Open the home screen |
| `/movies` | Latest indexed movies |
| `/series` | Latest indexed series |
| `/connect` | Connect group to PM search |
| `/settings` | Group settings |
| `/filter` | Add a manual filter |
| `/filters` | View all manual filters |
| `/del` | Delete a manual filter |
| `/imdb` | Search IMDb |
| `/id` | Get user/chat ID |

### Admin
| Command | Description |
|---|---|
| `/index` | Index a channel |
| `/deletefiles` | Delete indexed files |
| `/broadcast` | Broadcast to all users |
| `/stats` | Database statistics |
| `/ban` / `/unban` | Ban/unban users |
| `/fsub` | Set force-subscribe channels |
| `/restart` | Restart the bot |
| `/logs` | Get recent logs |

---

## 🔄 User Flow

### Normal Search
```
User types movie name in group
  → Auto Filter (unchanged)
    → Dynamic Filter Wizard (Language → Year → Quality → Season → Episode)
      → File list
        → Click file → Send to PM
          → Stream / Download buttons
            → Rate the movie (👍/😐/👎)
```

### Browse Flow
```
/start → 🎬 Browse → Select category
  → Dynamic Filter Wizard
    → File list → Send to PM → Stream / Download
```

### Actor Search
```
/start → 🎭 Actors → Type actor name
  → Profile card + filmography
    → 🎬 View Movies
      → Dynamic Filter Wizard
        → File list → Send to PM
```

---

## 🛠 Troubleshooting

**Bot not indexing files**
- Ensure the bot is admin in the source channels with read-message permission
- Run `/index` in the admin PM

**Stream buttons not appearing**
- Set `STREAM_BASE_URL` and `BIN_CHANNEL` environment variables
- Ensure the bot is admin in `BIN_CHANNEL`
- Check `/status` endpoint: `https://your-url/status`

**Dynamic filters not showing**
- Filters only appear when multiple distinct values exist in results
- Single-language single-quality results skip the wizard and show results directly

**Actor search returns no results**
- The actor name is used to search indexed files — results depend on your indexed content
- Try shorter or alternate name spellings

**Trending / Top Rated empty**
- These features need usage data to accumulate
- Trending fills as users search; Top Rated fills as users rate movies

---

## 📝 Changelog

### v2.0 (Phase 2 — UI & Branding)
- Unified start menu via shared `start_menu.py`
- Full rebranding as "Leo Advanced Auto Filter Bot"
- Rewrote Script.py (Help, About, Start text)
- Fixed all Back button navigation paths
- Wrote this README

### v1.0 (Phase 1 — Feature Implementation)
- Dynamic Multi-Level Filter Wizard (Language → Year → Quality → Season → Episode)
- Actor / Director Search with IMDb integration
- Browse by Genre (35+ genres), Language, Year
- New Releases, Trending, Top Rated, Collections
- Movie rating system (👍/😐/👎)
- FileToLink streaming server integrated
- IMDb genre cache + actor cache + ratings DB
- PM search enabled

---

## 📄 Attribution & License

This project is a customized variant of **ShobanaFilterBot**.

- Original project: [github.com/mn-bots/ShobanaFilterBot](https://github.com/mn-bots/ShobanaFilterBot)
- Original author: [MN-TG](https://github.com/mntgxo)
- License: MIT

All original attribution is preserved as required by the license. This customization adds new features without removing credit to the original authors.

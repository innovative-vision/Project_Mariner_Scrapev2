# Discord Search Bot

A focused Discord bot with a `/google` command that returns the top 10 search results in rich embeds with AI-generated TLDRs. Built with a cog-based architecture so new commands slot in without touching existing code.

## Quick Start

```bash
cd discord_bot
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
python bot.py
```

## Bot Structure

```
discord_bot/
├── bot.py                # Entry point — auto-loads all cogs
├── config.py             # Reads .env into typed attributes
├── Procfile              # Railway: worker process
├── railway.toml          # Railway: 1 replica, restart on failure
├── cogs/
│   ├── google.py         # /google command
│   └── _skeleton_cog.py  # Template for new cogs (ignored by loader)
└── utils/
    ├── search.py         # Brave Search / Google CSE abstraction
    └── ai_providers.py   # AI backends with automatic fallback
```

## Railway Deployment

This bot runs as a single **worker** service (no HTTP server needed).

1. Create a new Railway project and add a service pointing at this repo
2. Set the root directory to `discord_bot/`
3. Add all env vars from `.env.example` in the Railway dashboard
4. Deploy — Railway picks up `Procfile` automatically

The `railway.toml` enforces `numReplicas = 1` so you won't accidentally run duplicate bot instances.

## Adding a New Cog

1. Copy `cogs/_skeleton_cog.py` → `cogs/your_feature.py`
2. Rename the class and implement your commands
3. Restart — the bot auto-discovers everything in `cogs/` not starting with `_`

## Search API

| Provider | Free tier | Notes |
|---|---|---|
| **Brave Search** (default) | 2,000 req/month | No credit card — get key at api.search.brave.com |
| Google Custom Search | 100 req/day | Requires Custom Search Engine setup |

Set `SEARCH_PROVIDER=brave` or `google_cse` in `.env`.

## AI for TLDRs

| Role | Provider | Model | Notes |
|---|---|---|---|
| **Primary** | Groq | llama-3.3-70b-versatile | Fast inference, generous free tier |
| **Fallback** | OpenAI | gpt-4o-mini | Auto-kicks in if Groq fails |
| Backup | Claude | claude-haiku-4-5 | Swap via `ACTIVE_AI_PROVIDER=claude` |
| Backup | Gemini | gemini-1.5-flash | Swap via `ACTIVE_AI_PROVIDER=gemini` |
| Backup | Cerebras | llama-3.3-70b | Swap via `ACTIVE_AI_PROVIDER=cerebras` |

Both `GROQ_API_KEY` and `OPENAI_API_KEY` are required (primary + fallback).
Backup provider keys are only needed if you switch `ACTIVE_AI_PROVIDER`.

## `/google` Output

**Embed 1 — Top result:** title, snippet, image, AI TLDR 
**Embed 2 — Results 2–10:** numbered list, link + AI TLDR each

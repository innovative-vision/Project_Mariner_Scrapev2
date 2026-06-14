# Discord Search Bot

A focused Discord bot with a `/google` command that returns the top 10 search results in rich embeds with AI-generated TLDRs. Built with a cog-based architecture so new commands slot in without touching existing code.

## Quick Start

```bash
cd discord_bot
pip install -r requirements.txt
cp .env.example .env   # then fill in your keys
python bot.py
```

## Bot Structure

```
discord_bot/
├── bot.py              # Entry point — auto-loads all cogs
├── config.py           # Reads .env into typed attributes
├── cogs/
│   ├── google.py       # /google command
│   └── _skeleton_cog.py  # Template for new cogs (ignored by loader)
└── utils/
    ├── search.py       # Serper.dev / Google CSE abstraction
    └── ai_providers.py # Pluggable AI backends for TLDRs
```

## Adding a New Cog

1. Copy `cogs/_skeleton_cog.py` → `cogs/your_feature.py`
2. Rename the class and implement your commands
3. Restart the bot — it auto-discovers and loads everything in `cogs/` that doesn't start with `_`

## Search API

| Provider | Free tier | Paid | Notes |
|---|---|---|---|
| **Serper.dev** (recommended) | Trial credits | ~$50 / 50k searches | Fast, images, knowledge graph |
| Google Custom Search API | 100 req/day | $5 / 1k after | Official, setup required |

Set `SEARCH_PROVIDER=serper` or `SEARCH_PROVIDER=google_cse` in `.env`.

## AI Provider for TLDRs

Set `ACTIVE_AI_PROVIDER` in `.env` and uncomment the matching line in `requirements.txt`:

| Value | Model used | SDK |
|---|---|---|
| `claude` | claude-haiku-4-5 | `anthropic` |
| `openai` | gpt-4o-mini | `openai` |
| `gemini` | gemini-1.5-flash | `google-generativeai` |
| `groq` | llama-3.3-70b-versatile | `groq` |
| `cerebras` | llama-3.3-70b | `cerebras-cloud-sdk` |

## `/google` Command Output

**Embed 1 — Top result**
- Title (linked), snippet, featured image
- AI TLDR at the bottom

**Embed 2 — Results 2–10**
- Numbered list, link + AI TLDR per result

## Environment Variables

See `.env.example` for the full list.

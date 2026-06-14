import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Discord
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    PREFIX: str = os.getenv("PREFIX", "!")

    # ── Search provider ───────────────────────────────────────────────────────
    # "brave"      → Brave Search API  (default — 2,000 free/month)
    # "google_cse" → Google Custom Search JSON API (100 free/day)
    SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "brave")
    BRAVE_API_KEY: str = os.getenv("BRAVE_API_KEY", "")
    GOOGLE_CSE_API_KEY: str = os.getenv("GOOGLE_CSE_API_KEY", "")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "")

    # ── AI provider ───────────────────────────────────────────────────────────
    # Primary: groq (fast, generous free tier)
    # Fallback: openai (triggered automatically if primary fails)
    # Backup options: claude | gemini | cerebras (swap via env if needed)
    ACTIVE_AI_PROVIDER: str = os.getenv("ACTIVE_AI_PROVIDER", "groq")
    FALLBACK_AI_PROVIDER: str = os.getenv("FALLBACK_AI_PROVIDER", "openai")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Backup provider keys — only needed if you swap ACTIVE_AI_PROVIDER
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    CEREBRAS_API_KEY: str = os.getenv("CEREBRAS_API_KEY", "")

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Discord
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    PREFIX: str = os.getenv("PREFIX", "!")

    # ── Search provider ───────────────────────────────────────────────────────
    # "serper"     → serper.dev  (recommended: free trial, ~$50/50k searches)
    # "google_cse" → Google Custom Search JSON API (100 free/day)
    SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "serper")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    GOOGLE_CSE_API_KEY: str = os.getenv("GOOGLE_CSE_API_KEY", "")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "")

    # ── AI provider for TLDRs ─────────────────────────────────────────────────
    # Options: "claude" | "openai" | "gemini" | "groq" | "cerebras"
    ACTIVE_AI_PROVIDER: str = os.getenv("ACTIVE_AI_PROVIDER", "claude")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    CEREBRAS_API_KEY: str = os.getenv("CEREBRAS_API_KEY", "")

"""
AI provider abstraction for one-sentence TLDRs.

Active setup (configured via .env):
  Primary  → Groq  (llama-3.3-70b-versatile — fast, generous free tier)
  Fallback → OpenAI (gpt-4o-mini — kicks in automatically if Groq fails)

Backup providers (Claude, Gemini, Cerebras) stay wired up —
swap ACTIVE_AI_PROVIDER in .env to use one instead.
"""
from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from config import Config

log = logging.getLogger(__name__)


class AIProvider(ABC):
    @abstractmethod
    async def tldr(self, title: str, snippet: str, url: str) -> str:
        """Return a single-sentence TLDR for a search result."""


# ─── Groq (PRIMARY default) ────────────────────────────────────────────────────
class GroqProvider(AIProvider):
    def __init__(self):
        from groq import AsyncGroq
        self._client = AsyncGroq(api_key=Config.GROQ_API_KEY)

    async def tldr(self, title: str, snippet: str, url: str) -> str:
        resp = await self._client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=80,
            messages=[{
                "role": "user",
                "content": (
                    "Write a single-sentence TLDR for this search result.\n"
                    f"Title: {title}\nSnippet: {snippet}\nURL: {url}"
                ),
            }],
        )
        return resp.choices[0].message.content.strip()


# ─── OpenAI (FALLBACK) ─────────────────────────────────────────────────────────
class OpenAIProvider(AIProvider):
    def __init__(self):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

    async def tldr(self, title: str, snippet: str, url: str) -> str:
        resp = await self._client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=80,
            messages=[{
                "role": "user",
                "content": (
                    "Write a single-sentence TLDR for this search result.\n"
                    f"Title: {title}\nSnippet: {snippet}\nURL: {url}"
                ),
            }],
        )
        return resp.choices[0].message.content.strip()


# ─── Backup providers — swap via ACTIVE_AI_PROVIDER in .env ────────────────────────
class ClaudeProvider(AIProvider):
    def __init__(self):
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)

    async def tldr(self, title: str, snippet: str, url: str) -> str:
        msg = await self._client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            messages=[{
                "role": "user",
                "content": (
                    "Write a single-sentence TLDR for this search result.\n"
                    f"Title: {title}\nSnippet: {snippet}\nURL: {url}"
                ),
            }],
        )
        return msg.content[0].text.strip()


class GeminiProvider(AIProvider):
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self._model = genai.GenerativeModel("gemini-1.5-flash")

    async def tldr(self, title: str, snippet: str, url: str) -> str:
        resp = await self._model.generate_content_async(
            "Write a single-sentence TLDR for this search result.\n"
            f"Title: {title}\nSnippet: {snippet}\nURL: {url}"
        )
        return resp.text.strip()


class CerebrasProvider(AIProvider):
    def __init__(self):
        from cerebras.cloud.sdk import AsyncCerebras
        self._client = AsyncCerebras(api_key=Config.CEREBRAS_API_KEY)

    async def tldr(self, title: str, snippet: str, url: str) -> str:
        resp = await self._client.chat.completions.create(
            model="llama-3.3-70b",
            max_tokens=80,
            messages=[{
                "role": "user",
                "content": (
                    "Write a single-sentence TLDR for this search result.\n"
                    f"Title: {title}\nSnippet: {snippet}\nURL: {url}"
                ),
            }],
        )
        return resp.choices[0].message.content.strip()


# ─── Fallback wrapper ─────────────────────────────────────────────────────────────
class FallbackProvider(AIProvider):
    """Tries primary, silently falls back to secondary on any exception."""
    def __init__(self, primary: AIProvider, secondary: AIProvider):
        self._primary = primary
        self._secondary = secondary

    async def tldr(self, title: str, snippet: str, url: str) -> str:
        try:
            return await self._primary.tldr(title, snippet, url)
        except Exception as exc:
            log.warning("Primary AI provider failed (%s), using fallback", exc)
            return await self._secondary.tldr(title, snippet, url)


# ─── Registry + factory ───────────────────────────────────────────────────────────
_PROVIDERS: dict[str, type[AIProvider]] = {
    "groq":     GroqProvider,
    "openai":   OpenAIProvider,
    "claude":   ClaudeProvider,
    "gemini":   GeminiProvider,
    "cerebras": CerebrasProvider,
}


def _make(name: str) -> AIProvider:
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown AI provider: {name!r}. Choose from {list(_PROVIDERS)}")
    return cls()


def get_provider() -> AIProvider:
    """
    Returns a FallbackProvider(primary, secondary).
    Defaults: primary=groq, secondary=openai.
    Override via ACTIVE_AI_PROVIDER / FALLBACK_AI_PROVIDER in .env.
    """
    primary = _make(Config.ACTIVE_AI_PROVIDER)
    fallback = _make(Config.FALLBACK_AI_PROVIDER)
    return FallbackProvider(primary, fallback)

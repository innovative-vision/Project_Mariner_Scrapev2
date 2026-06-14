"""
AI provider abstraction for one-sentence TLDRs.

Set ACTIVE_AI_PROVIDER in .env to select a backend.
Only install the SDK for the provider you actually use — see requirements.txt.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from config import Config


class AIProvider(ABC):
    @abstractmethod
    async def tldr(self, title: str, snippet: str, url: str) -> str:
        """Return a single-sentence TLDR for a search result."""


# ─── Claude (Anthropic) ───────────────────────────────────────────────────────
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
                    f"Write a single-sentence TLDR for this search result.\n"
                    f"Title: {title}\nSnippet: {snippet}\nURL: {url}"
                ),
            }],
        )
        return msg.content[0].text.strip()


# ─── OpenAI ───────────────────────────────────────────────────────────────────
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
                    f"Write a single-sentence TLDR for this search result.\n"
                    f"Title: {title}\nSnippet: {snippet}\nURL: {url}"
                ),
            }],
        )
        return resp.choices[0].message.content.strip()


# ─── Google Gemini ────────────────────────────────────────────────────────────
class GeminiProvider(AIProvider):
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self._model = genai.GenerativeModel("gemini-1.5-flash")

    async def tldr(self, title: str, snippet: str, url: str) -> str:
        resp = await self._model.generate_content_async(
            f"Write a single-sentence TLDR for this search result.\n"
            f"Title: {title}\nSnippet: {snippet}\nURL: {url}"
        )
        return resp.text.strip()


# ─── Groq ─────────────────────────────────────────────────────────────────────
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
                    f"Write a single-sentence TLDR for this search result.\n"
                    f"Title: {title}\nSnippet: {snippet}\nURL: {url}"
                ),
            }],
        )
        return resp.choices[0].message.content.strip()


# ─── Cerebras ─────────────────────────────────────────────────────────────────
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
                    f"Write a single-sentence TLDR for this search result.\n"
                    f"Title: {title}\nSnippet: {snippet}\nURL: {url}"
                ),
            }],
        )
        return resp.choices[0].message.content.strip()


# ─── Factory ──────────────────────────────────────────────────────────────────
_PROVIDERS: dict[str, type[AIProvider]] = {
    "claude":   ClaudeProvider,
    "openai":   OpenAIProvider,
    "gemini":   GeminiProvider,
    "groq":     GroqProvider,
    "cerebras": CerebrasProvider,
}


def get_provider() -> AIProvider:
    name = Config.ACTIVE_AI_PROVIDER.lower()
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown ACTIVE_AI_PROVIDER: {name!r}. "
            f"Choose from: {list(_PROVIDERS)}"
        )
    return cls()

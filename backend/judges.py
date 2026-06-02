"""Three independent AI judge personalities via OpenRouter.

Integration is silently disabled when OPENROUTER_API_KEY is absent.
All three judges are called in parallel (asyncio.gather).
"""

import asyncio
import os
from typing import Optional

import httpx

_OPENROUTER_API_KEY: Optional[str] = None
_judges_enabled = False

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ---------------------------------------------------------------------------
# Judge definitions — model + personality system prompt
# ---------------------------------------------------------------------------

JUDGES = [
    {
        "name": "Judge Dmitri",
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "system": (
            "You are Judge Dmitri — blunt, analytical, and direct. "
            "You review AI responses with zero tolerance for vagueness. "
            "State clearly whether the response is accurate, partially accurate, "
            "or wrong, and explain your reasoning in 3-5 concise sentences. "
            "No flattery. No hedging."
        ),
    },
    {
        "name": "The Architect",
        "model": "nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
        "system": (
            "You are The Architect — you think in systems and structures. "
            "Evaluate the AI response by examining its logical structure, "
            "completeness, and whether the reasoning holds up. "
            "Identify any structural gaps or logical leaps. "
            "Keep your assessment to 3-5 sentences."
        ),
    },
    {
        "name": "Agent Zero",
        "model": "meta-llama/llama-4-maverick:free",
        "system": (
            "You are Agent Zero — a generalist with broad knowledge. "
            "Evaluate the AI response from a practical, real-world perspective. "
            "Would this answer actually help someone? Is anything missing or misleading? "
            "Give your view plainly in 3-5 sentences."
        ),
    },
]


def init():
    """Wire up the OpenRouter API key. Call once at startup."""
    global _OPENROUTER_API_KEY, _judges_enabled
    _OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if _OPENROUTER_API_KEY:
        _judges_enabled = True
        print("[judges] OpenRouter integration enabled — 3 judges active")
    else:
        print("[judges] OPENROUTER_API_KEY not set — judge integration disabled")


async def _call_judge(
    client: httpx.AsyncClient,
    judge: dict,
    prompt: str,
    gemini_response: str,
) -> dict:
    """Call a single judge model and return its opinion."""
    user_message = (
        f"Original question:\n{prompt}\n\n"
        f"AI response under review:\n{gemini_response}"
    )
    payload = {
        "model": judge["model"],
        "messages": [
            {"role": "system", "content": judge["system"]},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 300,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": "Bearer " + _OPENROUTER_API_KEY,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/innovative-vision/Project_Mariner_Scrapev2",
        "X-Title": "Gemini Shadow Courtroom",
    }

    try:
        r = await client.post(
            _OPENROUTER_URL,
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        text = f"[error] {exc}"

    return {"judge": judge["name"], "model": judge["model"], "text": text}


async def get_opinions(prompt: str, gemini_response: str) -> list:
    """Fan out to all three judges in parallel and return their opinions.

    Returns an empty list when the integration is disabled.
    """
    if not _judges_enabled:
        return []

    async with httpx.AsyncClient() as client:
        tasks = [
            _call_judge(client, judge, prompt, gemini_response)
            for judge in JUDGES
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    opinions = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            opinions.append({
                "judge": JUDGES[i]["name"],
                "model": JUDGES[i]["model"],
                "text": f"[error] {result}",
            })
        else:
            opinions.append(result)

    return opinions

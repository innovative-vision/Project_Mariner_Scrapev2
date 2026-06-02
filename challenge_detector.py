"""Heuristic challenge / CAPTCHA / anti-bot detection.

Inspects the current Playwright page and returns a ChallengeStatus
describing any blocking condition found.
"""

from enum import Enum
from typing import Optional


class ChallengeStatus(Enum):
    OK = "OK"
    CAPTCHA = "CAPTCHA"
    BOT_CHALLENGE = "BOT_CHALLENGE"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    SCRIPT_BLOCKED = "SCRIPT_BLOCKED"
    RATE_LIMITED = "RATE_LIMITED"
    UNKNOWN_BLOCK = "UNKNOWN_BLOCK"


# Keyword signatures used for heuristic detection.
# Ordered from most-specific to least-specific.
_CAPTCHA_SIGNALS = [
    "recaptcha",
    "hcaptcha",
    "i'm not a robot",
    "verify you are human",
    "prove you're human",
    "captcha",
]

_BOT_CHALLENGE_SIGNALS = [
    "cloudflare",
    "ddos-guard",
    "just a moment",
    "checking your browser",
    "enable javascript",
    "access denied",
    "403 forbidden",
    "bot protection",
    "ray id",
]

_LOGIN_SIGNALS = [
    "sign in to continue",
    "log in to continue",
    "please sign in",
    "please log in",
    "login required",
    "you must be logged in",
    "create an account",
]

_RATE_LIMIT_SIGNALS = [
    "too many requests",
    "rate limit",
    "429",
    "slow down",
]

_SCRIPT_BLOCKED_SIGNALS = [
    "javascript is disabled",
    "enable javascript",
    "this page requires javascript",
]


def _normalise(text: str) -> str:
    return text.lower().replace("\n", " ")


async def detect(page, strictness: str = "basic") -> ChallengeStatus:
    """Analyse *page* and return the relevant ChallengeStatus.

    Parameters
    ----------
    page:
        A Playwright ``Page`` object.
    strictness:
        ``"strict"`` — flag any unexpected/empty state as UNKNOWN_BLOCK.
        ``"basic"``  — only flag obvious challenge patterns.
    """
    try:
        title = await page.title()
        body = await page.inner_text("body")
    except Exception:
        # If we can't read the page at all that is itself suspicious.
        if strictness == "strict":
            return ChallengeStatus.UNKNOWN_BLOCK
        return ChallengeStatus.OK

    content = _normalise(f"{title} {body}")

    # Check in priority order
    for signal in _CAPTCHA_SIGNALS:
        if signal in content:
            return ChallengeStatus.CAPTCHA

    for signal in _BOT_CHALLENGE_SIGNALS:
        if signal in content:
            return ChallengeStatus.BOT_CHALLENGE

    for signal in _RATE_LIMIT_SIGNALS:
        if signal in content:
            return ChallengeStatus.RATE_LIMITED

    for signal in _SCRIPT_BLOCKED_SIGNALS:
        if signal in content:
            return ChallengeStatus.SCRIPT_BLOCKED

    for signal in _LOGIN_SIGNALS:
        if signal in content:
            return ChallengeStatus.LOGIN_REQUIRED

    # Strict mode: treat suspiciously short/empty pages as unknown blocks.
    if strictness == "strict" and len(body.strip()) < 200:
        return ChallengeStatus.UNKNOWN_BLOCK

    return ChallengeStatus.OK


def status_to_result_reason(status: ChallengeStatus) -> Optional[str]:
    """Map a ChallengeStatus to a human-readable agent result reason."""
    mapping = {
        ChallengeStatus.CAPTCHA: "CAPTCHA challenge detected — manual verification required",
        ChallengeStatus.BOT_CHALLENGE: "Bot-protection wall detected",
        ChallengeStatus.LOGIN_REQUIRED: "Login required before proceeding",
        ChallengeStatus.SCRIPT_BLOCKED: "Page failed to boot due to blocked scripts/resources",
        ChallengeStatus.RATE_LIMITED: "Rate-limited by the target site",
        ChallengeStatus.UNKNOWN_BLOCK: "Unknown blocking condition on page",
        ChallengeStatus.OK: None,
    }
    return mapping.get(status)

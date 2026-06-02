"""Site policy loader and domain tier classifier.

Reads policies/default.yaml and resolves the effective policy for any domain.
"""

import os
from dataclasses import dataclass
from typing import Optional
import yaml


POLICY_FILE = os.path.join(os.path.dirname(__file__), "policies", "default.yaml")
DEFAULT_KEY = "__default__"


@dataclass
class SitePolicy:
    domain: str
    tier: int
    access_mode: str
    persistent_profile: bool
    headless_allowed: bool
    manual_checkpoint: bool
    challenge_strictness: str
    resource_blocking: bool

    def is_autonomous(self) -> bool:
        """Return True when the policy allows fully autonomous browser operation."""
        return self.access_mode in ("browser", "api_first")

    def requires_manual(self) -> bool:
        return self.access_mode == "browser_manual_only" or self.manual_checkpoint

    def is_unsupported(self) -> bool:
        return self.access_mode == "unsupported"


_POLICY_CACHE: Optional[dict] = None


def _load_raw() -> dict:
    global _POLICY_CACHE
    if _POLICY_CACHE is None:
        with open(POLICY_FILE, "r") as fh:
            data = yaml.safe_load(fh)
        _POLICY_CACHE = data.get("policies", {})
    return _POLICY_CACHE


def _build_policy(domain: str, raw: dict) -> SitePolicy:
    return SitePolicy(
        domain=domain,
        tier=int(raw.get("tier", 3)),
        access_mode=raw.get("access_mode", "browser"),
        persistent_profile=bool(raw.get("persistent_profile", False)),
        headless_allowed=bool(raw.get("headless_allowed", True)),
        manual_checkpoint=bool(raw.get("manual_checkpoint", False)),
        challenge_strictness=raw.get("challenge_strictness", "basic"),
        resource_blocking=bool(raw.get("resource_blocking", True)),
    )


def get_policy(domain: str) -> SitePolicy:
    """Return the effective SitePolicy for *domain*.

    Resolution order:
    1. Exact match (e.g. ``discord.com``)
    2. Parent-domain suffix match (e.g. policy for ``example.com`` covers
       ``sub.example.com``)
    3. ``__default__`` fallback
    """
    raw_policies = _load_raw()
    domain = domain.lower().strip()

    # Exact match
    if domain in raw_policies:
        return _build_policy(domain, raw_policies[domain])

    # Suffix / parent-domain match
    for key, raw in raw_policies.items():
        if key == DEFAULT_KEY:
            continue
        if domain.endswith("." + key) or domain == key:
            return _build_policy(key, raw)

    # Default fallback
    default_raw = raw_policies.get(DEFAULT_KEY, {})
    return _build_policy(domain, default_raw)


def extract_domain(url_or_task: str) -> Optional[str]:
    """Best-effort extraction of a domain from a URL or free-text task string."""
    import re
    # Try a URL pattern first
    url_match = re.search(
        r"https?://(?:www\.)?([a-zA-Z0-9\-]+(?:\.[a-zA-Z]{2,})+)", url_or_task
    )
    if url_match:
        return url_match.group(1).lower()
    # Try bare domain pattern
    bare_match = re.search(
        r"\b([a-zA-Z0-9\-]+\.(?:com|org|net|io|gov|edu|co\.[a-z]{2}|[a-z]{2}))\b",
        url_or_task,
    )
    if bare_match:
        return bare_match.group(1).lower()
    return None

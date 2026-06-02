"""Persistent browser profile / session manager.

Tier 1 sites get a dedicated persistent profile directory so cookies,
local storage, and session state survive across runs.

Tier 2/3 sites can use a shared lightweight profile or an ephemeral
context as directed by policy.
"""

import os
import shutil


PROFILES_ROOT = os.path.join(os.path.dirname(__file__), ".profiles")


def _sanitise(domain: str) -> str:
    """Convert a domain name into a safe directory component."""
    return domain.replace(".", "_").replace("/", "_")


def get_profile_dir(domain: str) -> str:
    """Return the path to the persistent profile directory for *domain*.

    The directory is created if it does not already exist.
    """
    profile_dir = os.path.join(PROFILES_ROOT, _sanitise(domain))
    os.makedirs(profile_dir, exist_ok=True)
    return profile_dir


def get_shared_profile_dir() -> str:
    """Return a shared profile directory for Tier 2 sites."""
    shared = os.path.join(PROFILES_ROOT, "__shared__")
    os.makedirs(shared, exist_ok=True)
    return shared


def clear_profile(domain: str) -> bool:
    """Delete the persistent profile for *domain*.

    Returns True if a profile existed and was removed, False otherwise.
    """
    profile_dir = os.path.join(PROFILES_ROOT, _sanitise(domain))
    if os.path.isdir(profile_dir):
        shutil.rmtree(profile_dir)
        return True
    return False


def list_profiles() -> list:
    """Return the list of domain profiles currently stored on disk."""
    if not os.path.isdir(PROFILES_ROOT):
        return []
    return [
        entry
        for entry in os.listdir(PROFILES_ROOT)
        if os.path.isdir(os.path.join(PROFILES_ROOT, entry))
        and not entry.startswith(".")
    ]


def resolve_profile(domain: str, tier: int, persistent_profile: bool) -> dict:
    """Return a dict of browser-context kwargs for the given policy settings.

    The returned dict can be unpacked into BrowserConfig / context options
    that control profile persistence.
    """
    if persistent_profile or tier == 1:
        return {"user_data_dir": get_profile_dir(domain)}
    if tier == 2:
        return {"user_data_dir": get_shared_profile_dir()}
    # Tier 3 / ephemeral — no persistent profile
    return {}

"""Human-in-the-loop manual checkpoint / resume flow.

When the agent encounters a challenge (CAPTCHA, login wall, bot check) on a
protected site it calls ``wait_for_user_resolution`` to:

1. Print a clear terminal notice to the user.
2. Keep the browser open so the user can manually resolve the issue.
3. Optionally re-check the page state after the user confirms.
4. Return True if the block was resolved, False if the user skips/quits.
"""

import asyncio
import sys
from typing import Optional

from challenge_detector import detect, ChallengeStatus


_SEPARATOR = "=" * 60


def _print_checkpoint_notice(domain: str, reason: str) -> None:
    print(f"\n{_SEPARATOR}")
    print("  ⚠  MANUAL CHECKPOINT REQUIRED")
    print(_SEPARATOR)
    print(f"  Site   : {domain}")
    print(f"  Reason : {reason}")
    print()
    print("  The browser window is open. Please resolve the issue")
    print("  manually (e.g. complete the CAPTCHA, log in, etc.).")
    print()
    print("  When done, return here and press ENTER to continue,")
    print("  or type 'skip' and press ENTER to abort this task.")
    print(f"{_SEPARATOR}\n")


async def wait_for_user_resolution(
    page,
    domain: str,
    reason: str,
    strictness: str = "basic",
    recheck: bool = True,
) -> bool:
    """Pause execution and hand control to the user.

    Parameters
    ----------
    page:
        The active Playwright ``Page`` object (kept open for manual use).
    domain:
        The domain being accessed (used in the notice message).
    reason:
        Human-readable description of the blocking condition.
    strictness:
        Passed to :func:`challenge_detector.detect` on re-check.
    recheck:
        If True, re-run challenge detection after the user confirms before
        returning, to verify the block was actually cleared.

    Returns
    -------
    bool
        ``True`` if the blocking condition appears resolved, ``False`` if the
        user chose to skip or the block persists after re-check.
    """
    _print_checkpoint_notice(domain, reason)

    loop = asyncio.get_event_loop()
    user_input = await loop.run_in_executor(
        None, lambda: input("  > ").strip().lower()
    )

    if user_input in ("skip", "s", "quit", "q", "exit"):
        print("\n  [checkpoint] Skipped by user.\n")
        return False

    if recheck and page is not None:
        print("\n  [checkpoint] Re-checking page state …")
        status = await detect(page, strictness=strictness)
        if status != ChallengeStatus.OK:
            print(f"  [checkpoint] Block still detected ({status.value}). Aborting.\n")
            return False
        print("  [checkpoint] Page looks clear — resuming.\n")

    return True


def print_final_checkpoint_summary(domain: str, resolved: bool) -> None:
    """Print a brief summary line after the checkpoint completes."""
    icon = "✓" if resolved else "✗"
    state = "resolved" if resolved else "not resolved"
    print(f"  [{icon}] Manual checkpoint for {domain}: {state}\n")

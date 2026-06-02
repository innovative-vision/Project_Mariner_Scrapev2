"""4-hour summary cron job.

Uses APScheduler (if installed) to run a Gemini Flash summarisation of
all exchanges logged in the previous window, then appends the result to
Google Sheets.

The scheduler is **optional**: if APScheduler is not installed or
GEMINI_API_KEY is absent, this module is a no-op.
"""

import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

_scheduler = None
_scheduler_enabled = False

# Interval in hours between summary runs (overridable via env var).
_SUMMARY_INTERVAL_HOURS = int(os.getenv("SUMMARY_INTERVAL_HOURS", "4"))


def _build_gemini_summary(exchanges: list) -> str:
    """Call Gemini Flash to summarise a list of exchange dicts."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "[disabled] GEMINI_API_KEY not set"

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        if not exchanges:
            return "Nil"

        exchange_text = "\n\n".join(
            f"[{ex.get('timestamp', 'unknown')}]\n"
            f"Prompt: {ex.get('prompt', '')}\n"
            f"Response: {ex.get('response', '')}"
            for ex in exchanges
        )

        prompt = (
            f"You are a concise analyst. Below are {len(exchanges)} AI conversation "
            f"exchange(s) from the last {_SUMMARY_INTERVAL_HOURS} hours. "
            "Write a 3-5 sentence summary covering: the main topics discussed, "
            "any notable patterns, and the overall quality of the AI responses. "
            "Be direct.\n\n"
            f"{exchange_text}"
        )

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:
        return f"[error] {exc}"


def _run_summary(exchange_buffer: list) -> None:
    """Pull buffered exchanges, summarise, write to Sheets, then clear buffer."""
    from backend import google_docs  # avoid circular import at module level

    now_utc = datetime.now(timezone.utc).isoformat()
    count = len(exchange_buffer)

    print(f"[scheduler] Running {_SUMMARY_INTERVAL_HOURS}h summary — "
          f"{count} exchange(s) to summarise")

    summary = _build_gemini_summary(exchange_buffer)
    print(f"[scheduler] Summary: {summary[:120]}{'...' if len(summary) > 120 else ''}")

    ok = google_docs.append_summary_row(summary, count)
    if ok:
        print("[scheduler] Summary written to Google Sheets ✓")
    else:
        print("[scheduler] Sheets write skipped (integration disabled or error)")

    # Clear the buffer in-place so the caller's reference is updated too.
    exchange_buffer.clear()


def init(exchange_buffer: list) -> None:
    """Start the background scheduler.

    *exchange_buffer* is the shared list from main.py that accumulates
    logged exchanges.  The scheduler holds a reference to it so it can
    drain it every N hours.
    """
    global _scheduler, _scheduler_enabled

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        print("[scheduler] APScheduler not installed — cron summarisation disabled")
        return

    if not os.getenv("GEMINI_API_KEY"):
        print("[scheduler] GEMINI_API_KEY not set — cron summarisation disabled")
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_summary,
        "interval",
        hours=_SUMMARY_INTERVAL_HOURS,
        args=[exchange_buffer],
        id="summary_job",
    )
    _scheduler.start()
    _scheduler_enabled = True
    print(f"[scheduler] Cron summarisation enabled — every {_SUMMARY_INTERVAL_HOURS}h ✓")


def shutdown() -> None:
    """Gracefully stop the scheduler on app exit."""
    if _scheduler and _scheduler_enabled:
        _scheduler.shutdown(wait=False)

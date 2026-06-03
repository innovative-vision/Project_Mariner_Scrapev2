"""Structured logger for the Browser-Use Agent.

Writes one JSONL record per run to logs/agent.log covering:
  - Run metadata      : run_id, timestamp, task, domain, tier, policy details
  - Browser session   : profile used, headless mode
  - URLs visited      : every page navigated to during the run
  - Actions taken     : clicks, form fills, navigation steps, extractions
  - Challenge events  : CAPTCHA / bot-wall / login-wall detections
  - Manual checkpoint : triggered, user response, resolved/not
  - Judge verdicts    : per-model verdict from the 3-judge panel
  - Final result      : status, output snippet, duration, error reason

Usage
-----
    from logger import RunLogger

    log = RunLogger(task="...", domain="...", policy=policy)
    log.url_visited("https://example.com/page")
    log.action("click", detail="Submit button")
    log.judge_verdict("judge_dmitri", "AGREE", "Answer looks correct")
    log.finish(result)          # writes the record to disk
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOGS_DIR, "agent.log")


def _ensure_log_dir() -> None:
    os.makedirs(LOGS_DIR, exist_ok=True)


@dataclass
class RunLogger:
    task: str
    domain: str
    policy: object  # SitePolicy — kept loosely typed to avoid circular import

    # Auto-populated
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    start_time: float = field(default_factory=time.time)

    # Accumulated during run
    _urls: list = field(default_factory=list)
    _actions: list = field(default_factory=list)
    _challenges: list = field(default_factory=list)
    _checkpoints: list = field(default_factory=list)
    _judges: list = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Public recording methods                                             #
    # ------------------------------------------------------------------ #

    def url_visited(self, url: str) -> None:
        """Record a URL the browser navigated to."""
        self._urls.append({
            "url": url,
            "t": round(time.time() - self.start_time, 2),
        })

    def action(self, action_type: str, detail: str = "", url: str = "") -> None:
        """Record a browser action (click, fill, navigate, extract, etc.)."""
        self._actions.append({
            "type": action_type,
            "detail": detail,
            "url": url,
            "t": round(time.time() - self.start_time, 2),
        })

    def challenge_detected(self, status: str, url: str = "") -> None:
        """Record a challenge/block event (CAPTCHA, bot-wall, login wall, etc.)."""
        self._challenges.append({
            "status": status,
            "url": url,
            "t": round(time.time() - self.start_time, 2),
        })

    def checkpoint(self, domain: str, reason: str, resolved: bool) -> None:
        """Record a manual checkpoint event and its outcome."""
        self._checkpoints.append({
            "domain": domain,
            "reason": reason,
            "resolved": resolved,
            "t": round(time.time() - self.start_time, 2),
        })

    def judge_verdict(
        self,
        judge_name: str,
        verdict: str,
        reasoning: str = "",
        model: str = "",
    ) -> None:
        """Record a single judge's verdict from the 3-panel review."""
        self._judges.append({
            "judge": judge_name,
            "model": model,
            "verdict": verdict,
            "reasoning": reasoning[:500],  # cap to keep log sizes sane
            "t": round(time.time() - self.start_time, 2),
        })

    def finish(self, result) -> None:
        """Finalise the log record and append it to logs/agent.log.

        Parameters
        ----------
        result : AgentResult
            The final result returned by run_task().
        """
        _ensure_log_dir()

        duration = round(time.time() - self.start_time, 2)

        # Derive judge panel summary
        verdicts = [j["verdict"] for j in self._judges]
        agree_count = sum(1 for v in verdicts if v.upper() == "AGREE")
        disagree_count = sum(1 for v in verdicts if v.upper() == "DISAGREE")
        if verdicts:
            if agree_count >= 2:
                panel_summary = "GREEN"
            elif disagree_count >= 2:
                panel_summary = "RED"
            else:
                panel_summary = "AMBER"
        else:
            panel_summary = "NO_PANEL"

        record = {
            # --- Run identity ---
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_s": duration,

            # --- Task ---
            "task": self.task,
            "domain": self.domain,

            # --- Policy / browser session ---
            "tier": getattr(self.policy, "tier", None),
            "access_mode": getattr(self.policy, "access_mode", None),
            "headless": getattr(self.policy, "headless_allowed", None),
            "persistent_profile": getattr(self.policy, "persistent_profile", None),
            "challenge_strictness": getattr(self.policy, "challenge_strictness", None),

            # --- What happened ---
            "urls_visited": self._urls,
            "actions": self._actions,
            "challenges": self._challenges,
            "manual_checkpoints": self._checkpoints,

            # --- Judge panel ---
            "judges": self._judges,
            "panel_summary": panel_summary,

            # --- Outcome ---
            "status": result.status.value if result else "UNKNOWN",
            "output_snippet": (result.output or "")[:1000],
            "error_reason": result.reason if result else None,
        }

        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

        _print_run_summary(record)


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _print_run_summary(record: dict) -> None:
    """Print a compact human-readable summary to stdout."""
    print("\n" + "=" * 60)
    print(f"  RUN SUMMARY  [{record['run_id']}]")
    print("=" * 60)
    print(f"  Task        : {record['task'][:80]}")
    print(f"  Domain      : {record['domain']}  (Tier {record['tier']})")
    print(f"  Duration    : {record['duration_s']}s")
    print(f"  URLs seen   : {len(record['urls_visited'])}")
    print(f"  Actions     : {len(record['actions'])}")
    print(f"  Challenges  : {len(record['challenges'])}")
    print(f"  Panel       : {record['panel_summary']}")
    print(f"  Status      : {record['status']}")
    if record.get("error_reason"):
        print(f"  Reason      : {record['error_reason']}")
    print(f"  Log         : {LOG_FILE}")
    print("=" * 60 + "\n")

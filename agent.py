"""Browser-Use Agent — Gemini Edition (tiered trust/autonomy model).

Entrypoint for the autonomous browsing agent.  The agent now uses a
policy-driven architecture that treats different websites differently:

  Tier 1 — high-value, stateful, anti-bot-sensitive sites (e.g. discord.com)
            Full persistent profiles, manual checkpoints, strict challenge
            handling.
  Tier 2 — general web sites; reliability matters, shared profile optional.
  Tier 3 — disposable/generic public web; ephemeral, fully autonomous.

Run:
    python3 agent.py
or pass a task directly:
    python3 agent.py "Go to wikipedia.org and summarise the main article"
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from langchain_google_genai import ChatGoogleGenerativeAI

from agent_result import AgentResult, AgentResultStatus
from site_policies import get_policy, extract_domain
from session_manager import resolve_profile
from challenge_detector import detect, ChallengeStatus, status_to_result_reason
from manual_checkpoint import wait_for_user_resolution, print_final_checkpoint_summary
from logger import RunLogger

load_dotenv()

_DEFAULT_TASK = "Go to google.com and tell me what the weather is in Melbourne, Australia"


def _build_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.0,
    )


def _build_browser(policy) -> Browser:
    """Create a Browser whose configuration is driven by *policy*."""
    profile_kwargs = resolve_profile(
        policy.domain,
        policy.tier,
        policy.persistent_profile,
    )
    headless = policy.headless_allowed

    config = BrowserConfig(
        headless=headless,
        **profile_kwargs,
    )
    return Browser(config=config)


async def run_task(task: str) -> AgentResult:
    """Run *task* and return a structured AgentResult."""
    domain = extract_domain(task) or "unknown"
    policy = get_policy(domain)

    # Initialise logger for this run
    log = RunLogger(task=task, domain=domain, policy=policy)

    print(f"\n[policy] domain={domain}  tier={policy.tier}  "
          f"mode={policy.access_mode}  headless={policy.headless_allowed}  "
          f"persistent_profile={policy.persistent_profile}")

    # Hard stop for unsupported sites.
    if policy.is_unsupported():
        result = AgentResult(
            status=AgentResultStatus.SITE_POLICY_DISALLOWS_AUTONOMOUS_MODE,
            domain=domain,
            reason=f"Site policy marks {domain!r} as unsupported",
        )
        log.finish(result)
        return result

    browser = _build_browser(policy)
    llm = _build_llm()

    # For manual-only sites, warn the user upfront.
    if policy.requires_manual():
        print(f"\n[policy] {domain!r} is configured for manual-checkpoint mode.")
        print("         The browser will open for you to handle any challenges.\n")

    # Hook into browser-use action callbacks to capture URLs + actions
    def _on_action(action_info):
        """Callback fired by browser-use before each agent action."""
        try:
            action_type = action_info.get("action", "unknown")
            detail = str(action_info.get("params", ""))
            url = action_info.get("url", "")
            log.action(action_type, detail=detail, url=url)
            if url:
                log.url_visited(url)
        except Exception:
            pass  # Never let logging break the agent

    agent = Agent(task=task, llm=llm, browser=browser)

    # Attach action hook if the version supports it
    try:
        agent.register_action_hook(_on_action)
    except AttributeError:
        pass

    result = None
    try:
        raw_result = await agent.run()
    except Exception as exc:
        result = AgentResult(
            status=AgentResultStatus.UNKNOWN_FAILURE,
            domain=domain,
            reason=str(exc),
        )
        log.finish(result)
        return result
    finally:
        # Attempt challenge detection on the final page state.
        try:
            playwright_page = browser.playwright_browser  # may not exist on all versions
            if playwright_page and hasattr(playwright_page, "pages") and playwright_page.pages:
                page = playwright_page.pages[-1]

                # Log the final URL
                try:
                    final_url = page.url
                    if final_url:
                        log.url_visited(final_url)
                except Exception:
                    pass

                challenge = await detect(page, strictness=policy.challenge_strictness)

                if challenge != ChallengeStatus.OK:
                    reason = status_to_result_reason(challenge)
                    print(f"\n[challenge] {challenge.value} — {reason}")
                    log.challenge_detected(challenge.value, url=page.url)

                    # Offer manual intervention when policy allows/requires it.
                    if policy.requires_manual():
                        resolved = await wait_for_user_resolution(
                            page=page,
                            domain=domain,
                            reason=reason or challenge.value,
                            strictness=policy.challenge_strictness,
                        )
                        print_final_checkpoint_summary(domain, resolved)
                        log.checkpoint(domain, reason or challenge.value, resolved)

                        if not resolved:
                            result = AgentResult(
                                status=AgentResultStatus.MANUAL_VERIFICATION_REQUIRED,
                                domain=domain,
                                reason=reason,
                            )
                            log.finish(result)
                            return result
        except Exception:
            pass  # Best-effort challenge detection; don't mask the primary result.

    output = str(raw_result) if raw_result is not None else ""
    print("\n--- RESULT ---")
    print(output)

    result = AgentResult(
        status=AgentResultStatus.SUCCESS,
        domain=domain,
        output=output,
    )
    log.finish(result)
    return result


def main() -> None:
    print("Browser-Use Agent — Gemini Edition (tiered trust/autonomy model)")
    print("Type your task below. The agent will browse the web and complete it.")
    print("Example: 'Go to reddit.com and find the top post in r/Python today'\n")

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:]).strip()
        print(f"Task (from args): {task}\n")
    else:
        task = input("Task: ").strip()
        if not task:
            task = _DEFAULT_TASK
            print(f"No task entered — using default: {task}\n")

    result = asyncio.run(run_task(task))

    if not result.succeeded():
        print(f"\n[agent] Task did not complete successfully: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()

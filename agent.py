"""Browser-Use Agent (tiered trust/autonomy model).

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
from dataclasses import dataclass

from dotenv import load_dotenv
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from agent_result import AgentResult, AgentResultStatus
from site_policies import get_policy, extract_domain
from session_manager import resolve_profile
from challenge_detector import detect, ChallengeStatus, status_to_result_reason
from manual_checkpoint import wait_for_user_resolution, print_final_checkpoint_summary

load_dotenv()

_DEFAULT_TASK = "Go to google.com and tell me what the weather is in Melbourne, Australia"


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    api_key_env: str
    base_url: str | None = None


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} not set. Add it to your .env file.")
    return value


def _get_llm_config() -> LLMConfig:
    provider = os.getenv("LLM_PROVIDER", "nvidia_nim").strip().lower()

    if provider in {"nvidia", "nvidia_nim", "nim"}:
        return LLMConfig(
            provider="nvidia_nim",
            model=os.getenv("NVIDIA_NIM_MODEL", "z-ai/glm-5.2"),
            api_key_env="NVIDIA_NIM_API_KEY",
            base_url=os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        )

    if provider == "gemini":
        return LLMConfig(
            provider="gemini",
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            api_key_env="GEMINI_API_KEY",
        )

    raise ValueError(
        "Unsupported LLM_PROVIDER. Use 'nvidia_nim' (default) or 'gemini'."
    )


def _build_llm():
    config = _get_llm_config()
    api_key = _require_env(config.api_key_env)

    if config.provider == "nvidia_nim":
        return ChatOpenAI(
            model=config.model,
            api_key=api_key,
            base_url=config.base_url,
            temperature=0.0,
        )

    return ChatGoogleGenerativeAI(
        model=config.model,
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

    print(f"\n[policy] domain={domain}  tier={policy.tier}  "
          f"mode={policy.access_mode}  headless={policy.headless_allowed}  "
          f"persistent_profile={policy.persistent_profile}")

    # Hard stop for unsupported sites.
    if policy.is_unsupported():
        return AgentResult(
            status=AgentResultStatus.SITE_POLICY_DISALLOWS_AUTONOMOUS_MODE,
            domain=domain,
            reason=f"Site policy marks {domain!r} as unsupported",
        )

    browser = _build_browser(policy)
    llm = _build_llm()

    # For manual-only sites, warn the user upfront.
    if policy.requires_manual():
        print(f"\n[policy] {domain!r} is configured for manual-checkpoint mode.")
        print("         The browser will open for you to handle any challenges.\n")

    agent = Agent(task=task, llm=llm, browser=browser)

    try:
        raw_result = await agent.run()
    except Exception as exc:
        return AgentResult(
            status=AgentResultStatus.UNKNOWN_FAILURE,
            domain=domain,
            reason=str(exc),
        )
    finally:
        # Attempt challenge detection on the final page state.
        try:
            playwright_page = browser.playwright_browser  # may not exist on all versions
            if playwright_page and hasattr(playwright_page, "pages") and playwright_page.pages:
                page = playwright_page.pages[-1]
                challenge = await detect(page, strictness=policy.challenge_strictness)

                if challenge != ChallengeStatus.OK:
                    reason = status_to_result_reason(challenge)
                    print(f"\n[challenge] {challenge.value} — {reason}")

                    # Offer manual intervention when policy allows/requires it.
                    if policy.requires_manual():
                        resolved = await wait_for_user_resolution(
                            page=page,
                            domain=domain,
                            reason=reason or challenge.value,
                            strictness=policy.challenge_strictness,
                        )
                        print_final_checkpoint_summary(domain, resolved)
                        if not resolved:
                            return AgentResult(
                                status=AgentResultStatus.MANUAL_VERIFICATION_REQUIRED,
                                domain=domain,
                                reason=reason,
                            )
        except Exception:
            pass  # Best-effort challenge detection; don't mask the primary result.

    output = str(raw_result) if raw_result is not None else ""
    print("\n--- RESULT ---")
    print(output)
    return AgentResult(
        status=AgentResultStatus.SUCCESS,
        domain=domain,
        output=output,
    )


def main() -> None:
    llm_config = _get_llm_config()

    print("Browser-Use Agent (tiered trust/autonomy model)")
    print(f"LLM backend: {llm_config.provider} ({llm_config.model})")
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

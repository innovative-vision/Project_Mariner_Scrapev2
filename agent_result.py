from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class AgentResultStatus(Enum):
    SUCCESS = "SUCCESS"
    MANUAL_VERIFICATION_REQUIRED = "MANUAL_VERIFICATION_REQUIRED"
    BLOCKED_BY_BOT_PROTECTION = "BLOCKED_BY_BOT_PROTECTION"
    LOGIN_SESSION_EXPIRED = "LOGIN_SESSION_EXPIRED"
    SITE_POLICY_DISALLOWS_AUTONOMOUS_MODE = "SITE_POLICY_DISALLOWS_AUTONOMOUS_MODE"
    PAGE_BOOT_FAILED_DUE_TO_BLOCKED_RESOURCES = "PAGE_BOOT_FAILED_DUE_TO_BLOCKED_RESOURCES"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


@dataclass
class AgentResult:
    status: AgentResultStatus
    output: Optional[str] = None
    reason: Optional[str] = None
    domain: Optional[str] = None

    def succeeded(self) -> bool:
        return self.status == AgentResultStatus.SUCCESS

    def __str__(self) -> str:
        parts = [f"[{self.status.value}]"]
        if self.domain:
            parts.append(f"domain={self.domain}")
        if self.output:
            parts.append(self.output)
        if self.reason:
            parts.append(f"({self.reason})")
        return " ".join(parts)

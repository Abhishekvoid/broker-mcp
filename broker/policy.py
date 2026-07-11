from dataclasses import dataclass


class PolicyDenied(Exception):
    pass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


ALLOWED_REPO = "Abhishekvoid/broker-mcp"
ALLOWED_ACTION = "github.issues.create"


def evaluate(action: str, repo: str) -> PolicyDecision:
    if action != ALLOWED_ACTION:
        return PolicyDecision(False, f"action {action} not permitted")
    if repo != ALLOWED_REPO:
        return PolicyDecision(False, f"repo {repo} not in allowlist")
    return PolicyDecision(True, "matches allowlist")
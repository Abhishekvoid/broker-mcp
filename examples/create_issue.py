"""
Broker MCP — capability lifecycle demo.

Creates a GitHub issue via Broker. No standing credential is present in this
process's environment; Broker mints a short-lived installation token, uses it
for one API call, and the token expires with GitHub's server-side TTL.

Run:
    python -m examples.create_issue
"""
import json
from broker.github import create_issue
from broker.policy import PolicyDenied

REPO = "Abhishekvoid/broker-mcp"


def demo_allow():
    print(f"\n--- capability request: github.issues.create on {REPO} ---")
    result = create_issue(
        repo=REPO,
        title="[broker] capability lifecycle demo",
        body="Issued by Broker. See audit.jsonl for the full lifecycle.",
    )
    print(json.dumps(result, indent=2))
    print(f"\nissue: {result['url']}")


def demo_deny():
    bad_repo = "Abhishekvoid/some-other-repo"
    print(f"\n--- capability request: github.issues.create on {bad_repo} ---")
    try:
        create_issue(repo=bad_repo, title="denied", body="")
    except PolicyDenied as e:
        print(f"DENIED: {e}")


if __name__ == "__main__":
    demo_allow()
    demo_deny()
    print("\nfull audit trail: audit.jsonl")
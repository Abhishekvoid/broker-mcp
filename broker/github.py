import time
import jwt
import requests
from broker.config import (
    GITHUB_APP_ID,
    GITHUB_INSTALLATION_ID,
    load_private_key,
)
from broker.capability import Capability, new_capability
from broker.policy import evaluate, PolicyDenied
from broker.audit import record

GITHUB_API = "https://api.github.com"


def _app_jwt() -> str:
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 9 * 60,
        "iss": GITHUB_APP_ID,
    }
    return jwt.encode(payload, load_private_key(), algorithm="RS256")


def mint_capability(scope: str) -> Capability:
    """Exchange the App JWT for a short-lived installation token,
    wrapped in a Capability. The raw token is never returned."""
    app_jwt = _app_jwt()
    resp = requests.post(
        f"{GITHUB_API}/app/installations/{GITHUB_INSTALLATION_ID}/access_tokens",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return new_capability(
        provider="github",
        scope=scope,
        token=data["token"],
        expires_at_iso=data["expires_at"],
    )


def create_issue(repo: str, title: str, body: str = "") -> dict:
    action = "github.issues.create"
    decision = evaluate(action=action, repo=repo)

    record({
        "event": "policy.decision",
        "action": action,
        "repo": repo,
        "allowed": decision.allowed,
        "reason": decision.reason,
    })

    if not decision.allowed:
        raise PolicyDenied(decision.reason)

    cap = mint_capability(scope="issues:write")

    record({
        "event": "capability.minted",
        "capability_id": cap.id,
        "provider": cap.provider,
        "scope": cap.scope,
        "ttl_seconds": cap.ttl_seconds,
        "expires_at": cap.expires_at,
    })

    resp = requests.post(
        f"{GITHUB_API}/repos/{repo}/issues",
        headers={
            "Authorization": f"Bearer {cap._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"title": title, "body": body},
        timeout=10,
    )
    resp.raise_for_status()
    issue = resp.json()

    record({
        "event": "capability.used",
        "capability_id": cap.id,
        "outcome": "success",
        "resource": issue["html_url"],
    })

    return {
        "number": issue["number"],
        "url": issue["html_url"],
        "capability": cap.to_public_dict(),
    }
# Replacing GitHub PATs with Ephemeral Installation Tokens

*Give an AI agent GitHub access without giving it a standing credential.*

## The problem

Every AI agent I build eventually needs to touch GitHub — open an issue, push a
branch, comment on a PR. And every guide, every example repo, every quickstart
solves that the same way: generate a personal access token, paste it into `.env`,
move on. I did it too, for a long time, and it always felt wrong.

A classic PAT is a *standing* credential. It's long-lived — valid until you
remember to revoke it. It's broadly scoped — it carries your whole account's
reach, not the one thing the agent needs right now. And it's ambient — it sits in
the process environment where any code path can read it, where a stack trace can
log it, and where a prompt-injected agent can be talked into exfiltrating it. Fine-
grained PATs help at the margins — per-repo, optional expiry — but they're still a
credential a developer scopes by hand, pastes into an environment, and leaves lying
there for weeks. Broker isn't competing with them; it's replacing the pattern of
putting any long-lived credential where an agent can read it. The shape of the
problem doesn't change: the agent is holding power it isn't using.

## The idea

GitHub already has a better primitive, and almost nobody uses it for agents.

A GitHub **App** doesn't authenticate with a token you store. It authenticates by
signing a short JWT with a private key, then exchanging that JWT for an
**installation access token** — scoped to exactly the repositories and permissions
you granted the App, and expiring on GitHub's side in about an hour. Nothing to
rotate. Nothing broad. Nothing that outlives the moment.

The reason people reach for a PAT anyway is ergonomics: the JWT dance, the App
registration, the installation IDs — it's more moving parts than "paste a token."
So I built **Broker**, a small capability broker that makes installation tokens
the *default* path for an agent. The agent asks for an action; Broker checks
policy, mints a token at the instant of use, spends it on one call, and logs the
whole lifecycle. The agent never sees or stores a credential.

## The demo

Here is the entire thesis in one screenshot. An LLM, wired to Broker over MCP,
asked it to create an issue in a repository that isn't on the allowlist:

![Claude explaining that Broker denied the call because the repo is not on the allowlist](https://raw.githubusercontent.com/Abhishekvoid/broker-mcp/main/docs/demo-04-denied.png)

*An LLM asked Broker to create an issue in a non-allowlisted repo. Broker refused.
No token was ever minted.*

That last sentence is the whole point. In the PAT model, the agent already holds
the credential — policy is something you hope the agent respects, or something you
bolt on after the fact. Here, the credential *does not exist yet* when the decision
is made. Policy runs first. A denial isn't "the agent was told no"; it's "there was
never anything to say no with." The token for a forbidden action is never minted,
never sent, never logged — because Broker never reaches the mint step. The deny
path is cheaper and safer than the allow path, which is exactly the property you
want in a security boundary.

Broker speaks the Model Context Protocol, which is how Claude Desktop and a growing
number of agent frameworks discover and call external tools. That's what makes the
demo work end-to-end: the LLM saw `github_create_issue` in Broker's tool catalog,
chose to call it with structured parameters, and got back either a capability object
or a policy denial. The interception point isn't code the developer had to write.
It's the tool boundary itself.

## How it works

The whole thing is three small files.

**`broker/policy.py` is one function.** It takes an action and a repo and returns a
decision — allow or deny with a reason. That's it:

```python
def evaluate(action: str, repo: str) -> PolicyDecision:
    if action != ALLOWED_ACTION:
        return PolicyDecision(False, f"action {action} not permitted")
    if repo != ALLOWED_REPO:
        return PolicyDecision(False, f"repo {repo} not in allowlist")
    return PolicyDecision(True, "matches allowlist")
```

It runs *before* any credential exists. Wrong repo or wrong action, and the request
dies here.

**`broker/github.py` does the JWT → installation-token exchange.** It signs an
`RS256` JWT with the App private key (a nine-minute expiry, per GitHub's ceiling),
POSTs it to `/app/installations/{id}/access_tokens`, and wraps the returned token in
a `Capability`. The raw token goes into a private field and never leaves the object —
callers get a public view with the token stripped out.

**`broker/audit.py` is `json.dumps` to a file.** Every stage — the policy decision,
the mint, the use and its outcome — appends one timestamped JSON line to
`audit.jsonl`. Tokens are never written. You get a replayable, grep-able trail of
who asked for what and what happened.

The difference is easiest to see in what the agent actually holds. With a PAT:

```bash
# .env — sits here for the life of the project
GITHUB_TOKEN=ghp_R8sNq...   # your whole account. no expiry. readable by any code path.
```

With Broker, the only thing the agent ever receives is the public capability:

```json
{
  "id": "CAP-6AEB2D42",
  "provider": "github",
  "scope": "issues:write",
  "ttl_seconds": 3598,
  "expires_at": "2026-07-11T08:34:05Z",
  "status": "ACTIVE"
}
```

No secret in there. Just a receipt.

| | PAT in `.env` | Broker capability |
|---|---|---|
| **If it leaks** | Full account access | An already-expiring, single-scope token |
| **Scope** | Whole account | One action (`issues:write`) |
| **Lifetime** | Months, until revoked | ~1 hour, server-enforced |
| **Storage** | Sits in the environment | Never stored; minted per call |

## Limitations

I want to be precise about what this v0.1 is and isn't, because the gaps matter more
than the pitch.

The `.pem` is still a real secret. Broker moves the standing credential from the
agent's environment to the App's private key — a single, high-value key that lives
outside the repo and is git-ignored along with `.env` and `audit.jsonl`. That's a
better key to have to protect, but it's still a key.

"Spend once" is a *discipline*, not an enforcement. Broker mints a token and uses it
for exactly one call — but the token it mints is a real GitHub installation token
with a server-side expiry of roughly an hour. Broker does no local revocation, so
within that window the token would technically still work if it leaked between mint
and use. True one-shot, immediately-revoked credentials are future work.

And the policy engine is deliberately tiny: a single action against a single-repo
allowlist. There's no per-caller policy, no rate limiting, no multi-tenant story
yet. Those are extension points, not shipped features.

## What's next

Two directions. First, other providers — the same pattern maps cleanly onto **AWS
STS** (`AssumeRole` for short-lived, scoped credentials), and the provider layer is
where that plugs in. Second, the awkward reality that some services only offer
long-lived keys: those can be wrapped behind the same policy-and-audit layer, so
even a legacy secret is spent through a broker instead of handed to the agent.

The repo is open source and MIT-licensed:
**[github.com/Abhishekvoid/broker-mcp](https://github.com/Abhishekvoid/broker-mcp)**.
It's small enough to read in one sitting — kick the tires and tell me where it
breaks.

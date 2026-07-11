"""
Broker MCP server.

Exposes GitHub capabilities as MCP tools. An MCP client (Claude Desktop,
Cursor, etc.) connects over stdio; each tool call goes through Broker's
policy → capability mint → API call → audit pipeline.
"""
from mcp.server.fastmcp import FastMCP
from broker.github import create_issue as broker_create_issue
from broker.policy import PolicyDenied

mcp = FastMCP("broker")


@mcp.tool()
def github_create_issue(repo: str, title: str, body: str = "") -> dict:
    """
    Create a GitHub issue via Broker.

    Broker mints a short-lived GitHub App installation token, uses it for
    exactly this call, and records the capability lifecycle in audit.jsonl.
    No standing credential is exposed to the caller.

    Args:
        repo: "owner/name" — must be on Broker's allowlist.
        title: Issue title.
        body: Issue body (optional).
    """
    try:
        return broker_create_issue(repo=repo, title=title, body=body)
    except PolicyDenied as e:
        return {"error": "policy_denied", "reason": str(e)}


if __name__ == "__main__":
    mcp.run()
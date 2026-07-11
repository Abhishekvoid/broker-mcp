import json
from datetime import datetime, timezone
from pathlib import Path

# Anchor to the repo root (parent of the broker package) so the audit trail
# always lands here regardless of the process's working directory — MCP hosts
# may launch the server from an arbitrary cwd.
AUDIT_LOG = Path(__file__).resolve().parent.parent / "audit.jsonl"


def record(event: dict) -> None:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
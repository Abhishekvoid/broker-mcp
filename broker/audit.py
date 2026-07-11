import json
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG = Path("audit.jsonl")


def record(event: dict) -> None:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **event,
    }
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class Capability:
    id: str
    provider: str
    scope: str
    ttl_seconds: int
    expires_at: str
    status: str
    _token: str = ""

    def to_public_dict(self) -> dict:
        
        d = asdict(self)
        d.pop("_token", None)
        return d


def new_capability(provider: str, scope: str, token: str, expires_at_iso: str) -> Capability:
    expires = datetime.fromisoformat(expires_at_iso.replace("Z", "+00:00"))
    ttl = int((expires - datetime.now(timezone.utc)).total_seconds())
    return Capability(
        id=f"CAP-{uuid.uuid4().hex[:8].upper()}",
        provider=provider,
        scope=scope,
        ttl_seconds=ttl,
        expires_at=expires_at_iso,
        status="ACTIVE",
        _token=token,
    )
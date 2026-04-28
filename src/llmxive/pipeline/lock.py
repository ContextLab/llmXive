"""Per-project advisory lock (T018, FR-005).

state/locks/<PROJ-ID>.lock is a small YAML sentinel that records the
holder run id, acquisition time, and expiry. Stale locks (expires_at in
the past) are forcibly released on next acquire.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from llmxive.types import Lock


class LockError(RuntimeError):
    """Raised when a lock acquisition cannot proceed."""


def _state_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "state"


def _lock_path(project_id: str, *, repo_root: Path | None = None) -> Path:
    state_dir = (repo_root / "state") if repo_root else _state_root()
    return state_dir / "locks" / f"{project_id}.lock"


def acquire(
    project_id: str,
    *,
    holder_run_id: str,
    ttl_seconds: int = 3600,
    repo_root: Path | None = None,
) -> Lock:
    """Acquire the lock or raise LockError if it's actively held.

    Stale locks (expires_at < now) are silently overwritten.
    """
    path = _lock_path(project_id, repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    if path.exists():
        existing = Lock.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        if existing.expires_at > now:
            raise LockError(
                f"project {project_id} is locked by run {existing.holder_run_id} "
                f"until {existing.expires_at.isoformat()}"
            )
    lock = Lock(
        project_id=project_id,
        holder_run_id=holder_run_id,
        acquired_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds),
    )
    path.write_text(
        yaml.safe_dump(lock.model_dump(mode="json"), sort_keys=True),
        encoding="utf-8",
    )
    return lock


def release(project_id: str, *, holder_run_id: str, repo_root: Path | None = None) -> bool:
    """Release the lock if held by `holder_run_id`. Returns True if released."""
    path = _lock_path(project_id, repo_root=repo_root)
    if not path.exists():
        return False
    existing = Lock.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if existing.holder_run_id != holder_run_id:
        return False
    path.unlink()
    return True


def is_locked(project_id: str, *, repo_root: Path | None = None) -> bool:
    path = _lock_path(project_id, repo_root=repo_root)
    if not path.exists():
        return False
    existing = Lock.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    return existing.expires_at > datetime.now(timezone.utc)


__all__ = ["acquire", "release", "is_locked", "LockError"]

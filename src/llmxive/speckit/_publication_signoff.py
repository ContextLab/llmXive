"""Persisted manual maintainer DOI sign-off (spec 015 T035, FR-054).

Spec 015 / discrepancy #2 + clarify Q1: the publisher was not wired into the
graph (``paper_accepted → posted`` shortcut), and even after wiring there must be
a MANDATORY manual maintainer sign-off before any Zenodo DOI is minted (initial
publication or living-document version). This module persists that approval to
``<project>/.specify/memory/publication_signoff.yaml`` with the who/when/what
record FR-054 requires, and exposes read/write/clear helpers used by the graph,
the publisher, and the CLI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

_FILENAME = "publication_signoff.yaml"


def _signoff_path(memory_dir: Path) -> Path:
    return memory_dir / _FILENAME


def read_signoff(memory_dir: Path) -> dict[str, Any] | None:
    """Return the persisted sign-off record or ``None`` if no approval recorded."""
    p = _signoff_path(memory_dir)
    if not p.exists():
        return None
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def has_signoff(memory_dir: Path) -> bool:
    return read_signoff(memory_dir) is not None


def write_signoff(
    memory_dir: Path,
    *,
    who: str,
    what: str,
    kind: str = "initial",
    when: str | None = None,
) -> Path:
    """Record FR-054 sign-off (who/when/what). ``kind`` distinguishes the initial
    publication from a living-document version DOI."""
    if not who or not who.strip():
        raise ValueError("publication sign-off requires a non-empty 'who'")
    if not what or not what.strip():
        raise ValueError("publication sign-off requires a non-empty 'what'")
    if kind not in ("initial", "version"):
        raise ValueError(f"publication sign-off kind must be 'initial' or 'version', got {kind!r}")
    memory_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "who": who.strip(),
        "what": what.strip(),
        "kind": kind,
        "when": when or datetime.now(UTC).isoformat(),
    }
    p = _signoff_path(memory_dir)
    p.write_text(yaml.safe_dump(record, sort_keys=True), encoding="utf-8")
    return p


def clear_signoff(memory_dir: Path) -> None:
    """Remove the persisted approval (e.g., after a successful DOI mint, so a
    later version DOI requires a fresh sign-off)."""
    p = _signoff_path(memory_dir)
    if p.exists():
        p.unlink()


__all__ = [
    "clear_signoff",
    "has_signoff",
    "read_signoff",
    "write_signoff",
]

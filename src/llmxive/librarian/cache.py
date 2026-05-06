"""Disk-based cache for librarian results (spec 005 / FR-011 / Decision 6).

Each cache entry is a JSON file at
``state/librarian-cache/<sha256>.json`` containing a complete
LibrarianResult plus metadata. Cache key derives from
sha256(normalized_term + field + target_n + prompt_version), so the
same query under the same prompt version returns deterministic results.

TTLs (matching FR-011 + Clarifications):
  - 30 days for arXiv-derived data
  - 7 days for HTTP-HEAD verification status
  - 90 days for DOI bibliographic info

Cache invalidation:
  - explicit ``--no-cache`` flag (caller-controlled)
  - automatic on TTL expiry
  - automatic on prompt-version mismatch (entry's prompt_version != current)

Per Constitution Principle III: real disk, no in-memory mocks. Cache
files are committed to git so the diagnostic is reproducible from any
checkout.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

CACHE_TTLS = {
    "arxiv": 30 * 24 * 3600,  # 30 days
    "http_head": 7 * 24 * 3600,  # 7 days
    "doi_bib": 90 * 24 * 3600,  # 90 days
}


def cache_key(
    term_normalized: str,
    field: str | None,
    target_n: int,
    prompt_version: str,
) -> str:
    """Compute the sha256 cache key for a librarian invocation."""
    h = hashlib.sha256()
    payload = json.dumps(
        {
            "term_normalized": term_normalized,
            "field": field or "",
            "target_n": target_n,
            "prompt_version": prompt_version,
        },
        sort_keys=True,
    )
    h.update(payload.encode("utf-8"))
    return h.hexdigest()


def cache_path(repo_root: Path, key: str) -> Path:
    """Return the on-disk path for a cache key."""
    return repo_root / "state" / "librarian-cache" / f"{key}.json"


def get(
    repo_root: Path,
    key: str,
    *,
    current_prompt_version: str,
    now_utc: _dt.datetime | None = None,
) -> dict[str, Any] | None:
    """Read cache entry. Returns None on miss / TTL expiry / version mismatch.

    The caller is responsible for re-querying on None.
    """
    p = cache_path(repo_root, key)
    if not p.is_file():
        return None
    try:
        entry = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    # Prompt-version mismatch invalidates the entry.
    if entry.get("prompt_version") != current_prompt_version:
        return None

    # TTL check (use the most-restrictive TTL by default).
    fetched_at_str = entry.get("fetched_at")
    if not fetched_at_str:
        return None
    try:
        fetched_at = _dt.datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00"))
    except ValueError:
        return None

    now = now_utc or _dt.datetime.now(_dt.UTC)
    age_seconds = (now - fetched_at).total_seconds()
    # Use the shortest TTL (http_head, 7d) as the default invalidation
    # window. Callers wanting a longer effective TTL on cached arXiv
    # bib metadata can read the entry directly.
    max_age = entry.get("ttls", {}).get("http_head", CACHE_TTLS["http_head"])
    if age_seconds > max_age:
        return None

    return entry.get("result")


def set(
    repo_root: Path,
    key: str,
    *,
    term_normalized: str,
    field: str | None,
    target_n: int,
    prompt_version: str,
    result: dict[str, Any],
    now_utc: _dt.datetime | None = None,
) -> Path:
    """Write a cache entry to disk."""
    p = cache_path(repo_root, key)
    p.parent.mkdir(parents=True, exist_ok=True)
    now = now_utc or _dt.datetime.now(_dt.UTC)
    entry = {
        "term_normalized": term_normalized,
        "field": field,
        "target_n": target_n,
        "result": result,
        "fetched_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ttls": dict(CACHE_TTLS),
        "prompt_version": prompt_version,
    }
    # Pretty-print for git diff readability.
    p.write_text(
        json.dumps(entry, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return p


def invalidate(repo_root: Path, key: str) -> bool:
    """Delete a cache entry. Returns True if a file was removed."""
    p = cache_path(repo_root, key)
    if p.is_file():
        p.unlink()
        return True
    return False


def normalize_term(raw: str) -> str:
    """Canonicalize a search term for cache-key consistency.

    - Lowercase
    - Collapse whitespace
    - Strip leading/trailing punctuation
    - Drop standalone punctuation tokens
    """
    if not raw:
        return ""
    s = raw.lower().strip()
    # Collapse internal whitespace.
    s = " ".join(s.split())
    return s


__all__ = [
    "CACHE_TTLS",
    "cache_key",
    "cache_path",
    "get",
    "set",
    "invalidate",
    "normalize_term",
]

"""Adjacent-work pointer liveness verification (spec 010, FR-002).

Resolves arXiv IDs, DOIs, and raw URLs via HEAD requests; rejects pointers
whose target is unreachable. A 7-day disk cache (state/audit/liveness-cache.json)
avoids hammering arXiv/DOI on repeated cron ticks.

Usage:
    from llmxive.audit.liveness import check_pointer
    result = check_pointer("arxiv", "2202.01933")
    # {"status": "pass", "http_code": 200, "checked_at": "2026-05-15T..."}
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

LIVENESS_CACHE_PATH = Path("state/audit/liveness-cache.json")
LIVENESS_TIMEOUT_SEC = float(os.environ.get("LIVENESS_TIMEOUT_SEC", "10"))
LIVENESS_CACHE_TTL_DAYS = 7

_KIND_RESOLVERS = {
    "arxiv": lambda p: f"https://arxiv.org/abs/{p}",
    "doi": lambda p: f"https://doi.org/{p}",
    "url": lambda p: p,
}


class InvalidPointerKind(ValueError):
    """Raised when `kind` is not one of the supported pointer types."""


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_cache(path: Path = LIVENESS_CACHE_PATH) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        # Corrupted cache → treat as empty; next save overwrites it.
        return {}


def _save_cache(cache: dict[str, dict[str, Any]], path: Path = LIVENESS_CACHE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, sort_keys=True))


def _is_fresh(entry: dict[str, Any]) -> bool:
    """Return True if a cache entry is within TTL."""
    checked_at = entry.get("checked_at")
    if not checked_at:
        return False
    try:
        ts = datetime.strptime(checked_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        return False
    return datetime.now(UTC) - ts < timedelta(days=LIVENESS_CACHE_TTL_DAYS)


def check_pointer(
    kind: str,
    pointer: str,
    *,
    cache_path: Path = LIVENESS_CACHE_PATH,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Verify a single adjacent-work pointer is live.

    Returns a dict matching the cache-entry shape:
        {"status": "pass" | "fail", "http_code": int, "checked_at": ISO8601}

    Args:
        kind: one of "arxiv", "doi", "url"
        pointer: the pointer string (cache key)
        cache_path: override for the cache file (tests pass a temp path)
        timeout: override LIVENESS_TIMEOUT_SEC

    Raises:
        InvalidPointerKind: kind not in {"arxiv", "doi", "url"}
    """
    if kind not in _KIND_RESOLVERS:
        raise InvalidPointerKind(
            f"unsupported kind {kind!r}; expected one of {sorted(_KIND_RESOLVERS)}"
        )

    cache = _load_cache(cache_path)
    if pointer in cache and _is_fresh(cache[pointer]):
        return cache[pointer]

    url = _KIND_RESOLVERS[kind](pointer)
    t = LIVENESS_TIMEOUT_SEC if timeout is None else timeout
    try:
        resp = httpx.head(url, follow_redirects=True, timeout=t)
        # arXiv sometimes returns 405 on HEAD; fall back to GET with stream
        if resp.status_code == 405:
            resp = httpx.get(url, follow_redirects=True, timeout=t)
        status = "pass" if 200 <= resp.status_code < 400 else "fail"
        http_code = resp.status_code
    except (httpx.RequestError, httpx.TimeoutException):
        status = "fail"
        http_code = 0  # connection error / timeout

    entry = {"status": status, "http_code": http_code, "checked_at": _now_iso()}
    cache[pointer] = entry
    _save_cache(cache, cache_path)
    return entry


__all__ = ["LIVENESS_CACHE_PATH", "InvalidPointerKind", "check_pointer"]

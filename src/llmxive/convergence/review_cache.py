"""Resumable, content-addressed cache for convergence panel reviews.

WHY: a convergence transition runs each panel lens's R1 ``identify`` review
as a ~234s reasoning call. When the circuit-breaker aborts a run
mid-transition (e.g. a qwen outage), the NEXT run re-does the whole
transition from scratch, re-paying every lens review even though the
artifact is unchanged. This persistent, content-addressed cache lets an
aborted-then-restarted run REUSE a prior review of the SAME artifact
instead of re-calling the model — making outages cheap to recover from.

CORRECTNESS IS PARAMOUNT. A wrong cache HIT is a wrong scientific review.
The cache key (:func:`compose_key`) hashes EVERY input that determines the
review output — the exact composed user message, the system prompt, the
lens, the stage, and the model. If ANY of these differ it is a guaranteed
MISS (a fresh model call). A HIT returns an exact round-trip of the stored
``list[Concern]`` (pydantic ``model_dump`` / ``model_validate``).

This mirrors the on-disk approach of ``llmxive.grounding.cache``: one JSON
file per key-hash under ``state/convergence-cache/``, an atomic write, a
TTL (default 14 days, env-overridable via
``LLMXIVE_CONVERGENCE_CACHE_TTL_DAYS``), and best-effort error handling
(any read/write/parse error is swallowed and falls through to a normal
model call — the cache NEVER crashes a review or changes its result on
error).

Kill-switch: ``LLMXIVE_CONVERGENCE_CACHE`` (default ENABLED). Set it to
``0`` / ``false`` / ``no`` / ``off`` to disable the cache entirely — when
disabled the reviewer always calls the model and never reads or writes the
cache, byte-identical to the pre-cache behavior.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
import time
from pathlib import Path

from .types import Concern

logger = logging.getLogger(__name__)

# Field separator chosen to never appear in a sha256 hex digest or in the
# canonical concatenation of independently-length-prefixed inputs.
_SENTINEL = "\x1e"  # ASCII record separator

# Default TTL: 14 days. Env-overridable (in days) so an operator can widen
# or tighten staleness without a code change. A negative / zero TTL makes
# every stored entry expired → an unconditional MISS.
_DEFAULT_TTL_DAYS = 14.0


# --- enable / TTL knobs ---------------------------------------------------


def cache_enabled() -> bool:
    """Return True unless ``LLMXIVE_CONVERGENCE_CACHE`` is a falsey string.

    Default ENABLED. Recognised disable values (case-insensitive):
    ``0``, ``false``, ``no``, ``off``.
    """
    val = os.environ.get("LLMXIVE_CONVERGENCE_CACHE")
    if val is None:
        return True
    return val.strip().lower() not in {"0", "false", "no", "off"}


def _ttl_seconds() -> float:
    raw = os.environ.get("LLMXIVE_CONVERGENCE_CACHE_TTL_DAYS")
    if raw is None or not raw.strip():
        return _DEFAULT_TTL_DAYS * 24 * 3600
    try:
        return float(raw) * 24 * 3600
    except ValueError:
        logger.debug("bad LLMXIVE_CONVERGENCE_CACHE_TTL_DAYS=%r; using default", raw)
        return _DEFAULT_TTL_DAYS * 24 * 3600


def _now() -> float:
    return time.time()


def convergence_cache_dir(repo_root: Path) -> Path:
    """Directory for the convergence review cache (transient, uncommitted)."""
    return Path(repo_root) / "state" / "convergence-cache"


# --- key composition ------------------------------------------------------


def compose_key(
    *,
    user: str,
    system: str,
    lens: str,
    stage: str,
    model: str | None,
) -> str:
    """Hash ALL review-determining inputs into a stable 64-char sha256.

    The inputs are length-prefixed and joined with a record-separator
    sentinel so that no concatenation of one set of inputs can ever equal
    a different set's concatenation (i.e. no boundary ambiguity — e.g.
    ``user='ab', system='c'`` cannot collide with ``user='a', system='bc'``).

    ``model`` distinguishes ``None`` (no model pinned) from ``""`` (an
    empty model string) via a one-char presence flag, since those are
    different inputs to the backend router.
    """
    model_flag = "0" if model is None else "1"
    model_val = "" if model is None else model
    fields = (user, system, lens, stage, model_flag, model_val)
    canonical = _SENTINEL.join(f"{len(f)}:{f}" for f in fields)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --- persistence ----------------------------------------------------------


def _path_for(repo_root: Path, key: str) -> Path:
    return convergence_cache_dir(repo_root) / f"{key}.json"


def load(repo_root: Path, key: str) -> list[Concern] | None:
    """Return the cached concern list for ``key``, or ``None`` on MISS.

    A MISS is any of: cache disabled, no file, expired (past TTL),
    unreadable file, malformed JSON, or a payload that fails to
    round-trip back into ``Concern`` models. Every failure mode is
    swallowed (logged at debug) and reported as a plain MISS — the cache
    never raises into the review path.
    """
    if not cache_enabled():
        return None
    path = _path_for(repo_root, key)
    try:
        if not path.exists():
            return None
        rec = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        logger.debug("convergence cache read failed for %s: %s", key, exc)
        return None
    try:
        ttl = _ttl_seconds()
        if ttl <= 0 or (_now() - float(rec.get("_ts", 0))) > ttl:
            return None
        raw = rec.get("concerns")
        if not isinstance(raw, list):
            return None
        return [Concern.model_validate(c) for c in raw]
    except Exception as exc:  # deserialization / validation — best effort
        logger.debug("convergence cache deserialize failed for %s: %s", key, exc)
        return None


def store(repo_root: Path, key: str, concerns: list[Concern]) -> None:
    """Persist ``concerns`` under ``key`` (atomic write). Best-effort.

    A no-op when the cache is disabled. Any IO error is swallowed (logged
    at debug) — failing to WRITE the cache must never break a review.
    """
    if not cache_enabled():
        return
    try:
        directory = convergence_cache_dir(repo_root)
        directory.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({
            "_ts": _now(),
            "concerns": [c.model_dump(mode="json") for c in concerns],
        })
        path = _path_for(repo_root, key)
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".json.tmp")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(payload)
            os.replace(tmp, path)  # atomic
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except Exception as exc:  # best-effort: never crash a review on write
        logger.debug("convergence cache write failed for %s: %s", key, exc)


__all__ = [
    "cache_enabled",
    "compose_key",
    "convergence_cache_dir",
    "load",
    "store",
]

"""Last-known-good (LKG) component store for the runtime snapshot (spec 026, slice 1).

When a live acquisition of a snapshot component (Dartmouth catalog, local
inventory, credit-guard balance, Hugging Face catalog, or leaderboard scores)
FAILS, the snapshot may fall back to the last value that was successfully
observed — marked ``source=last_known_good`` with its TRUE age (FR-007, spec
§48). This module persists those per-component values.

Design notes:

- **Per-component, not whole-snapshot.** Each component is stored independently
  with its own ``observed_at`` timestamp, so a transient credit-balance blip does
  NOT discard a perfectly good catalog cache (and vice-versa). Only components
  that succeed live this run get their LKG entry refreshed; the rest are preserved.
- **Best-effort cache, not authoritative state.** A stale-but-valid LKG value is
  acceptable (the selector enforces ``max_catalog_age_s``), so writes are simple
  last-writer-wins atomic writes (via ``state/_io.atomic_write_text``) — NOT the
  strict compare-and-swap the credit-reservation ledger (slice 1B) requires.
- **Corruption tolerance (Fail Fast, Constitution V).** A malformed file, a
  schema-version mismatch, or a self-digest mismatch (truncation/tampering that
  still parses) is treated as ABSENT — a cold start, never a crash. The next
  successful acquisition heals the file.

This module is generic over the payload: it stores/validates ``{component:
(observed_at, payload_dict)}``; ``snapshot.py`` owns (de)serializing its domain
types (``ModelRef``/``ModelPricing``/``CreditGuardSnapshot``) to/from the payload.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from llmxive.config import repo_root
from llmxive.state._io import atomic_write_text

logger = logging.getLogger(__name__)

#: Bump when the on-disk payload shape changes; an older/newer file is ABSENT.
LKG_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class LKGEntry:
    """One component's last successfully-observed value + when it was observed."""

    observed_at: datetime
    payload: dict


def _default_lkg_path() -> Path:
    return repo_root() / "state" / "model_selection" / "lkg_snapshot.json"


def _component_digest(components: dict[str, dict]) -> str:
    """SHA-256 over the canonical components blob (excludes the digest field
    itself), used to detect truncation/tampering that still parses as JSON."""
    return hashlib.sha256(
        json.dumps(components, sort_keys=True, default=str).encode()
    ).hexdigest()


class LKGStore:
    """Reads/writes the per-component last-known-good file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _default_lkg_path()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> dict[str, LKGEntry]:
        """Return ``{component: LKGEntry}``. A missing, malformed, wrong-version,
        or digest-mismatched file yields ``{}`` (treated as absent / cold start)."""
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("LKG file unreadable (%s: %s); treating as absent", type(exc).__name__, exc)
            return {}

        try:
            if raw.get("schema_version") != LKG_SCHEMA_VERSION:
                logger.warning(
                    "LKG schema_version %r != %d; treating as absent",
                    raw.get("schema_version"), LKG_SCHEMA_VERSION,
                )
                return {}
            components = raw["components"]
            if not isinstance(components, dict):
                raise TypeError("components is not an object")
            if _component_digest(components) != raw.get("digest"):
                logger.warning("LKG digest mismatch (truncated/tampered); treating as absent")
                return {}
            out: dict[str, LKGEntry] = {}
            for name, entry in components.items():
                out[name] = LKGEntry(
                    observed_at=datetime.fromisoformat(entry["observed_at"]),
                    payload=entry["payload"],
                )
            return out
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("LKG content invalid (%s: %s); treating as absent", type(exc).__name__, exc)
            return {}

    def record(self, updates: dict[str, LKGEntry]) -> None:
        """Merge freshly-observed ``updates`` over the currently-valid entries and
        atomically rewrite the file. Components NOT in ``updates`` are preserved
        (per-component freshness); a currently-corrupt file is healed by the write.

        No-op if ``updates`` is empty (nothing succeeded live this run)."""
        if not updates:
            return
        merged: dict[str, LKGEntry] = dict(self.load())
        merged.update(updates)
        components = {
            name: {"observed_at": e.observed_at.isoformat(), "payload": e.payload}
            for name, e in merged.items()
        }
        blob = {
            "schema_version": LKG_SCHEMA_VERSION,
            "digest": _component_digest(components),
            "components": components,
        }
        atomic_write_text(self._path, json.dumps(blob, indent=2, sort_keys=True))

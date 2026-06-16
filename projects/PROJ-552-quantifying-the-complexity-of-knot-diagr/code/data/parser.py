"""
Parser for Knot Atlas data.

This module provides:
- ``ParsedKnotData``: dataclass representing the cleaned knot record.
- ``KnotParser``: class encapsulating the parsing logic for a single
  ``download.knot_atlas_loader.KnotRecord``.
- ``parse_knot_atlas_data``: function that reads the raw JSON file,
  applies tie‑breaking rules, and returns a list of ``ParsedKnotData``.
- ``verify_parser_consistency``: lightweight sanity‑check that can be
  used by downstream validation scripts.

Tie‑breaking rules (FR‑011):
  1. Prefer a record that contains a ``braid_word`` over one that only has a
     ``dt_code``.
  2. If both candidates have a ``braid_word`` (or both have a ``dt_code``)
     choose the lexicographically smaller string.
The rules are applied per knot identifier so that the final cleaned dataset
contains exactly one record per knot.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from download.knot_atlas_loader import KnotRecord

__all__ = [
    "ParsedKnotData",
    "KnotParser",
    "parse_knot_atlas_data",
    "verify_parser_consistency",
]


@dataclass
class ParsedKnotData:
    """
    Normalised representation of a knot record.

    Attributes
    ----------
    knot_id: str
        Unique identifier for the knot (e.g. ``"3_1"`` for the trefoil).
    crossing_number: int
    braid_index: int
    hyperbolic_volume: float | None
    alternating: bool | None
    braid_word: str | None
    dt_code: str | None
    """

    knot_id: str
    crossing_number: int
    braid_index: int
    hyperbolic_volume: Optional[float] = None
    alternating: Optional[bool] = None
    braid_word: Optional[str] = None
    dt_code: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        """Return a plain‑dict suitable for ``pandas.DataFrame`` construction."""
        return asdict(self)


class KnotParser:
    """
    Parser for a single ``KnotRecord`` coming from the Knot Atlas downloader.

    The parser extracts the fields required for the downstream analysis and
    normalises them to the types defined in :class:`ParsedKnotData`.
    """

    @staticmethod
    def _bool_from_value(value: Any) -> Optional[bool]:
        """Coerce common truthy / falsy representations to ``bool``."""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"yes", "true", "alternating", "alternating knot"}:
                return True
            if lowered in {"no", "false", "nonalternating", "non‑alternating"}:
                return False
        return None

    @staticmethod
    def _float_from_value(value: Any) -> Optional[float]:
        """Convert a value to ``float`` if possible."""
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _int_from_value(value: Any) -> Optional[int]:
        """Convert a value to ``int`` if possible."""
        if value is None:
            return None
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return None

    def parse(self, record: KnotRecord) -> ParsedKnotData:
        """
        Parse a ``KnotRecord`` into a ``ParsedKnotData`` instance.

        Parameters
        ----------
        record: KnotRecord
            Raw record as returned by :func:`download.knot_atlas_loader.download_knot_atlas_data`.

        Returns
        -------
        ParsedKnotData
        """
        # The ``KnotRecord`` is a dataclass; we can treat it as a dict via ``asdict``.
        raw = asdict(record)

        knot_id = str(raw.get("name") or raw.get("id") or raw.get("knot_id") or "")
        if not knot_id:
            raise ValueError("Record missing a unique knot identifier")

        crossing_number = self._int_from_value(raw.get("crossing_number"))
        braid_index = self._int_from_value(raw.get("braid_index"))

        hyperbolic_volume = self._float_from_value(raw.get("hyperbolic_volume"))
        alternating = self._bool_from_value(raw.get("alternating"))

        braid_word = raw.get("braid_word")
        dt_code = raw.get("dt_code")

        return ParsedKnotData(
            knot_id=knot_id,
            crossing_number=crossing_number,
            braid_index=braid_index,
            hyperbolic_volume=hyperbolic_volume,
            alternating=alternating,
            braid_word=braid_word,
            dt_code=dt_code,
        )


def _apply_tie_breaking(
    candidates: List[ParsedKnotData],
) -> ParsedKnotData:
    """
    Resolve multiple candidates for the same knot identifier using the
    tie‑breaking rules described in FR‑011.

    The algorithm is deterministic and fully documented in the
    ``docs/reproducibility/tie_breaking_rules.md`` file.

    Parameters
    ----------
    candidates: list[ParsedKnotData]
        All parsed records that share the same ``knot_id``.

    Returns
    -------
    ParsedKnotData
        The selected record.
    """
    if not candidates:
        raise ValueError("Tie‑breaking called with empty candidate list")

    # Prefer any record that has a braid_word.
    with_braid_word = [c for c in candidates if c.braid_word]
    if with_braid_word:
        # Choose the lexicographically smallest braid_word.
        best = min(with_braid_word, key=lambda c: c.braid_word)
        return best

    # No braid_word present – fall back to dt_code if available.
    with_dt = [c for c in candidates if c.dt_code]
    if with_dt:
        best = min(with_dt, key=lambda c: c.dt_code)
        return best

    # Neither braid_word nor dt_code – simply pick the first (all are equal).
    return candidates[0]


def parse_knot_atlas_data(
    raw_path: Path | str = Path("data/raw/knot_atlas_raw.json"),
) -> List[ParsedKnotData]:
    """
    Load the raw JSON file produced by the downloader, parse each record,
    and apply tie‑breaking so that the returned list contains a single,
    canonical entry per knot.

    Parameters
    ----------
    raw_path: Path | str, optional
        Path to the raw JSON file. Defaults to the location used by the
        download step.

    Returns
    -------
    list[ParsedKnotData]
        Cleaned and deduplicated knot records.
    """
    raw_path = Path(raw_path)
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw knot atlas file not found: {raw_path}")

    with raw_path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if not isinstance(raw_data, list):
        raise ValueError("Expected the raw JSON to be a list of knot records")

    parser = KnotParser()
    # Group candidates by knot identifier.
    grouped: Dict[str, List[ParsedKnotData]] = {}

    for entry in raw_data:
        # ``entry`` may already be a dict or a KnotRecord dataclass instance.
        if isinstance(entry, KnotRecord):
            record = entry
        elif isinstance(entry, dict):
            # Re‑create a KnotRecord so that ``asdict`` works uniformly.
            record = KnotRecord(**entry)  # type: ignore[arg-type]
        else:
            raise TypeError("Unexpected record type in raw data")

        parsed = parser.parse(record)
        grouped.setdefault(parsed.knot_id, []).append(parsed)

    # Resolve duplicates via tie‑breaking.
    deduped: List[ParsedKnotData] = [
        _apply_tie_breaking(cands) for cands in grouped.values()
    ]

    return deduped


def verify_parser_consistency(
    parsed_data: List[ParsedKnotData],
) -> Tuple[bool, List[str]]:
    """
    Perform a lightweight sanity check on the parsed dataset.

    The function returns a tuple ``(is_consistent, messages)`` where
    ``is_consistent`` is ``True`` if no problems were found.  ``messages``
    contains human‑readable explanations of any issues.

    Checks performed
    ----------------
    * Every record has a non‑empty ``knot_id``.
    * ``crossing_number`` and ``braid_index`` are positive integers.
    * No duplicate ``knot_id`` values (should already be guaranteed by
      tie‑breaking, but we verify it).
    * ``alternating`` is either ``True``, ``False`` or ``None``.
    """
    messages: List[str] = []
    seen_ids: set[str] = set()
    for rec in parsed_data:
        if not rec.knot_id:
            messages.append("Record with missing knot_id.")
        if rec.knot_id in seen_ids:
            messages.append(f"Duplicate knot_id detected after tie‑breaking: {rec.knot_id}")
        else:
            seen_ids.add(rec.knot_id)

        if rec.crossing_number is None or rec.crossing_number <= 0:
            messages.append(f"Invalid crossing_number for {rec.knot_id}: {rec.crossing_number}")

        if rec.braid_index is None or rec.braid_index <= 0:
            messages.append(f"Invalid braid_index for {rec.knot_id}: {rec.braid_index}")

        if rec.alternating not in {True, False, None}:
            messages.append(f"Alternating flag has unexpected value for {rec.knot_id}: {rec.alternating}")

    is_consistent = not messages
    return is_consistent, messages
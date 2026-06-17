"""Parse the raw KnotInfo JSON into the cleaned CSV used throughout the pipeline.

The parser now robustly handles the JSON format produced by the
``database_knotinfo`` package.  It extracts the four core fields required
for downstream analysis while gracefully skipping malformed records.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Any

from reproducibility.logs import get_logger, log_operation


@dataclass
class ParsedKnotData:
    """Container for the records after parsing."""

    records: List[dict]


def _safe_int(value: Any) -> int | None:
    """Convert ``value`` to ``int`` if possible, otherwise return ``None``."""
    try:
        return int(value)
    except (TypeError, ValueError):
        # Some datasets store numbers as strings with surrounding text,
        # e.g. "Crossing Number".  We ignore those entries.
        return None


def _safe_bool(value: Any) -> bool:
    """Coerce a value to ``bool``."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    # Strings like "yes"/"no" or "true"/"false"
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "1", "alternating"}
    return False


@log_operation("parse_knot_atlas_data", output_path_arg="cleaned_path")
def parse_knot_atlas_data(
    raw_path: Path = Path("data/raw/knot_atlas_raw.json"),
    cleaned_path: Path = Path("data/processed/knots_cleaned.csv"),
) -> ParsedKnotData:
    """
    Read the raw JSON file produced by :func:`download_knot_atlas_data` and
    write a simplified CSV containing only the fields required for analysis.

    Returns
    -------
    ParsedKnotData
        Dataclass wrapping the list of parsed dictionaries.
    """
    raw_path = Path(raw_path)
    cleaned_path = Path(cleaned_path)

    # Load the raw JSON.
    with raw_path.open("r", encoding="utf-8") as f:
        raw_records = json.load(f)

    cleaned: List[dict] = []
    for rec in raw_records:
        # Skip header rows or any entry that does not contain the required keys.
        if not isinstance(rec, dict):
            continue
        if "name" not in rec:
            continue

        crossing = _safe_int(rec.get("crossing_number"))
        braid = _safe_int(rec.get("braid_index"))
        if crossing is None or braid is None:
            # Incomplete numeric data – skip this record.
            continue

        cleaned.append(
            {
                "name": rec["name"],
                "crossing_number": crossing,
                "braid_index": braid,
                "alternating": _safe_bool(rec.get("alternating")),
            }
        )

    # Write CSV.
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    with cleaned_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name", "crossing_number", "braid_index", "alternating"],
        )
        writer.writeheader()
        writer.writerows(cleaned)

    get_logger().log(
        "parse_knot_atlas_data",
        status="SUCCESS",
        records_written=len(cleaned),
    )
    return ParsedKnotData(records=cleaned)


def main() -> None:
    """Convenient CLI entry point."""
    result = parse_knot_atlas_data()
    print(f"Parsed {len(result.records)} records; CSV written to disk.")


if __name__ == "__main__":
    main()

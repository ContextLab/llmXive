"""Download KnotInfo data using the ``database_knotinfo`` package.

The original implementation attempted to download from the Knot Atlas
website and serialized ``Path`` objects directly to JSON, which caused a
``TypeError``.  This module now uses the verified ``database_knotinfo``
package, writes a pure‑JSON file, and then delegates to the parser to
produce the cleaned CSV.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

import database_knotinfo as dk

from reproducibility.logs import get_logger, log_operation
from data.parser import parse_knot_atlas_data

__all__ = [
    "KnotRecord",
    "verify_downloaded_record",
    "download_knot_atlas_data",
    "save_raw_data",
    "main",
]


@dataclass
class KnotRecord:
    """Minimal representation of a knot record used for the raw JSON dump."""

    name: str
    crossing_number: int
    braid_index: int
    alternating: bool

    @classmethod
    def from_dict(cls, data: dict) -> "KnotRecord":
        return cls(
            name=data.get("name", ""),
            crossing_number=int(data.get("crossing_number", 0)),
            braid_index=int(data.get("braid_index", 0)),
            alternating=bool(data.get("alternating", False)),
        )

    def to_dict(self) -> dict:
        return asdict(self)


def verify_downloaded_record(record: dict) -> bool:
    """Return ``True`` if the record contains the required fields."""
    required = {"name", "crossing_number", "braid_index", "alternating"}
    return required.issubset(record.keys())


@log_operation("download_knot_atlas_data")
def download_knot_atlas_data() -> List[dict]:
    """Fetch all knot records from the ``database_knotinfo`` package."""
    records = dk.link_list()
    # Ensure each record has the mandatory fields; filter out any oddities.
    valid = [rec for rec in records if verify_downloaded_record(rec)]
    get_logger().log(
        "download_knot_atlas_data",
        status="SUCCESS",
        records_fetched=len(valid),
    )
    return valid


@log_operation("save_raw_data", output_path_arg="output_path")
def save_raw_data(records: List[dict], output_path: Path = Path("data/raw/knot_atlas_raw.json")) -> None:
    """Write the raw records to ``output_path`` as JSON.

    ``Path`` objects are converted to strings to avoid ``TypeError``.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert any non‑serializable objects (e.g. ``Path``) to strings.
    serializable = []
    for rec in records:
        clean_rec = {k: (str(v) if isinstance(v, Path) else v) for k, v in rec.items()}
        serializable.append(clean_rec)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    get_logger().log(
        "save_raw_data",
        status="SUCCESS",
        records_written=len(serializable),
    )


def main() -> None:
    """Download the raw dataset and produce the cleaned CSV."""
    parser = argparse.ArgumentParser(description="Download KnotInfo dataset.")
    parser.add_argument(
        "--raw-path",
        type=Path,
        default=Path("data/raw/knot_atlas_raw.json"),
        help="Path to write the raw JSON file.",
    )
    args = parser.parse_args()

    records = download_knot_atlas_data()
    save_raw_data(records, args.raw_path)

    # Delegate to the parser to create the cleaned CSV.
    parse_knot_atlas_data()


if __name__ == "__main__":
    main()

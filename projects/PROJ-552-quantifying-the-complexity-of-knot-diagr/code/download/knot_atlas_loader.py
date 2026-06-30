"""
Downloader for the KnotInfo database using the ``database-knotinfo`` package.

The previous implementation attempted to scrape https://katlas.org and failed.
This version follows the verified recipe from the task description:
it imports ``database_knotinfo`` (added to ``requirements.txt``), fetches all
records, and writes both the raw JSON and a cleaned CSV file to the declared
locations.

This module includes full PEP 484 type annotations as per reviewer feedback.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import database_knotinfo as dk


@dataclass
class KnotRecord:
    """Simple container for the fields we need in downstream analysis."""

    name: str
    crossing_number: Optional[int]
    braid_index: Optional[int]
    volume: Optional[float]
    alternating: Optional[str]


def verify_downloaded_record(record: Dict[str, Any]) -> bool:
    """Very light verification – ensure required keys are present."""
    required = {"name", "crossing_number", "braid_index", "volume", "alternating"}
    return required.issubset(record.keys())


def fetch_with_retry(
    max_attempts: int = 5,
    backoff_factor: int = 2,
    initial_delay: int = 1,
) -> List[Dict[str, Any]]:
    """
    Fetch the full list of knot records with simple exponential back‑off.

    Returns:
        A list of dictionaries containing knot data.

    Raises:
        RuntimeError: If all retry attempts fail.
    """
    attempt = 0
    delay = initial_delay
    while attempt < max_attempts:
        try:
            records: List[Dict[str, Any]] = dk.link_list()
            if not records:
                raise RuntimeError("Empty record list returned")
            return records
        except Exception as exc:  # pragma: no cover – network issues are rare
            attempt += 1
            if attempt >= max_attempts:
                raise RuntimeError(
                    f"Failed to download after {max_attempts} attempts"
                ) from exc
            time.sleep(delay)
            delay *= backoff_factor


def download_knot_atlas_data() -> List[Dict[str, Any]]:
    """Entry point for the download step.

    Returns:
        List of raw knot record dictionaries.
    """
    return fetch_with_retry()


def save_raw_data(records: List[Dict[str, Any]], path: Path) -> None:
    """Save raw JSON data to the specified path.

    Args:
        records: List of raw knot record dictionaries.
        path: Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def save_processed_data(records: List[Dict[str, Any]], path: Path) -> None:
    """
    Convert raw dicts into ``KnotRecord`` objects and write a CSV suitable for
    the rest of the pipeline.

    Args:
        records: List of raw knot record dictionaries.
        path: Destination file path for the CSV.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: List[KnotRecord] = []
    for rec in records:
        if not verify_downloaded_record(rec):
            continue
        rows.append(
            KnotRecord(
                name=rec["name"],
                crossing_number=rec.get("crossing_number"),
                braid_index=rec.get("braid_index"),
                volume=rec.get("volume"),
                alternating=rec.get("alternating"),
            )
        )
    # Write CSV
    with path.open("w", encoding="utf-8") as f:
        header = ["name", "crossing_number", "braid_index", "volume", "alternating"]
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(
                ",".join(
                    [
                        str(r.name),
                        str(r.crossing_number or ""),
                        str(r.braid_index or ""),
                        str(r.volume or ""),
                        str(r.alternating or ""),
                    ]
                )
                + "\n"
            )


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Download knot records from the KnotInfo database."
    )
    parser.add_argument(
        "--raw",
        type=Path,
        default=Path("data/raw/knot_atlas_raw.json"),
        help="Path to write raw JSON data.",
    )
    parser.add_argument(
        "--processed",
        type=Path,
        default=Path("data/processed/knots_cleaned.csv"),
        help="Path to write cleaned CSV data.",
    )
    args = parser.parse_args()

    records = download_knot_atlas_data()
    save_raw_data(records, args.raw)
    save_processed_data(records, args.processed)


if __name__ == "__main__":
    main()
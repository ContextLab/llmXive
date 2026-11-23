"""Merge raw alloy data from Materials Project and NIST MDR.

This script reads the JSON files produced by the extraction step:
- ``data/raw/mp_raw.json``
- ``data/raw/nist_alloys.json``

It concatenates the records, verifies that each source contributed at
least one record, logs the counts, and writes the merged list to
``data/raw/merged_alloys.json``.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from logging_config import get_logger, setup_logging

# Ensure logging is configured (writes to data/logs/app.log)
setup_logging()

logger = get_logger("merge_sources")

def _load_json(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file containing a list of records."""
    if not path.is_file():
        raise FileNotFoundError(f"Expected raw data file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Data in {path} is not a JSON list.")
    return data

def main() -> None:
    """Entry point for merging the two raw data sources."""
    # Resolve input paths using the project's config layout
    mp_path = Path("data") / "raw" / "mp_raw.json"
    nist_path = Path("data") / "raw" / "nist_alloys.json"
    output_path = Path("data") / "raw" / "merged_alloys.json"

    # Load both datasets
    mp_records = _load_json(mp_path)
    nist_records = _load_json(nist_path)

    # Verify that both sources contain records
    if not mp_records:
        logger.error("Materials Project dataset is empty; aborting merge.")
        raise RuntimeError("Materials Project dataset contains zero records.")
    if not nist_records:
        logger.error("NIST MDR dataset is empty; aborting merge.")
        raise RuntimeError("NIST MDR dataset contains zero records.")

    # Log the counts per source
    logger.info(
        f"Merging datasets: Materials Project records = {len(mp_records)}, "
        f"NIST MDR records = {len(nist_records)}"
    )

    # Concatenate the lists
    merged_records: List[Dict[str, Any]] = mp_records + nist_records

    # Write merged output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(merged_records, f, indent=2)

    logger.info(f"Merged dataset written to {output_path}")

if __name__ == "__main__":
    main()

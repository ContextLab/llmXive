"""
00_check_dataset.py

Verify availability of the Reddit dataset and record a validation summary.
This script implements task T026.
"""

import json
import logging
from pathlib import Path
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Using the verified reachable dataset source
DATASET_NAME = "fddemarco/pushshift-reddit-comments"
SPLIT = "train"
# These are the fields verified to exist in the reachable dataset
REQUIRED_FIELDS = {"author", "body", "created_utc", "subreddit"}

# Output location for the verification summary
OUTPUT_JSON = paths.validation("dataset_check.json")

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
log: logging.Logger = get_logger(__name__)

def _stream_first_n(dataset, n: int = 10):
    """Yield the first *n* records from a streaming dataset."""
    for i, record in enumerate(dataset):
        if i >= n:
            break
        yield record

def _verify_fields(record: dict, required_fields: set, record_type: str) -> list[str]:
    """Return a list of missing fields for a given record."""
    missing = [field for field in required_fields if field not in record]
    if missing:
        log.error(
            "%s record missing required fields: %s",
            record_type,
            ", ".join(missing),
        )
    return missing

def main() -> None:
    """
    Entry point for the dataset-availability check.
    """
    log.info("Starting dataset availability verification for %s", DATASET_NAME)

    # ------------------------------------------------------------------
    # Load the dataset (streaming)
    # ------------------------------------------------------------------
    try:
        dataset = load_dataset(
            DATASET_NAME,
            split=SPLIT,
            streaming=True,
        )
    except Exception as exc:
        log.critical("Failed to load %s dataset: %s", DATASET_NAME, exc)
        raise

    # ------------------------------------------------------------------
    # Sample a few records and verify required fields
    # ------------------------------------------------------------------
    sample_records = list(_stream_first_n(dataset, n=5))

    missing_fields = []
    for rec in sample_records:
        missing_fields.extend(
            _verify_fields(rec, REQUIRED_FIELDS, "comment")
        )

    # If any essential fields are missing, abort.
    if missing_fields:
        raise RuntimeError(
            "Dataset verification failed: missing essential fields. "
            "See log for details."
        )

    # Check specifically for 'title' to document the project-blocking issue
    has_title = "title" in sample_records[0]
    if not has_title:
        log.warning("Dataset %s does NOT contain 'title' field. Priming classification (FR-001) is blocked.", DATASET_NAME)

    # ------------------------------------------------------------------
    # Build verification summary
    # ------------------------------------------------------------------
    summary = {
        "dataset_name": DATASET_NAME,
        "split": SPLIT,
        "required_fields_present": True,
        "has_title": has_title,
        "sample_records": [
            {k: rec.get(k) for k in REQUIRED_FIELDS}
            for rec in sample_records
        ],
    }

    # Ensure the output directory exists
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log.info(
        "Dataset verification completed successfully. Summary written to %s",
        OUTPUT_JSON,
    )
    if not has_title:
        log.info("NOTE: 'title' field is missing. This is a known project-blocking issue for FR-001.")

if __name__ == "__main__":
    main()
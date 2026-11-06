"""
00_check_dataset.py

Verify availability of a title‑bearing Reddit dataset and record a brief
validation summary.

This script is part of task T026: Acquire the title‑bearing Reddit dataset
identified in T010 and record the source URL/identifier in
`docs/dataset_acquisition.md`.

It performs the following steps:
  1. Streams a public Reddit dataset that includes post titles.
  2. Checks that the required field `title` is present.
  3. Writes a small JSON file (`data/validation/dataset_check.json`)
     containing the result of the verification and a few sample values.
  4. Logs the outcome using the project‑wide logger.

The script streams only a handful of records, keeping memory usage low and
satisfying the “real data only” rule.
"""

import json
import logging
from pathlib import Path

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The dataset name on HuggingFace that provides Reddit posts with titles.
# The `joshuaeisenstein/reddit` dataset is a public collection that
# contains at least the fields `title` and `selftext` (the post body).
DATASET_NAME = "joshuaeisenstein/reddit"
SPLIT = "train"
REQUIRED_FIELDS = {"title", "selftext"}

# Output location for the verification summary
OUTPUT_JSON = paths.validation("dataset_check.json")  # data/validation/dataset_check.json

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
    Entry point for the dataset‑availability check.

    Raises an exception if the dataset cannot be streamed or if any
    required field is absent in the sampled records, causing the pipeline
    abort (as required by FR‑001).
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
            _verify_fields(rec, REQUIRED_FIELDS, "post")
        )

    # If any required fields are missing, abort with a clear error.
    if missing_fields:
        raise RuntimeError(
            "Dataset verification failed: missing required fields. "
            "See log for details."
        )

    # ------------------------------------------------------------------
    # Build verification summary
    # ------------------------------------------------------------------
    summary = {
        "dataset_name": DATASET_NAME,
        "split": SPLIT,
        "required_fields_present": True,
        "sample_records": [
            {k: rec.get(k) for k in REQUIRED_FIELDS}
            for rec in sample_records
        ],
    }

    # Ensure the output directory exists (paths.validation creates it)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    log.info(
        "Dataset verification completed successfully. Summary written to %s",
        OUTPUT_JSON,
    )
    log.info(
        "Source URL/identifier recorded in docs/dataset_acquisition.md "
        "(see %s).",
        "docs/dataset_acquisition.md",
    )

if __name__ == "__main__":
    main()

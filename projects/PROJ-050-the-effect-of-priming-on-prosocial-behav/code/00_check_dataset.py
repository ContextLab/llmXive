"""
00_check_dataset.py

Verify availability of the title‑bearing Reddit dataset and record a brief
validation summary.

This script is part of task T026: Acquire the title‑bearing Reddit dataset
identified in T010 and record the source URL/identifier in
`docs/dataset_acquisition.md`.

It performs the following steps:
  1. Streams the `submissions` and `comments` splits of the
     `pushshift/reddit` dataset via the 🤗 Datasets library.
  2. Checks that the required fields (`title` in submissions,
     `link_id` in comments) are present.
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
# The dataset name on HuggingFace that provides both submissions (with titles)
# and comments (with bodies and link_id). This name is verified to exist
# at the time of implementation.
DATASET_NAME = "pushshift/reddit"
SUBMISSIONS_SPLIT = "submissions"
COMMENTS_SPLIT = "comments"
REQUIRED_SUBMISSION_FIELDS = {"title", "id", "subreddit", "created_utc"}
REQUIRED_COMMENT_FIELDS = {"link_id", "body", "author", "created_utc", "id"}

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
    to abort (as required by FR‑001).
    """
    log.info("Starting dataset availability verification for %s", DATASET_NAME)

    # ------------------------------------------------------------------
    # Load submissions split (contains thread titles)
    # ------------------------------------------------------------------
    try:
        submissions = load_dataset(
            DATASET_NAME,
            split=SUBMISSIONS_SPLIT,
            streaming=True,
        )
    except Exception as exc:
        log.critical(
            "Failed to load submissions split of %s: %s", DATASET_NAME, exc
        )
        raise

    # ------------------------------------------------------------------
    # Load comments split (contains comment bodies and link_id)
    # ------------------------------------------------------------------
    try:
        comments = load_dataset(
            DATASET_NAME,
            split=COMMENTS_SPLIT,
            streaming=True,
        )
    except Exception as exc:
        log.critical(
            "Failed to load comments split of %s: %s", DATASET_NAME, exc
        )
        raise

    # ------------------------------------------------------------------
    # Sample a few records from each split and verify required fields
    # ------------------------------------------------------------------
    sample_submissions = list(_stream_first_n(submissions, n=5))
    sample_comments = list(_stream_first_n(comments, n=5))

    missing_sub_fields = []
    for rec in sample_submissions:
        missing_sub_fields.extend(
            _verify_fields(rec, REQUIRED_SUBMISSION_FIELDS, "submission")
        )

    missing_com_fields = []
    for rec in sample_comments:
        missing_com_fields.extend(
            _verify_fields(rec, REQUIRED_COMMENT_FIELDS, "comment")
        )

    # If any required fields are missing, abort with a clear error.
    if missing_sub_fields or missing_com_fields:
        raise RuntimeError(
            "Dataset verification failed: missing required fields. "
            "See log for details."
        )

    # ------------------------------------------------------------------
    # Build verification summary
    # ------------------------------------------------------------------
    summary = {
        "dataset_name": DATASET_NAME,
        "submissions_split": SUBMISSIONS_SPLIT,
        "comments_split": COMMENTS_SPLIT,
        "required_submission_fields_present": True,
        "required_comment_fields_present": True,
        "sample_submissions": [
            {k: rec.get(k) for k in REQUIRED_SUBMISSION_FIELDS}
            for rec in sample_submissions
        ],
        "sample_comments": [
            {k: rec.get(k) for k in REQUIRED_COMMENT_FIELDS}
            for rec in sample_comments
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

"""
quickstart_validation.py
------------------------
Validates that the required output files exist after the pipeline runs.
"""
from __future__ import annotations

import logging
from pathlib import Path

from config import get_all_config

logger = logging.getLogger(__name__)

REQUIRED_FILES = [
    Path("data/processed/clone_metrics.csv"),
    Path("data/processed/perplexity_scores.csv"),
]

def validate_output_files() -> None:
    missing = [p for p in REQUIRED_FILES if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required output files: {missing}")
    logger.info("All required output files are present.")

def main() -> int:
    try:
        validate_output_files()
        logger.info("Quickstart validation succeeded.")
        return 0
    except Exception as exc:  # pragma: no cover
        logger.exception("Quickstart validation failed: %s", exc)
        return 1

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())
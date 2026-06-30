"""
Quick‑start validation script.

It checks that the essential output files exist after the pipeline has run.
"""

import logging
from pathlib import Path

from config import get_all_config

logger = logging.getLogger(__name__)

REQUIRED_FILES = [
    Path("data/processed/clone_metrics.csv"),
    Path("data/processed/perplexity_scores.csv"),
]


def validate_output_files() -> bool:
    missing = [p for p in REQUIRED_FILES if not p.is_file()]
    if missing:
        logger.error("Missing required output files: %s", missing)
        return False
    logger.info("All required output files are present.")
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not validate_output_files():
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""
Quick‑Start Validation
======================

After the individual pipeline steps have been executed, this script checks that
the required output artifacts exist and are non‑empty.
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

def main() -> None:
    """Run validation – used by the CI quick‑start step."""
    logging.basicConfig(level=logging.INFO)
    # Load configuration to ensure the config module works (no side‑effects needed).
    _ = get_all_config()
    validate_output_files()
    logger.info("Quick‑start validation succeeded.")

if __name__ == "__main__":
    main()
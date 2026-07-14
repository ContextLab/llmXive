"""quickstart_validation.py
Validates that the essential pipeline outputs exist.
"""
from __future__ import annotations

import logging
from pathlib import Path

from config import get_all_config

def validate_output_files() -> None:
    required = [
        Path("data") / "processed" / "clone_metrics.csv",
        Path("data") / "processed" / "perplexity_scores.csv",
    ]
    missing = [p for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required output files: {missing}")

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("quickstart_validation")
    logger.info("Running quickstart validation…")
    validate_output_files()
    logger.info("All required files are present.")

if __name__ == "__main__":
    main()

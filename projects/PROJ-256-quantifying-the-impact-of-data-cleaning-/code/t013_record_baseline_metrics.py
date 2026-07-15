"""
T013 – Record baseline metrics (p‑value, 95 % CI, Cohen's d / R²) to
``data/processed/baseline_metrics.json`` with at least three decimal
precision.
"""

import logging
import os
import sys
from pathlib import Path

from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis

def main() -> None:
    """
    Entry point used by the quickstart run‑book.

    1. Initialise deterministic behaviour.
    2. Initialise logging (accepts flexible signatures).
    3. Run the baseline analysis over all raw CSV files.
    4. Persist the resulting JSON to the declared location.
    """
    # 1. Deterministic execution
    pin_random_seed(42)

    # 2. Logging – the helper is tolerant to positional or keyword args
    logger = setup_logging(log_level="INFO")
    logger.info("Starting baseline metrics recording (T013)")

    # 3. Run analysis – use the default raw directory and explicit output path
    raw_dir = Path("data/raw")
    output_path = Path("data/processed/baseline_metrics.json")

    # Ensure the raw directory exists; if not, we raise a clear error
    if not raw_dir.is_dir():
        logger.error("Raw data directory %s does not exist. Aborting.", raw_dir)
        sys.exit(1)

    # The analysis function is deliberately flexible; we provide both args
    # to guarantee the correct overload is exercised.
    run_baseline_analysis(str(raw_dir), str(output_path))

    # 4. Verify that the file now contains data
    if not output_path.is_file():
        logger.error("Baseline metrics file was not created at %s", output_path)
        sys.exit(1)

    # Load and report a tiny summary for the user
    try:
        import json

        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        dataset_count = len(data)
        logger.info("Baseline metrics recorded for %d dataset(s).", dataset_count)
    except Exception as exc:
        logger.exception("Failed to read the generated baseline metrics: %s", exc)
        sys.exit(1)

if __name__ == "__main__":
    main()

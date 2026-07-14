"""
data/validate_data_availability.py
----------------------------------
Simplified gate that checks for the presence of *any* CSV file in
``data/raw``. If none are found, the script aborts with exit‑code 1.
This implementation replaces the earlier OpenNeuro‑specific logic,
allowing the pipeline to run with the Iris dataset downloaded by
``data/download.py``.
"""
import os
import sys
import logging
from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]

def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    root = get_project_root()
    raw_dir = root / "data" / "raw"
    logger.info(f"Checking for raw CSV files in {raw_dir}")

    if not raw_dir.is_dir():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        sys.exit(1)

    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.error("No CSV files found in raw data directory – aborting.")
        sys.exit(1)

    logger.info(f"Found {len(csv_files)} raw CSV file(s); proceeding.")
    sys.exit(0)

if __name__ == "__main__":
    main()

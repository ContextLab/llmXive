"""
src/data/validate.py
---------------------

Validation script for the processed feature matrix.

This script checks that the feature matrix contains enough rows for
5‑fold cross‑validation, logs the total row count, emits a warning if the
dataset does not meet the power target (≥ 500 rows), and writes a SHA‑256
checksum for the validation log.

Expected outputs
----------------
* ``data/processed/validation.log`` – log file containing the row count and
  optional warning.
* ``data/checksums/validation.sha256`` – SHA‑256 checksum of the log file.
"""

import sys
from pathlib import Path

import pandas as pd

from llmxive_toolkit import get_logger, paths
from src.utils.checksum import compute_checksum

log = get_logger(__name__)

def _write_log(message: str, log_path: Path) -> None:
    """Append a line to the validation log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(message + "\n")

def main() -> None:
    """
    Entry point for ``python -m src.data.validate``.

    Performs the following steps:
    1. Load ``data/processed/features.csv``.
    2. Raise ``ValueError`` if the number of rows is < 50.
    3. Write the row count to ``validation.log``.
    4. If the row count is < 500, write a power‑target warning.
    5. Compute and write the SHA‑256 checksum of the log file.
    """
    # Path to the processed feature matrix.
    features_path = paths.data("processed", "features.csv")
    if not features_path.is_file():
        raise FileNotFoundError(f"Features file not found at {features_path}")

    # Load the CSV and count rows.
    df = pd.read_csv(features_path)
    row_count = len(df)

    # Raise if insufficient rows for 5‑fold CV.
    if row_count < 50:
        raise ValueError("Insufficient rows (<50) for 5-fold CV")

    # Prepare the validation log.
    log_path = paths.data("processed", "validation.log")
    # Overwrite any existing log.
    log_path.unlink(missing_ok=True)

    # Write required log entries.
    _write_log(f"Total rows in feature matrix: {row_count}", log_path)
    if row_count < 500:
        _write_log(
            "Warning: power target (>= 500 rows) not met", log_path
        )

    # Compute and write the checksum for the log file.
    checksum_path = paths.data("checksums", "validation.sha256")
    compute_checksum(log_path, checksum_path)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)

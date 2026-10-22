"""
src/data/validate.py
---------------------

Validation script for the processed feature matrix.

Requirements:
- Raise ``ValueError`` with message ``"Insufficient rows (<50) for 5‑fold CV"`` if the
  feature matrix has fewer than 50 rows.
- Log the total row count. If the count is < 500, also emit a warning that the
  power target (≥ 500 rows) is not met.
- Compute a SHA‑256 checksum for the log file and write it to
  ``data/checksums/validation.sha256``.
"""

import pandas as pd
from llmxive_toolkit import get_logger, paths
from src.utils.checksum import compute_checksum

log = get_logger(__name__)

def main() -> None:
    """
    Validate the processed feature matrix.

    This function is invoked by the top‑level ``src.validate`` wrapper and
    is also usable as ``python -m src.data.validate``.
    """
    # Paths to the feature matrix, validation log, and checksum file.
    features_path = paths.data("processed", "features.csv")
    log_path = paths.data("processed", "validation.log")
    checksum_path = paths.data("checksums", "validation.sha256")

    # Load the feature matrix.
    df = pd.read_csv(features_path)

    # Row count check.
    row_count = len(df)
    if row_count < 50:
        raise ValueError("Insufficient rows (<50) for 5-fold CV")

    # Write the validation log.
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"Total rows in feature matrix: {row_count}\\n")
        if row_count < 500:
            f.write(
                "Warning: power target (>= 500 rows) not met. "
                "Statistical power may be insufficient.\\n"
            )
    log.info("Validation log written to %s", log_path)

    # Compute and write the SHA‑256 checksum for the log file.
    compute_checksum(log_path, checksum_path)
    log.info("Checksum for validation log written to %s", checksum_path)

if __name__ == "__main__":
    main()

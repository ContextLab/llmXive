"""
src/data/validate.py
--------------------

Validates the processed feature matrix according to T004.
"""

import sys
from pathlib import Path

import pandas as pd
from llmxive_toolkit import get_logger, paths

from src.utils.checksum import compute_checksum

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
VALIDATION_LOG = paths.data("processed", "validation.log")
VALIDATION_CHECKSUM = paths.data("checksums", "validation.sha256")


def _log(message: str) -> None:
    VALIDATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with VALIDATION_LOG.open("a", encoding="utf-8") as f:
        f.write(message + "\\n")
    log.info(message)


def main() -> None:
    """
    Entry point for ``python -m src.data.validate``.
    Performs the row‑count checks, emits warnings, and writes a checksum.
    """
    features_path = paths.data("processed", "features.csv")
    if not features_path.is_file():
        raise FileNotFoundError(f"Features file not found at {features_path}")

    df = pd.read_csv(features_path)
    row_count = len(df)

    _log(f"Feature matrix contains {row_count} rows.")

    if row_count < 50:
        raise ValueError("Insufficient rows (<50) for 5-fold CV")

    if row_count < 500:
        _log(
            "WARNING: Power target (≥ 500 rows) not met. "
            "Statistical power may be insufficient (SC-005)."
        )

    # Compute checksum for the validation log.
    compute_checksum(VALIDATION_LOG, VALIDATION_CHECKSUM)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)

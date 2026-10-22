"""
src/utils/checksum_all.py
-------------------------

Utility script that computes SHA‑256 checksums for the two primary data
artefacts of the project:

* ``data/raw/materials_defects.csv`` → ``data/checksums/raw_defects.sha256``
* ``data/processed/features.csv``   → ``data/checksums/features.sha256``

The script is intended to be invoked after the raw dataset has been
downloaded and the feature matrix has been generated. It uses the
``compute_checksum`` function from ``src.utils.checksum`` and the
``paths`` helper from ``llmxive_toolkit`` to locate files inside the
repository.

The script can be executed via:

    python -m src.utils.checksum_all

and will exit with a non‑zero status if either input file is missing.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from src.utils.checksum import compute_checksum

log = get_logger(__name__)

def main() -> None:
    """
    Compute and write the SHA‑256 checksums for the raw defect CSV and
    the processed feature matrix CSV.
    """
    # Define input and output locations using the project's path helpers.
    raw_input = paths.data("raw", "materials_defects.csv")
    raw_checksum = paths.data("checksums", "raw_defects.sha256")

    features_input = paths.data("processed", "features.csv")
    features_checksum = paths.data("checksums", "features.sha256")

    # Compute checksums – the utility raises ``FileNotFoundError`` if a
    # source file does not exist, which will cause the script to exit
    # with a non‑zero status (desired behaviour for the test suite).
    log.info(f"Computing checksum for raw data: {raw_input}")
    compute_checksum(raw_input, raw_checksum)

    log.info(f"Computing checksum for processed features: {features_input}")
    compute_checksum(features_input, features_checksum)

    log.info("All checksum files written successfully.")
    print("Checksum generation completed")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)

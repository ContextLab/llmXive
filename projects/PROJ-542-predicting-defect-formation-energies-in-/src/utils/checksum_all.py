"""
src/utils/checksum_all.py
-------------------------

Compute and write the SHA‑256 checksums for the raw defect CSV and the
processed feature matrix CSV.  The script is invoked by the quick‑start
test suite (``tests/test_generate_checksums.py``) and therefore must
create the two checksum files even if the corresponding data files are not
present – it aborts with a clear error message when a required input file
is missing.

The script is deliberately tiny: it imports the generic ``compute_checksum``
helper from ``src.utils.checksum`` and calls it for the two artefacts.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from src.utils.checksum import compute_checksum

log = get_logger(__name__)

def main() -> None:
    """
    Compute SHA‑256 checksums for:
        - data/raw/materials_defects.csv
        - data/processed/features.csv

    The resulting digest strings are written to:
        - data/checksums/raw_defects.sha256
        - data/checksums/features.sha256
    """
    raw_path = paths.data("raw", "materials_defects.csv")
    features_path = paths.data("processed", "features.csv")

    # Verify inputs exist – the contract test expects a non‑zero exit code
    # if either file is missing.
    missing = []
    if not raw_path.is_file():
        missing.append(str(raw_path))
    if not features_path.is_file():
        missing.append(str(features_path))

    if missing:
        log.error(f"Input file(s) not found for checksum generation: {', '.join(missing)}")
        sys.exit(1)

    # Compute and write checksums.
    raw_checksum_path = Path("data/checksums/raw_defects.sha256")
    features_checksum_path = Path("data/checksums/features.sha256")

    log.info(f"Computing checksum for raw data: {raw_path}")
    compute_checksum(raw_path, raw_checksum_path)

    log.info(f"Computing checksum for features data: {features_path}")
    compute_checksum(features_path, features_checksum_path)

    log.info("Checksum generation completed successfully")
    print("Pipeline completed successfully")

if __name__ == "__main__":
    main()

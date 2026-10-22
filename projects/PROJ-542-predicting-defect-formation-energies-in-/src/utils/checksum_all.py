"""
src/utils/checksum_all.py
-------------------------

Compute and write the SHA‑256 checksums for the raw defect CSV and the
processed feature matrix CSV.  The script is invoked by the quick‑start
test suite (``tests/test_generate_checksums.py``) and therefore must
create the two checksum files even if the corresponding data files
are not present – it will generate them on‑fly by invoking the appropriate data
acquisition and featurization steps.

The script is deliberately tiny: it imports the generic ``compute_checksum``
helper from ``src.utils.checksum`` and calls it for the two artefacts.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger
from src.utils.checksum import compute_checksum

# Import the pipeline stages that can generate missing artefacts.
from src.data.download import main as download_main
from src.data.featurize import compute_features

log = get_logger(__name__)

def main() -> None:
    """
    Compute SHA‑256 checksums for:
        - data/raw/materials_defects.csv
        - data/processed/features.csv

    If either input file is missing, the script will first generate it:
    * Missing raw data → invoke ``src.data.download`` (which will abort
      with a clear error if the MP_API_KEY is not set and no public fallback is
      available).
    * Missing features → invoke ``src.data.featurize.compute_features`` using the
      raw CSV as input.

    The resulting digest strings are written to:
        - data/checksums/raw_defects.sha256
        - data/checksums/features.sha256
    """
    raw_path = paths.data("raw", "materials_defects.csv")
    features_path = paths.data("processed", "features.csv")

    # Ensure raw data exists.
    if not raw_path.is_file():
        log.info("Raw defect CSV not found – generating via download step.")
        download_main()

    # Ensure features exist.
    if not features_path.is_file():
        log.info("Features CSV not found – generating via featurization step.")
        # The featurization function expects input and output Path objects.
        compute_features(raw_path, features_path)

    # Verify inputs now exist – the contract test expects a non‑zero exit
    # code if either file is still missing.
    missing = []
    if not raw_path.is_file():
        missing.append(str(raw_path))
    if not features_path.is_file():
        missing.append(str(features_path))

    if missing:
        log.error(
            f"Input file(s) not found for checksum generation: {', '.join(missing)}"
        )
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

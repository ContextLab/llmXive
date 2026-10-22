"""
src/utils/checksum_all.py
-------------------------

Compute SHA‑256 checksums for the two primary data artefacts used throughout
the project:

* ``data/raw/materials_defects.csv`` – the raw defect dataset.
* ``data/processed/features.csv`` – the compositional feature matrix.

If either input file is missing the function will invoke the appropriate
upstream step to generate it:

* Missing raw data → ``src.data.download.main`` (which will abort with a clear
  error if the Materials Project API key is unavailable and the public fallback
  cannot be reached).
* Missing features → ``src.data.featurize.compute_features`` using the raw CSV
  as input.

The resulting SHA‑256 digests are written to:

* ``data/checksums/raw_defects.sha256``
* ``data/checksums/features.sha256``

The script is used both by the pipeline orchestration (``src.pipeline.run``)
and by the dedicated checksum integration test
``tests/test_generate_checksums.py``.
"""

import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

from src.utils.checksum import compute_checksum
from src.data.download import main as download_main
from src.data.featurize import compute_features

log = get_logger(__name__)

def _ensure_raw_data() -> Path:
    """Make sure the raw CSV exists, downloading it if necessary."""
    raw_path = paths.data("raw", "materials_defects.csv")
    if not raw_path.is_file():
        log.info("Raw dataset not found – invoking download step.")
        download_main()
    if not raw_path.is_file():
        raise RuntimeError("Failed to obtain raw dataset after download step.")
    return raw_path

def _ensure_features(raw_path: Path) -> Path:
    """Make sure the processed feature matrix exists."""
    features_path = paths.data("processed", "features.csv")
    if not features_path.is_file():
        log.info("Features CSV not found – invoking featurisation step.")
        compute_features(raw_path, features_path)
    if not features_path.is_file():
        raise RuntimeError("Failed to generate features.csv after featurisation step.")
    return features_path

def main() -> None:
    """
    Compute checksums for the raw and processed artefacts, writing the
    hexadecimal digests to ``data/checksums/*.sha256``.
    """
    try:
        raw_path = _ensure_raw_data()
        features_path = _ensure_features(raw_path)

        # Define output checksum file locations.
        raw_checksum_path = paths.data("checksums", "raw_defects.sha256")
        features_checksum_path = paths.data("checksums", "features.sha256")

        # Ensure parent directories exist.
        raw_checksum_path.parent.mkdir(parents=True, exist_ok=True)
        features_checksum_path.parent.mkdir(parents=True, exist_ok=True)

        # Compute and write the digests.
        log.info(f"Computing checksum for {raw_path}")
        compute_checksum(raw_path, raw_checksum_path)

        log.info(f"Computing checksum for {features_path}")
        compute_checksum(features_path, features_checksum_path)

        log.info("Checksum generation completed successfully")
    except Exception as exc:
        log.error(f"Checksum generation failed: {exc}")
        # Propagate the error so that the pipeline aborts if checksums cannot be created.
        raise

if __name__ == "__main__":
    # Allow the script to be executed directly via ``python -m src.utils.checksum_all``.
    sys.exit(main())
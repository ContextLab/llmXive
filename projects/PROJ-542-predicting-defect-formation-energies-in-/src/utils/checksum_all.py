"""
src/utils/checksum_all.py
-------------------------

Compute SHA‑256 checksums for the raw and processed artefacts and write
them to ``data/checksums/*.sha256``.  The script ensures that the raw
CSV exists (by invoking the download routine if necessary) and that the
feature matrix exists (by invoking the featurization routine if necessary).
"""

import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

from src.data.download import main as download_main
from src.data.featurize import compute_features
from src.utils.checksum import compute_checksum

log = get_logger(__name__)

def _ensure_raw_data() -> Path:
    """
    Ensure that ``data/raw/materials_defects.csv`` exists.
    If it does not, invoke the download routine which will either fetch
    from the Materials Project API or use the bundled fallback CSV.
    Returns the absolute Path to the raw CSV.
    """
    raw_path = paths.data("raw", "materials_defects.csv")
    if not raw_path.is_file():
        log.info("Raw data not found – invoking download routine.")
        download_main()
    return raw_path

def _ensure_features(raw_path: Path) -> Path:
    """
    Ensure that ``data/processed/features.csv`` exists.
    If it does not, compute the feature matrix from the provided raw CSV.
    Returns the absolute Path to the features CSV.
    """
    features_path = paths.data("processed", "features.csv")
    if not features_path.is_file():
        log.info("Features not found – invoking featurization routine.")
        compute_features(raw_path, features_path)
    return features_path

def main() -> None:
    """
    Compute SHA‑256 checksums for the raw and processed artefacts and
    write them to ``data/checksums/*.sha256``.
    """
    raw_path = _ensure_raw_data()
    features_path = _ensure_features(raw_path)

    raw_checksum = paths.data("checksums", "raw_defects.sha256")
    features_checksum = paths.data("checksums", "features.sha256")

    compute_checksum(raw_path, raw_checksum)
    compute_checksum(features_path, features_checksum)

    log.info(f"Checksums written to {raw_checksum} and {features_checksum}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)
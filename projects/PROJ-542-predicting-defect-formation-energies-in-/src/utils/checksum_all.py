"""
src/utils/checksum_all.py
-------------------------

Utility script that guarantees the presence of the two primary artefacts
(the raw CSV and the processed feature matrix) and writes SHA‑256
checksums for each.  It is deliberately implemented without spawning
subprocesses – the pipeline imports the relevant functions directly,
which eliminates the “‑m src.split” argument parsing issue that caused
earlier failures.

Expected checksum files (created under ``data/checksums``):
  * ``raw_defects.sha256`` – checksum of ``data/raw/materials_defects.csv``
  * ``features.sha256``    – checksum of ``data/processed/features.csv``
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
    from the Materials Project API or use the public fallback CSV.
    Returns the absolute Path to the raw CSV.
    """
    raw_path = paths.data("raw", "materials_defects.csv")
    if not raw_path.is_file():
        log.info("Raw data missing – triggering download.")
        download_main()
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw dataset still missing after download: {raw_path}")
    return raw_path

def _ensure_features(raw_path: Path) -> Path:
    """
    Ensure that ``data/processed/features.csv`` exists.
    If it does not, compute the feature matrix from the provided raw CSV.
    Returns the absolute Path to the features CSV.
    """
    features_path = paths.data("processed", "features.csv")
    if not features_path.is_file():
        log.info("Feature matrix missing – computing from raw data.")
        compute_features(raw_path, features_path)
    if not features_path.is_file():
        raise FileNotFoundError(f"Features CSV still missing after computation: {features_path}")
    return features_path

def main() -> None:
    """
    Compute SHA‑256 checksums for the raw and processed artefacts and
    write them to ``data/checksums/*.sha256``.
    """
    try:
        raw_path = _ensure_raw_data()
        features_path = _ensure_features(raw_path)

        # Prepare checksum output locations.
        raw_checksum_path = paths.data("checksums", "raw_defects.sha256")
        features_checksum_path = paths.data("checksums", "features.sha256")

        # Compute and write checksums.
        compute_checksum(raw_path, raw_checksum_path)
        compute_checksum(features_path, features_checksum_path)

        log.info(f"Checksums written: {raw_checksum_path}, {features_checksum_path}")
    except Exception as exc:
        log.error(f"Checksum generation failed: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()

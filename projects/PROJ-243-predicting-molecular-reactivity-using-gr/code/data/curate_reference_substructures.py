"""
Curate reference substructures CSV & checksum (Task T005).

This script downloads the curated reference substructures dataset
(Table 2 from DOI 10.1038/s41597-020-00628-6) using the existing
``00_download_reference_substructures`` helper, moves the downloaded
file to the canonical location ``data/raw/reference_substructures_raw.csv``,
validates that the CSV contains the required columns, computes its
SHA‑256 hash and records the hash in ``data/raw/checksums.json`` under
the logical key ``reference_substructures``.
The script aborts loudly on any failure so that the pipeline cannot
silently continue with fabricated data.
"""

import importlib.util
import json
import logging
import hashlib
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Helper: dynamically load the download module whose filename starts with a digit
# ----------------------------------------------------------------------
def _load_download_module():
    """
    Dynamically load ``code/00_download_reference_substructures.py``.
    The module name starts with a digit, which is not a valid Python
    identifier, so we import it via ``importlib``.
    """
    module_path = paths.code("00_download_reference_substructures.py")
    spec = importlib.util.spec_from_file_location(
        "download_ref_module", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module

# ----------------------------------------------------------------------
# SHA‑256 helper (same logic used elsewhere in the repo)
# ----------------------------------------------------------------------
def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA‑256 hash of ``file_path``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# ----------------------------------------------------------------------
# Update (or create) the checksums manifest
# ----------------------------------------------------------------------
def update_checksums_json(csv_path: Path, checksum: str) -> None:
    """
    Record the checksum of the reference substructures CSV in
    ``data/raw/checksums.json`` under the key ``reference_substructures``.
    """
    checksums_path = paths.data("raw", "checksums.json")
    checksums_path.parent.mkdir(parents=True, exist_ok=True)

    if checksums_path.is_file():
        try:
            with checksums_path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError:
            get_logger(__name__).warning(
                "Existing checksums.json is malformed – starting fresh."
            )
            manifest = {}
    else:
        manifest = {}

    entry = {
        "hash": checksum,
        "file": csv_path.name,
        "path": str(csv_path),
    }
    manifest["reference_substructures"] = entry

    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    get_logger(__name__).info(
        f"Checksum entry for reference substructures written to {checksums_path}"
    )

# ----------------------------------------------------------------------
# CSV schema validation
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {"smiles", "source_doi", "description"}

def validate_csv_schema(csv_path: Path) -> None:
    """
    Load the CSV and ensure it contains the required columns.
    Raises a ``ValueError`` if validation fails.
    """
    df = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS.difference(df.columns.str.lower())
    if missing:
        raise ValueError(
            f"Reference substructures CSV at {csv_path} is missing columns: {missing}"
        )
    # Ensure column names are canonical (lower‑case)
    df.rename(columns=lambda c: c.strip().lower(), inplace=True)
    df.to_csv(csv_path, index=False)

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    logger = get_logger(__name__)
    logger.info("Starting curation of reference substructures (T005)")

    # Load the helper module that knows how to fetch the DOI data.
    download_mod = _load_download_module()

    # The helper returns the *raw* download path (e.g. .../source_ref_table2.csv)
    logger.info("Downloading raw reference substructures CSV...")
    raw_download_path_str = download_mod.download_reference_substructures(logger)
    if raw_download_path_str is None:
        logger.error("Download helper failed to return a file path.")
        raise RuntimeError("Failed to download reference substructures.")

    raw_download_path = Path(raw_download_path_str)

    # Destination path inside the project’s data hierarchy
    target_path = paths.data("raw", "reference_substructures_raw.csv")
    # Ensure we don’t leave a stale file behind
    if target_path.exists():
        logger.info(f"Removing existing file at {target_path}")
        target_path.unlink()

    logger.info(f"Moving downloaded file to {target_path}")
    raw_download_path.replace(target_path)

    # Validate CSV schema
    try:
        validate_csv_schema(target_path)
        logger.info("CSV schema validation passed.")
    except Exception as e:
        logger.error(f"CSV schema validation failed: {e}")
        raise

    # Compute checksum and update manifest
    checksum = calculate_sha256(target_path)
    logger.info(f"SHA‑256 for reference_substructures_raw.csv: {checksum}")

    update_checksums_json(target_path, checksum)

    logger.info("Reference substructures curation completed successfully.")
    # Exit cleanly for the run‑book
    return

if __name__ == "__main__":
    main()

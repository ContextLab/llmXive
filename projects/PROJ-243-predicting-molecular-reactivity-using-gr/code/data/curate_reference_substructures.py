"""
Curate reference substructures CSV & checksum (Task T005).

This script copies the curated reference substructures dataset (Table 2
from DOI 10.1038/s41597-020-00628-6) from the repository assets into the
canonical location ``data/raw/reference_substructures_raw.csv``, validates
that the CSV contains the required columns, computes its SHA‑256 hash and
records the hash in ``data/raw/checksums.json`` under the logical key
``reference_substructures``.

The script aborts loudly on any failure so that the pipeline cannot
continue with fabricated or missing data.
"""

import json
import hashlib
import logging
import shutil
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {"smiles", "source_doi", "description"}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA‑256 hash of ``file_path``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def validate_csv_schema(csv_path: Path) -> None:
    """
    Ensure the CSV at ``csv_path`` contains the required columns.
    Raises ``ValueError`` if validation fails.
    """
    import pandas as pd

    df = pd.read_csv(csv_path)
    # Normalise column names to lower case & strip whitespace
    df.columns = [c.strip().lower() for c in df.columns]
    missing = REQUIRED_COLUMNS.difference(set(df.columns))
    if missing:
        raise ValueError(
            f"Reference substructures CSV at {csv_path} is missing columns: {missing}"
        )
    # Write back canonical column order (lower‑case)
    df = df[[c for c in REQUIRED_COLUMNS]]
    df.to_csv(csv_path, index=False)

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
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    logger = get_logger(__name__)
    logger.info("Starting curation of reference substructures (T005)")

    # Source file lives in the repository assets folder
    source_path = paths.data("assets", "reference_substructures.csv")
    if not source_path.is_file():
        logger.error(f"Source reference substructures asset not found at {source_path}")
        raise FileNotFoundError(f"Missing asset: {source_path}")

    # Destination path inside the project's raw data hierarchy
    target_path = paths.data("raw", "reference_substructures_raw.csv")

    # Ensure the destination directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Overwrite any existing file to guarantee freshness
    if target_path.exists():
        logger.info(f"Removing stale file at {target_path}")
        target_path.unlink()

    logger.info(f"Copying reference substructures from {source_path} to {target_path}")
    shutil.copy2(source_path, target_path)

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

if __name__ == "__main__":
    main()

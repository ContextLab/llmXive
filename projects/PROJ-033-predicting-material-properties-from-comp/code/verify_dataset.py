"""
verify_dataset.py

Utility script for Task T002: Validate the presence and integrity of the
open Materials dataset (including the required ``hardness`` column).

The script performs the following steps:
1. Locate the first CSV file under ``data/raw``.
2. Verify that the CSV contains the required columns:
   ``material_id, formula, band_gap, hardness, crystal_system``.
3. Compute a SHA‑256 checksum of the file (memory‑efficient streaming).
4. Record the checksum in ``data/raw/README.md`` (updating an existing
   ``checksum: <value>`` line or appending a new one).
5. Load the JSON‑Schema ``contracts/materials_dataset.schema.yaml``.
6. Validate every row of the CSV against the schema; raise an exception
   on the first validation error.

The script is deliberately minimal – it has no CLI arguments because the
quick‑start guide invokes it directly.  It can also be imported and its
functions called programmatically.

Usage (as invoked by the quick‑start):
    python code/verify_dataset.py
"""
import hashlib
import logging
from pathlib import Path
from typing import List

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {
    "material_id",
    "formula",
    "band_gap",
    "hardness",
    "crystal_system",
}
RAW_DATA_DIR = Path("data") / "raw"
README_PATH = RAW_DATA_DIR / "README.md"
SCHEMA_PATH = Path("contracts") / "materials_dataset.schema.yaml"

log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def find_dataset_file() -> Path:
    """
    Return the first CSV file found in ``data/raw``.
    Raises FileNotFoundError if none are present.
    """
    csv_files = sorted(RAW_DATA_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV dataset found in {RAW_DATA_DIR}")
    dataset_path = csv_files[0]
    log.info("Dataset file located: %s", dataset_path)
    return dataset_path

def check_columns(csv_path: Path) -> None:
    """
    Validate that the CSV header contains all required columns.
    Raises ValueError if any are missing.
    """
    df_head = pd.read_csv(csv_path, nrows=0)
    missing = REQUIRED_COLUMNS - set(df_head.columns)
    if missing:
        raise ValueError(
            f"CSV file {csv_path} missing required columns: {sorted(missing)}"
        )
    log.info("All required columns are present in %s", csv_path)

def compute_sha256(csv_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of ``csv_path`` using a streaming
    approach (64 KB chunks) to keep memory usage low.
    """
    sha256 = hashlib.sha256()
    with csv_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    log.info("SHA‑256 checksum for %s: %s", csv_path, checksum)
    return checksum

def record_checksum(csv_path: Path, checksum: str) -> None:
    """
    Write (or update) a line ``checksum: <sha256>`` in
    ``data/raw/README.md``.  If a checksum line already exists it is
    replaced; otherwise the line is appended.
    """
    line = f"checksum: {checksum}"
    if not README_PATH.parent.exists():
        README_PATH.parent.mkdir(parents=True, exist_ok=True)

    if README_PATH.is_file():
        # Read existing lines, replace if a checksum line is found
        with README_PATH.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        updated = False
        for i, existing in enumerate(lines):
            if existing.lower().startswith("checksum:"):
                lines[i] = line + "\n"
                updated = True
                break
        if not updated:
            lines.append(line + "\n")
        with README_PATH.open("w", encoding="utf-8") as f:
            f.writelines(lines)
    else:
        # No README yet – create a minimal one with the checksum line
        with README_PATH.open("w", encoding="utf-8") as f:
            f.write(line + "\n")
    log.info("Recorded checksum in %s", README_PATH)

def load_schema() -> dict:
    """
    Load the JSON‑Schema for the materials dataset.
    """
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    log.info("Loaded schema from %s", SCHEMA_PATH)
    return schema

def _row_to_native(row: pd.Series) -> dict:
    """
    Convert a pandas Series to a plain ``dict`` with native Python types.
    This mirrors the helper in ``src/data/loader.py``.
    """
    return {k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()}

def validate_rows(csv_path: Path, schema: dict) -> None:
    """
    Validate each row of ``csv_path`` against ``schema``.
    Raises ValidationError on the first invalid row.
    """
    validator = Draft7Validator(schema)
    for chunk in pd.read_csv(csv_path, chunksize=5000):
        for _, row in chunk.iterrows():
            native_row = _row_to_native(row)
            errors = list(validator.iter_errors(native_row))
            if errors:
                # Report the first error for brevity
                err = errors[0]
                raise ValidationError(
                    f"Row validation failed for material_id={native_row.get('material_id')}: {err.message}"
                )
    log.info("All rows in %s conform to the schema", csv_path)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrates the verification steps for Task T002.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    dataset_path = find_dataset_file()
    check_columns(dataset_path)
    checksum = compute_sha256(dataset_path)
    record_checksum(dataset_path, checksum)
    schema = load_schema()
    validate_rows(dataset_path, schema)
    log.info("Dataset verification completed successfully.")

if __name__ == "__main__":
    main()
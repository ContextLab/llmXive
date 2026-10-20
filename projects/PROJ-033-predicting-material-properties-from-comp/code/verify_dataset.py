"""Verify presence and integrity of the Materials dataset.

This script checks that a CSV file exists in ``data/raw`` with the required
columns: ``material_id``, ``formula``, ``band_gap``, ``hardness``, and
``crystal_system``. If such a file is found, it computes the SHA‑256 checksum,
records it in ``data/raw/README.md``, and validates every row against the
JSON‑Schema defined in ``contracts/materials_dataset.schema.yaml`` using
``jsonschema``. If any condition is not met, a clear exception is raised
explaining what is missing or invalid.

The script is intended to be run as part of the quick‑start workflow:

``python code/verify_dataset.py``

It exits with status 0 on success; any exception will cause a non‑zero exit
code, which the CI verification step interprets as task failure.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

REQUIRED_COLUMNS = {
    "material_id",
    "formula",
    "band_gap",
    "hardness",
    "crystal_system",
}

def find_dataset_file() -> Path:
    """Return the first CSV file found in ``data/raw``."""
    raw_dir = paths.data("raw")
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV file found in {raw_dir}. Please place a dataset "
            "conforming to `contracts/materials_dataset.schema.yaml` at that location."
        )
    if len(csv_files) > 1:
        log.warning(
            f"Multiple CSV files found in {raw_dir}. Using the first one: {csv_files[0].name}"
        )
    return csv_files[0]

def check_columns(csv_path: Path) -> None:
    """Validate that the CSV header contains all required columns."""
    # Read only the header line to avoid loading the whole file.
    cols = pd.read_csv(csv_path, nrows=0).columns.tolist()
    missing = REQUIRED_COLUMNS - set(cols)
    if missing:
        raise ValueError(
            f"The dataset {csv_path.name} is missing required columns: {sorted(missing)}. "
            f"Required columns are: {sorted(REQUIRED_COLUMNS)}."
        )
    log.info(f"All required columns present in {csv_path.name}.")

def compute_sha256(csv_path: Path) -> str:
    """Compute the SHA‑256 checksum of the file in a memory‑efficient way."""
    sha256 = hashlib.sha256()
    with csv_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    log.info(f"SHA‑256 checksum for {csv_path.name}: {checksum}")
    return checksum

def record_checksum(csv_path: Path, checksum: str) -> None:
    """Write (or update) the checksum in ``data/raw/README.md``."""
    readme_path = paths.data("raw", "README.md")
    entry = f"{csv_path.name} SHA256: {checksum}\n"
    if readme_path.exists():
        # Replace an existing line for this file if present.
        lines = readme_path.read_text().splitlines()
        for i, line in enumerate(lines):
            if line.startswith(csv_path.name):
                lines[i] = entry.strip()
                break
        else:
            lines.append(entry.strip())
        new_content = "\n".join(lines) + "\n"
    else:
        new_content = entry
    readme_path.write_text(new_content)
    log.info(f"Recorded checksum in {readme_path}")

def load_schema() -> dict:
    """Load the JSON‑Schema for the materials dataset."""
    schema_path = paths.contracts("materials_dataset.schema.yaml")
    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    if not isinstance(schema, dict):
        raise TypeError(f"Schema at {schema_path} did not parse to a dict.")
    return schema

def validate_rows(csv_path: Path, schema: dict) -> None:
    """Validate each row of the CSV against the JSON‑Schema."""
    validator = Draft7Validator(schema)
    # Use chunked reading to stay within memory limits.
    for chunk in pd.read_csv(csv_path, chunksize=5000):
        for idx, row in chunk.iterrows():
            # jsonschema works with native Python types; convert pandas Series to dict.
            instance = json.loads(row.to_json())
            errors = list(validator.iter_errors(instance))
            if errors:
                # Report the first error for brevity.
                err = errors[0]
                raise ValidationError(
                    f"Row {idx} in {csv_path.name} violates the schema: {err.message}"
                )
    log.info(f"All rows in {csv_path.name} conform to the schema.")

def main() -> None:
    csv_path = find_dataset_file()
    check_columns(csv_path)
    checksum = compute_sha256(csv_path)
    record_checksum(csv_path, checksum)
    schema = load_schema()
    validate_rows(csv_path, schema)
    log.info("Dataset verification completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)
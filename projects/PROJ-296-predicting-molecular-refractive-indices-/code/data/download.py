"""
Download the curated refractive‑index dataset, verify its SHA‑256 checksum,
store it under ``data/raw/ri_dataset.csv`` and validate each row against the
dataset schema (``contracts/dataset.schema.yaml``).

The script is intended to be run as a stand‑alone command:

    python data/download.py

It performs the following steps:

1. Download the dataset file from the verified Hugging‑Face hub
   ``chemistry/ri_dataset`` using the ``huggingface_hub`` library.
2. Copy the file to ``data/raw/ri_dataset.csv`` (creating the ``raw``
   directory if necessary).
3. Compute the SHA‑256 checksum of the written file.
4. Compare the checksum with the expected value stored in
   ``state/download_checksum.txt``.  If the file does not exist, the
   computed checksum is written there for future runs.
5. Load the CSV with ``pandas`` and validate every record against the
   JSON‑Schema defined in ``contracts/dataset.schema.yaml`` using
   ``jsonschema``.  The script aborts with a clear error message if any
   validation fails.

All paths are resolved via the ``llmxive_toolkit.paths`` helper which
guarantees that the required directories exist.
"""

import hashlib
import json
from pathlib import Path
import shutil

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError
from huggingface_hub import hf_hub_download

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The verified Hugging‑Face dataset identifier.
HF_REPO_ID = "chemistry/ri_dataset"
# Expected filename inside the repository.  The dataset is provided as a CSV.
HF_FILENAME = "ri_dataset.csv"

# Destination for the raw CSV file.
RAW_CSV_PATH = paths.data("raw", "ri_dataset.csv")

# Path that stores the reference SHA‑256 checksum.
CHECKSUM_PATH = Path(paths.root) / "state" / "download_checksum.txt"

# Path to the JSON‑Schema that defines the expected column layout.
SCHEMA_PATH = Path(paths.root) / "contracts" / "dataset.schema.yaml"


def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 checksum of *file_path*."""
    hash_sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def load_expected_checksum() -> str | None:
    """Read the expected checksum from ``state/download_checksum.txt``."""
    if CHECKSUM_PATH.is_file():
        return CHECKSUM_PATH.read_text(encoding="utf-8").strip()
    return None


def write_checksum(checksum: str) -> None:
    """Write *checksum* to ``state/download_checksum.txt``."""
    CHECKSUM_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECKSUM_PATH.write_text(checksum + "\n", encoding="utf-8")
    log.info(f"Wrote checksum to {CHECKSUM_PATH}")


def download_dataset() -> pd.DataFrame:
    """
    Download the dataset CSV from Hugging‑Face Hub and return it as a
    ``pandas.DataFrame``.
    """
    log.info(f"Downloading dataset file '{HF_FILENAME}' from repo '{HF_REPO_ID}' …")
    try:
        # ``hf_hub_download`` returns a local cache path to the file.
        cached_path = hf_hub_download(repo_id=HF_REPO_ID, filename=HF_FILENAME, repo_type="dataset")
    except Exception as exc:
        log.error(f"Failed to download dataset from Hugging Face: {exc}")
        raise

    log.info(f"Dataset downloaded to temporary location: {cached_path}")

    # Load into pandas; we assume a CSV format.
    try:
        df = pd.read_csv(cached_path)
    except Exception as exc:
        log.error(f"Failed to read CSV from downloaded file: {exc}")
        raise

    log.info(f"Loaded {len(df)} records from the dataset.")
    return df, Path(cached_path)


def save_dataframe(df: pd.DataFrame) -> None:
    """Write *df* to the CSV path, creating parent directories if needed."""
    RAW_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_CSV_PATH, index=False)
    log.info(f"Saved raw CSV to {RAW_CSV_PATH}")


def validate_rows(df: pd.DataFrame) -> None:
    """
    Validate each row of *df* against the JSON‑Schema.
    Raises ``ValueError`` if any row fails validation.
    """
    log.info(f"Loading schema from {SCHEMA_PATH}")
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    validator = Draft7Validator(schema)

    log.info("Starting row‑wise validation …")
    errors = []
    for idx, row in df.iterrows():
        # Convert the pandas Series to a plain dict (json‑serialisable).
        record = json.loads(row.to_json())
        try:
            validator.validate(record)
        except ValidationError as exc:
            errors.append(f"Row {idx}: {exc.message}")

    if errors:
        log.error("Schema validation failed:")
        for e in errors[:10]:
            log.error(e)
        raise ValueError(f"Schema validation failed for {len(errors)} rows.")
    log.info("All rows passed schema validation.")


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Download the dataset
    # ------------------------------------------------------------------
    df, cached_path = download_dataset()

    # ------------------------------------------------------------------
    # 2. Persist to CSV at the canonical location
    # ------------------------------------------------------------------
    save_dataframe(df)

    # ------------------------------------------------------------------
    # 3. Verify checksum of the persisted file
    # ------------------------------------------------------------------
    actual_checksum = compute_sha256(RAW_CSV_PATH)
    log.info(f"Computed SHA‑256: {actual_checksum}")

    expected_checksum = load_expected_checksum()
    if expected_checksum:
        if actual_checksum != expected_checksum:
            raise ValueError(
                f"Checksum mismatch! Expected {expected_checksum}, got {actual_checksum}"
            )
        else:
            log.info("Checksum matches the recorded value.")
    else:
        # First run – store the checksum for future reproducibility.
        write_checksum(actual_checksum)
        log.info("No reference checksum existed; stored the newly computed value.")

    # ------------------------------------------------------------------
    # 4. Validate each row against the contract schema
    # ------------------------------------------------------------------
    validate_rows(df)

    log.info("Download, checksum verification, and schema validation completed successfully.")


if __name__ == "__main__":
    main()

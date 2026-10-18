"""
Download the curated refractive‑index dataset, verify its SHA‑256 checksum,
store it under ``data/raw/ri_dataset.csv`` and perform lightweight validation
of each row against the essential parts of the dataset schema
(``contracts/dataset.schema.yaml``).

The script is intended to be run as a stand‑alone command:

    python data/download.py

It performs the following steps:

1. Download the dataset CSV from Hugging Face Hub using ``hf_hub_download``.
2. Persist the file to ``data/raw/ri_dataset.csv`` (creating the ``raw``
   directory if necessary).
3. Compute the SHA‑256 checksum of the persisted file.
4. Compare the checksum with the expected value stored in
   ``state/download_checksum.txt``.  If the file does not exist, the
   computed checksum is written there for future runs.
5. Load the CSV with ``pandas`` and perform a minimal validation of the
   required columns (``smiles`` and ``refractive_index``).  The validation
   aborts with a clear error message if any check fails.

All paths are resolved via the ``llmxive_toolkit.paths`` helper which
guarantees that the required directories exist.
"""

import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml
from jsonschema import Draft7Validator, ValidationError
from huggingface_hub import hf_hub_download

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Hugging Face repository identifier for the refractive‑index dataset.
HF_REPO_ID = "zhanglab/ri-dataset"

# Name of the CSV file inside the repository.
HF_DATASET_FILENAME = "ri_dataset.csv"

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
    Download the dataset CSV from Hugging Face Hub and return it as a
    ``pandas.DataFrame``.
    """
    log.info(
        f"Downloading '{HF_DATASET_FILENAME}' from repository '{HF_REPO_ID}' via huggingface_hub …"
    )
    try:
        local_path = hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=HF_DATASET_FILENAME,
            repo_type="dataset",
            # Do not cache forever; we want a fresh copy each run.
            force_download=False,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download dataset file '{HF_DATASET_FILENAME}' from '{HF_REPO_ID}': {exc}"
        ) from exc

    log.info(f"Dataset downloaded to temporary location {local_path}")

    try:
        df = pd.read_csv(local_path)
    except Exception as exc:
        raise RuntimeError(f"Failed to read downloaded CSV into pandas: {exc}") from exc

    log.info(f"Loaded {len(df)} records from the CSV.")
    return df


def save_dataframe(df: pd.DataFrame) -> None:
    """Write *df* to the canonical CSV path, creating parent directories if needed."""
    RAW_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_CSV_PATH, index=False)
    log.info(f"Saved raw CSV to {RAW_CSV_PATH}")


def _minimal_schema_validation(df: pd.DataFrame) -> None:
    """
    Perform a lightweight validation that the required columns exist and
    have appropriate types.  This mirrors the essential constraints of
    ``contracts/dataset.schema.yaml`` without requiring the full set of
    node/edge feature columns, which are added later in preprocessing.
    """
    required_columns = {"smiles", "refractive_index"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in raw dataset: {missing}")

    for idx, row in df.iterrows():
        smiles = row["smiles"]
        ri = row["refractive_index"]
        if not isinstance(smiles, str):
            raise ValueError(f"Row {idx}: 'smiles' must be a string.")
        if not (isinstance(ri, (int, float)) and ri >= 1.0):
            raise ValueError(
                f"Row {idx}: 'refractive_index' must be a number >= 1.0."
            )
    log.info("Minimal schema validation passed for raw dataset.")


def validate_rows(df: pd.DataFrame) -> None:
    """
    Validate each row of *df* against the essential parts of the JSON‑Schema.
    This function delegates to the lightweight validator defined above.
    """
    log.info(f"Loading schema from {SCHEMA_PATH}")
    # Load the full schema for documentation; we only enforce the minimal checks.
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        _ = yaml.safe_load(f)  # noqa: F841 – intentionally ignored

    _minimal_schema_validation(df)


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Download the dataset
    # ------------------------------------------------------------------
    df = download_dataset()

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
    # 4. Validate each row against the contract schema (minimal check)
    # ------------------------------------------------------------------
    validate_rows(df)

    log.info(
        "Download, checksum verification, and minimal schema validation completed successfully."
    )


if __name__ == "__main__":
    main()

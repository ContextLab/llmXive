"""
T015: Save the unified dataset as a Parquet file.

This script loads the intermediate CSV produced by T014, validates that the
dataset satisfies the constraints required by T016 (no null values, fixed‑length
sequences, presence of required columns), and writes the final dataset to
`data/processed/unified_ctcf_dataset.parquet` using Snappy compression.

The script is deliberately idempotent: if the Parquet file already exists it
will be overwritten, ensuring that downstream steps always read the latest
validated data.
"""
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# ----------------------------------------------------------------------
# Path configuration – resolve the project root dynamically
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # <project>/code/data/../..
sys.path.insert(0, str(PROJECT_ROOT))

# Import helper from the preprocessing step
from data.preprocess import load_processed_dataset  # noqa: E402

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# File locations
# ----------------------------------------------------------------------
INTERMEDIATE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "intermediate_ctcf_features.csv"
)
OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "processed" / "unified_ctcf_dataset.parquet"
)

# ----------------------------------------------------------------------
# Validation logic (T016)
# ----------------------------------------------------------------------
def validate_dataset(df: pd.DataFrame) -> bool:
    """
    Validate that the dataset conforms to the strict schema required for
    downstream model training.

    Checks performed:
    1. No NaN values in any column.
    2. All sequences are exactly 1000 bp long.
    3. Required columns are present.

    Raises:
        ValueError: If any validation step fails.
    """
    logger.info("Running dataset validation...")

    # 1. Null check
    if df.isnull().any().any():
        null_cols = df.columns[df.isnull().any()].tolist()
        raise ValueError(
            f"Dataset contains null values in columns: {null_cols}. "
            "All missing values must be resolved before saving."
        )

    # 2. Sequence length check
    if "sequence" not in df.columns:
        raise ValueError("Required column 'sequence' is missing.")
    seq_lengths = df["sequence"].apply(len)
    unique_lengths = seq_lengths.unique()
    if len(unique_lengths) != 1 or unique_lengths[0] != 1000:
        raise ValueError(
            f"Sequence length inconsistency detected: {unique_lengths}. "
            "All sequences must be exactly 1000 bp."
        )
    logger.info(f"All sequences are {unique_lengths[0]} bp long.")

    # 3. Required columns check
    required_cols = {"sequence", "cell_type", "peak_type", "atac_signal"}
    missing = required_cols.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    logger.info("Dataset validation passed.")
    return True

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the save‑dataset pipeline.

    Steps:
    1. Ensure the output directory exists.
    2. Load the intermediate CSV (produced by T014).
    3. Validate the DataFrame.
    4. Write the DataFrame to Parquet with Snappy compression.
    """
    # Ensure the output directory hierarchy exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Locate the source CSV
    source_path = INTERMEDIATE_FILE
    if not source_path.exists():
        # Fall back to any CSV in the processed folder (helps during
        # iterative development) and emit a warning.
        csv_candidates = list(
            (PROJECT_ROOT / "data" / "processed").glob("*.csv")
        )
        if not csv_candidates:
            raise FileNotFoundError(
                f"Intermediate dataset not found at {source_path} and no CSV "
                "files are present in data/processed/. Ensure T014 has run."
            )
        source_path = csv_candidates[0]
        logger.warning(
            f"Expected intermediate file missing. Using fallback CSV: {source_path}"
        )

    logger.info(f"Loading intermediate dataset from {source_path}...")
    try:
        df = pd.read_csv(source_path)
    except Exception as exc:
        logger.error(f"Failed to read CSV: {exc}")
        raise

    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")

    # Validate the DataFrame according to T016 requirements
    try:
        validate_dataset(df)
    except ValueError as exc:
        logger.error(f"Validation error: {exc}")
        sys.exit(1)

    # Write to Parquet
    logger.info(f"Saving unified dataset to {OUTPUT_FILE}...")
    try:
        df.to_parquet(
            OUTPUT_FILE,
            engine="pyarrow",
            compression="snappy",
            index=False,
        )
    except Exception as exc:
        logger.error(f"Failed to write Parquet file: {exc}")
        raise

    size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    logger.info(
        f"Successfully saved {len(df)} rows to {OUTPUT_FILE} ({size_mb:.2f} MB)."
    )
    logger.info("T015 completed successfully.")

if __name__ == "__main__":
    main()

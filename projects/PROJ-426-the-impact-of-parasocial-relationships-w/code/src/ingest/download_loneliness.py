"""
Download the Reddit Loneliness Longitudinal Dataset from Zenodo.

This script fetches the dataset associated with the DOI provided in the
configuration, validates required columns, enforces a minimum longitudinal
depth per user, and writes the cleaned data to a Parquet file.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

# Ensure the project root is on the import path when executed as a script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from zenodo_get import zenodo_get
from src.utils.logging import get_logger, log_stage_start, log_stage_end, log_error_context
from src.utils.config import get_config
from src.utils.data_validation import record_checksum, ValidationError

# Configure logger
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants required by the unit test
# ----------------------------------------------------------------------
MIN_MONTHS_PER_USER: int = 6          # Minimum distinct months with a score per user
MIN_ROWS: int = 600                   # Minimum total rows after cleaning
OUTPUT_PARQUET = Path("data/raw/loneliness_dataset.parquet")

# ----------------------------------------------------------------------
# Expected column names (as defined in the specification)
# ----------------------------------------------------------------------
REQUIRED_COLUMNS: List[str] = [
    "username_hash",
    "UCLA_Loneliness_Score",
    "timestamp",
    "baseline_text",
    "age",
    "gender",
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_config() -> Dict[str, Any]:
    """Load configuration for data paths and Zenodo DOI."""
    cfg = get_config()
    return {
        "zenodo_doi": cfg.get("data", {}).get(
            "zenodo_loneliness_doi", "10.5281/zenodo.123456"
        ),
        "output_dir": Path("data/raw"),
    }

def fetch_dataset(zenodo_doi: str, output_dir: Path) -> Path:
    """
    Fetch dataset from Zenodo using zenodo_get.

    Returns the path to the first data file (CSV, Parquet, or ZIP) found.
    """
    logger.info(f"Fetching dataset from Zenodo DOI: {zenodo_doi}")
    zenodo_get([zenodo_doi], output_dir=str(output_dir))

    # Locate a suitable data file
    candidates = [
        p for p in output_dir.rglob("*")
        if p.suffix.lower() in {".csv", ".parquet", ".zip"}
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No CSV/Parquet/ZIP files found in {output_dir} after downloading {zenodo_doi}"
        )
    # Prefer non‑ZIP files first
    for p in candidates:
        if p.suffix.lower() != ".zip":
            return p
    # If only ZIPs were found, return the first ZIP (it will be extracted later)
    return candidates[0]

def _load_dataframe(file_path: Path) -> pd.DataFrame:
    """Load CSV or Parquet (or ZIP‑contained CSV/Parquet) into a DataFrame."""
    if file_path.suffix.lower() == ".csv":
        return pd.read_csv(file_path)
    if file_path.suffix.lower() == ".parquet":
        return pd.read_parquet(file_path)
    if file_path.suffix.lower() == ".zip":
        import zipfile
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            # Find the first CSV or Parquet inside the zip
            for name in zip_ref.namelist():
                if name.lower().endswith(".csv"):
                    with zip_ref.open(name) as f:
                        return pd.read_csv(f)
                if name.lower().endswith(".parquet"):
                    with zip_ref.open(name) as f:
                        return pd.read_parquet(f)
        raise ValueError("ZIP archive does not contain a CSV or Parquet file.")
    raise ValueError(f"Unsupported file type: {file_path}")

def _validate_columns(df: pd.DataFrame) -> None:
    """Ensure all REQUIRED_COLUMNS are present in the DataFrame."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValidationError(
            f"Dataset is missing required columns: {missing}"
        )

def _enforce_longitudinal_depth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep only users that have at least MIN_MONTHS_PER_USER distinct calendar
    months with a non‑null UCLA_Loneliness_Score.
    """
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Drop rows where timestamp could not be parsed
    df = df.dropna(subset=["timestamp"])

    # Extract year‑month for grouping
    df["year_month"] = df["timestamp"].dt.to_period("M")

    # Count distinct months with non‑null scores per user
    month_counts = (
        df.dropna(subset=["UCLA_Loneliness_Score"])
        .groupby("username_hash")["year_month"]
        .nunique()
    )
    eligible_users = month_counts[month_counts >= MIN_MONTHS_PER_USER].index

    filtered = df[df["username_hash"].isin(eligible_users)].copy()
    # Clean up helper column
    filtered.drop(columns=["year_month"], inplace=True)
    return filtered

def _final_row_count_check(df: pd.DataFrame) -> None:
    """Raise an error if the cleaned dataset does not meet MIN_ROWS."""
    if len(df) < MIN_ROWS:
        raise ValidationError(
            f"Dataset contains only {len(df)} rows after cleaning; "
            f"minimum required is {MIN_ROWS}."
        )

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Download, validate, clean, and persist the Reddit Loneliness Dataset."""
    log_stage_start("T003: Download Reddit Loneliness Longitudinal Dataset")

    try:
        cfg = load_config()
        output_dir: Path = cfg["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)

        # ------------------------------------------------------------------
        # 1. Download the raw file
        # ------------------------------------------------------------------
        raw_file = fetch_dataset(cfg["zenodo_doi"], output_dir)

        # ------------------------------------------------------------------
        # 2. Load into a DataFrame
        # ------------------------------------------------------------------
        df = _load_dataframe(raw_file)

        # ------------------------------------------------------------------
        # 3. Validate required columns
        # ------------------------------------------------------------------
        _validate_columns(df)

        # ------------------------------------------------------------------
        # 4. Enforce longitudinal depth per user
        # ------------------------------------------------------------------
        df = _enforce_longitudinal_depth(df)

        # ------------------------------------------------------------------
        # 5. Minimum row count check
        # ------------------------------------------------------------------
        _final_row_count_check(df)

        # ------------------------------------------------------------------
        # 6. Persist cleaned data
        # ------------------------------------------------------------------
        OUTPUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(OUTPUT_PARQUET, index=False)

        # Record checksum for provenance
        checksum_path = OUTPUT_PARQUET.parent / "loneliness_dataset.sha256"
        record_checksum(OUTPUT_PARQUET, checksum_path)

        logger.info(f"Cleaned dataset written to {OUTPUT_PARQUET}")
        log_stage_end("T003: Download Reddit Loneliness Longitudinal Dataset", success=True)

    except Exception as e:
        log_error_context("T003: Download Reddit Loneliness Longitudinal Dataset", e)
        log_stage_end("T003: Download Reddit Loneliness Longitudinal Dataset", success=False)
        raise

if __name__ == "__main__":
    main()

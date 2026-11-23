"""
T012c: Extract behavioral scores from validated raw parquet files.

This script reads all parquet files located in `data/raw/`, verifies that the
required WCST variable is present, filters participants by the minimum age,
extracts the necessary behavioral columns, and writes the consolidated
results to `data/processed/behavioral_scores.csv`.

The script is intended to be invoked as part of the quickstart pipeline
after the data download and validation steps.
"""
import sys
import logging
from pathlib import Path

import pandas as pd

# Project‑relative imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_wcst_variable_name, get_min_age
from utils.logging_config import get_logger, setup_data_flow_logger

def setup_logger(name: str) -> logging.Logger:
    """Create a module‑specific logger using the project's logging config."""
    return get_logger(name)

def load_raw_parquet_files(raw_dir: Path) -> pd.DataFrame:
    """
    Load all parquet files from ``raw_dir`` and concatenate them into a single
    DataFrame.

    Parameters
    ----------
    raw_dir : Path
        Directory containing ``*.parquet`` files.

    Returns
    -------
    pd.DataFrame
        Combined DataFrame of all raw records.

    Raises
    ------
    FileNotFoundError
        If ``raw_dir`` does not exist or contains no parquet files.
    """
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Raw data directory does not exist: {raw_dir}")

    parquet_files = list(raw_dir.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {raw_dir}")

    dfs = []
    for f in parquet_files:
        try:
            df = pd.read_parquet(f)
            dfs.append(df)
            logging.info(f"Loaded {f.name} with shape {df.shape}")
        except Exception as e:
            logging.error(f"Failed to read {f.name}: {e}")
            raise

    combined = pd.concat(dfs, ignore_index=True)
    logging.info(f"Combined raw data shape: {combined.shape}")
    return combined

def verify_variable_fit(df: pd.DataFrame, wcst_col: str) -> None:
    """
    Ensure the required WCST column exists in the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to check.
    wcst_col : str
        Name of the WCST variable (e.g., ``wcst_perseverative_errors``).

    Raises
    ------
    RuntimeError
        If the column is missing – this matches the ``DATASET_VARIABLE_MISMATCH``
        error contract for the task.
    """
    if wcst_col not in df.columns:
        available = ", ".join(df.columns.tolist())
        msg = (
            f"DATASET_VARIABLE_MISMATCH: Required column '{wcst_col}' not found. "
            f"Available columns: [{available}]"
        )
        logging.critical(msg)
        raise RuntimeError(msg)

def extract_behavioral_scores(df: pd.DataFrame, wcst_col: str) -> pd.DataFrame:
    """
    Filter participants by age, keep only the required columns, and clean the data.

    Parameters
    ----------
    df : pd.DataFrame
        Raw combined DataFrame.
    wcst_col : str
        WCST column name.

    Returns
    -------
    pd.DataFrame
        Cleaned behavioral scores with columns:
        ``participant_id``, ``age``, ``wcst_perseverative_errors`` (or the
        configured WCST column name), plus any optional covariates that are
        present in the source data.
    """
    # Resolve participant identifier column
    id_candidates = ["participant_id", "sub_id", "subject_id", "id"]
    id_col = next((c for c in id_candidates if c in df.columns), None)
    if not id_col:
        raise RuntimeError("Unable to locate a participant identifier column.")

    # Ensure age column exists (or try to infer)
    if "age" not in df.columns:
        age_candidates = [c for c in df.columns if "age" in c.lower()]
        if age_candidates:
            df = df.rename(columns={age_candidates[0]: "age"})
            logging.info(f"Renamed column {age_candidates[0]} to 'age'")
        else:
            raise RuntimeError("Age column missing and could not be inferred.")

    # Keep required columns
    required = [id_col, "age", wcst_col]
    optional = [c for c in ["education", "task_accuracy",
                            "neurological_condition", "medication_use"]
                if c in df.columns]
    cols = required + optional
    subset = df[cols].copy()

    # Rename identifier to canonical name
    subset = subset.rename(columns={id_col: "participant_id"})

    # Age filter (minimum age is defined in config)
    min_age = get_min_age()
    before = len(subset)
    subset = subset[subset["age"] >= min_age]
    after = len(subset)
    logging.info(f"Age filter >= {min_age}: {before} -> {after} participants")

    # Drop rows with missing critical values
    subset = subset.dropna(subset=["participant_id", "age", wcst_col])
    logging.info(f"After dropping NaNs, {len(subset)} rows remain")

    # Ensure correct dtypes
    subset["age"] = pd.to_numeric(subset["age"], errors="coerce").astype(int)
    subset[wcst_col] = pd.to_numeric(subset[wcst_col], errors="coerce")
    return subset

def main() -> int:
    """
    Entry point for the script.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    # Initialise logger
    logger = setup_logger("extract_behavior")
    logger.info("Starting behavioral extraction (T012c)")

    # Resolve project paths
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "behavioral_scores.csv"

    try:
        # Load and verify data
        combined_df = load_raw_parquet_files(raw_dir)
        wcst_var = get_wcst_variable_name()
        verify_variable_fit(combined_df, wcst_var)

        # Extract and save
        behavioral_df = extract_behavioral_scores(combined_df, wcst_var)
        behavioral_df.to_csv(output_path, index=False)

        logger.info(f"Behavioral scores written to {output_path}")
        logger.info(f"Rows written: {len(behavioral_df)}")
        logger.info(f"Columns: {list(behavioral_df.columns)}")
        print("Extraction completed successfully.")
        return 0

    except Exception as exc:
        logger.error(f"Extraction failed: {exc}")
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

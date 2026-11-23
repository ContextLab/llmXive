"""
T009g: Implement curation logic for both reference sets.

This script verifies that the downloaded reference sets (known reactive substructures
and kinetic datasets) match their respective criteria before final ingestion.
It performs literature/source validation checks and logs results to
artifacts/curation_validation.log.

Criteria:
- Reference Substructures (T009a/c): Must contain SMILES and a literature source ID.
- Kinetic Dataset (T009d/f): Must contain SMILES, a reaction rate value, and a
  literature source ID.
"""
import os
import sys
import logging
import pandas as pd
from typing import Optional, List, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config, ensure_directories

def setup_script_logging() -> logging.Logger:
    """Configure logging for the curation script."""
    logger = logging.getLogger("curation")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (append mode to preserve previous runs if any)
    log_path = os.path.join("artifacts", "curation_validation.log")
    ensure_directories([os.path.dirname(log_path)])
    fh = logging.FileHandler(log_path, mode="a")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def validate_reference_substructures(df: pd.DataFrame, logger: logging.Logger) -> Tuple[bool, List[str]]:
    """
    Validate the reference substructures dataset against 'known reactive' criteria.

    Criteria:
    1. Must have a 'smiles' column with non-null values.
    2. Must have a 'source_literature' or 'source_id' column indicating origin.
    3. (Optional but checked) Must not contain obviously invalid SMILES (basic length check).

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_failure_messages)
    """
    failures = []

    # Check required columns
    required_cols = ["smiles"]
    # Flexible check for source column
    source_cols = [c for c in df.columns if "source" in c.lower() or "literature" in c.lower()]

    if not source_cols:
        failures.append("Missing required source/literature column. Expected column containing 'source' or 'literature'.")
    else:
        source_col = source_cols[0]
        if df[source_col].isnull().all():
            failures.append(f"Column '{source_col}' is entirely empty.")

    if "smiles" not in df.columns:
        failures.append("Missing required 'smiles' column.")
    else:
        # Check for empty or very short SMILES (heuristic for invalid)
        invalid_smiles_count = df[df["smiles"].isnull() | (df["smiles"].str.len() < 3)].shape[0]
        if invalid_smiles_count > 0:
            failures.append(f"Found {invalid_smiles_count} rows with missing or invalid (too short) SMILES.")

    if failures:
        logger.error("Reference Substructures validation FAILED.")
        for f in failures:
            logger.error(f"  - {f}")
        return False, failures

    logger.info("Reference Substructures validation PASSED.")
    logger.info(f"  - Found {len(df)} valid entries with source information.")
    return True, []

def validate_kinetic_dataset(df: pd.DataFrame, logger: logging.Logger) -> Tuple[bool, List[str]]:
    """
    Validate the kinetic dataset against 'experimental reaction rates' criteria.

    Criteria:
    1. Must have a 'smiles' column.
    2. Must have a reaction rate column (e.g., 'rate', 'k', 'reaction_rate').
    3. Must have a source/literature column.
    4. Rate values must be numeric and non-negative.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_failure_messages)
    """
    failures = []

    # Check required columns
    if "smiles" not in df.columns:
        failures.append("Missing required 'smiles' column.")

    # Identify rate column
    rate_cols = [c for c in df.columns if "rate" in c.lower() or c.lower() == "k"]
    if not rate_cols:
        failures.append("Missing reaction rate column. Expected column containing 'rate' or 'k'.")
    else:
        rate_col = rate_cols[0]
        # Check if numeric
        try:
            pd.to_numeric(df[rate_col], errors='raise')
            if (df[rate_col] < 0).any():
                failures.append(f"Column '{rate_col}' contains negative values, which are invalid for reaction rates.")
        except (ValueError, TypeError):
            failures.append(f"Column '{rate_col}' contains non-numeric values.")

    # Check source column
    source_cols = [c for c in df.columns if "source" in c.lower() or "literature" in c.lower()]
    if not source_cols:
        failures.append("Missing required source/literature column.")
    else:
        source_col = source_cols[0]
        if df[source_col].isnull().all():
            failures.append(f"Column '{source_col}' is entirely empty.")

    if failures:
        logger.error("Kinetic Dataset validation FAILED.")
        for f in failures:
            logger.error(f"  - {f}")
        return False, failures

    logger.info("Kinetic Dataset validation PASSED.")
    logger.info(f"  - Found {len(df)} valid entries with rate data and source information.")
    return True, []

def curate_datasets(config: dict, logger: logging.Logger) -> bool:
    """
    Main orchestration function to curate both reference sets.

    Reads raw files, validates them, and if valid, copies them to the assets
    directory (overwriting previous ingested versions if necessary, ensuring
    consistency). If validation fails, the process halts and logs the error.
    """
    raw_sub_path = os.path.join("data", "raw", "reference_substructures_raw.csv")
    raw_kinetic_path = os.path.join("data", "raw", "kinetic_dataset_raw.csv")
    asset_sub_path = os.path.join("data", "assets", "reference_substructures.csv")
    asset_kinetic_path = os.path.join("data", "assets", "kinetic_dataset.csv")

    success = True

    # 1. Curate Reference Substructures
    logger.info("-" * 40)
    logger.info("Starting curation for Reference Substructures...")
    if not os.path.exists(raw_sub_path):
        logger.error(f"Raw file not found: {raw_sub_path}")
        return False

    try:
        df_sub = pd.read_csv(raw_sub_path)
        is_valid_sub, _ = validate_reference_substructures(df_sub, logger)

        if is_valid_sub:
            # Ensure output directory exists
            ensure_directories([os.path.dirname(asset_sub_path)])
            df_sub.to_csv(asset_sub_path, index=False)
            logger.info(f"Successfully curated and saved to {asset_sub_path}")
        else:
            logger.error("Curation failed for Reference Substructures. Aborting.")
            success = False
    except Exception as e:
        logger.error(f"Error processing Reference Substructures: {e}")
        success = False

    if not success:
        return False

    # 2. Curate Kinetic Dataset
    logger.info("-" * 40)
    logger.info("Starting curation for Kinetic Dataset...")
    if not os.path.exists(raw_kinetic_path):
        logger.error(f"Raw file not found: {raw_kinetic_path}")
        return False

    try:
        df_kin = pd.read_csv(raw_kinetic_path)
        is_valid_kin, _ = validate_kinetic_dataset(df_kin, logger)

        if is_valid_kin:
            # Ensure output directory exists
            ensure_directories([os.path.dirname(asset_kinetic_path)])
            df_kin.to_csv(asset_kinetic_path, index=False)
            logger.info(f"Successfully curated and saved to {asset_kinetic_path}")
        else:
            logger.error("Curation failed for Kinetic Dataset. Aborting.")
            success = False
    except Exception as e:
        logger.error(f"Error processing Kinetic Dataset: {e}")
        success = False

    return success

def main():
    """Entry point for the curation script."""
    logger = setup_script_logging()
    config = get_config()

    logger.info("Starting Reference Set Curation (Task T009g)...")
    logger.info(f"Config: {config}")

    success = curate_datasets(config, logger)

    if success:
        logger.info("Curation completed successfully.")
        sys.exit(0)
    else:
        logger.error("Curation failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
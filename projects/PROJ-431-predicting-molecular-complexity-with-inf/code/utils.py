"""
Utility functions for the Molecular Complexity Prediction pipeline.

Provides logging setup, SMILES validation, file I/O helpers, and
mandatory dataset verification with a hard gate for required columns.
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Callable

import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem


# --- Logging Configuration ---

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Configure the root logger and return a project-specific logger.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, logs only to console.
        log_format: Optional custom format string. Defaults to a standard format.

    Returns:
        A configured logger instance.
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logger = logging.getLogger("molecular_complexity")
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates on re-calls
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)

    return logger


# --- SMILES Validation ---

def validate_smiles(smiles: str) -> Tuple[bool, Optional[Chem.Mol]]:
    """
    Validate a single SMILES string using RDKit.

    Args:
        smiles: The SMILES string to validate.

    Returns:
        A tuple (is_valid, mol_object).
        - is_valid: True if the SMILES parses correctly and is not empty.
        - mol_object: The RDKit Mol object if valid, otherwise None.
    """
    if not smiles or not isinstance(smiles, str):
        return False, None

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False, None
        # Optional: Sanitize to catch deeper issues
        Chem.SanitizeMol(mol)
        return True, mol
    except Exception:
        return False, None


def validate_smiles_column(
    df: pd.DataFrame,
    smiles_col: str = "smiles",
    log: Optional[logging.Logger] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Validate the SMILES column in a DataFrame and drop invalid rows.

    Args:
        df: The input DataFrame.
        smiles_col: Name of the column containing SMILES strings.
        log: Optional logger instance.

    Returns:
        A tuple (cleaned_df, invalid_count).
        - cleaned_df: DataFrame with invalid SMILES rows removed.
        - invalid_count: Number of rows dropped due to invalid SMILES.
    """
    if log is None:
        log = logging.getLogger("molecular_complexity")

    valid_indices = []
    invalid_count = 0

    for idx, row in df.iterrows():
        smiles_val = row[smiles_col]
        is_valid, _ = validate_smiles(smiles_val)
        if is_valid:
            valid_indices.append(idx)
        else:
            invalid_count += 1
            log.warning(f"Invalid SMILES at index {idx}: '{smiles_val}'")

    cleaned_df = df.loc[valid_indices].reset_index(drop=True)
    log.info(f"Validated SMILES: {invalid_count} invalid rows dropped. {len(cleaned_df)} valid rows remaining.")

    return cleaned_df, invalid_count


# --- Dataset Verification Hard Gate (FR-008) ---

REQUIRED_COLUMNS = {"smiles", "logS", "logP"}

def verify_dataset_columns(
    df: pd.DataFrame,
    required_cols: Optional[set] = None,
    log: Optional[logging.Logger] = None
) -> None:
    """
    Verify that a DataFrame contains all required columns.

    This function implements the **mandatory dataset verification hard gate**.
    If required columns are missing, it logs a critical error and raises
    a RuntimeError to abort execution immediately.

    Args:
        df: The DataFrame to verify.
        required_cols: Set of required column names. Defaults to REQUIRED_COLUMNS
                       (smiles, logS, logP).
        log: Optional logger instance.

    Raises:
        RuntimeError: If any required columns are missing.
    """
    if required_cols is None:
        required_cols = REQUIRED_COLUMNS

    if log is None:
        log = logging.getLogger("molecular_complexity")

    actual_cols = set(df.columns)
    missing = required_cols - actual_cols

    if missing:
        error_msg = f"CRITICAL: Dataset is missing required columns: {sorted(missing)}. " \
                    f"Required columns are: {sorted(required_cols)}. " \
                    f"Execution aborted as per FR-008."
        log.critical(error_msg)
        raise RuntimeError(error_msg)

    log.info(f"Dataset verification passed. All required columns present: {sorted(required_cols)}")


def load_and_verify_dataset(
    file_path: str,
    required_cols: Optional[set] = None,
    log: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """
    Load a CSV dataset and verify it contains required columns.

    This is a convenience function combining loading and hard-gate verification.

    Args:
        file_path: Path to the CSV file.
        required_cols: Set of required columns. Defaults to REQUIRED_COLUMNS.
        log: Optional logger.

    Returns:
        The loaded and verified DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If required columns are missing (FR-008 hard gate).
    """
    if log is None:
        log = logging.getLogger("molecular_complexity")

    path = Path(file_path)
    if not path.exists():
        error_msg = f"File not found: {file_path}"
        log.error(error_msg)
        raise FileNotFoundError(error_msg)

    log.info(f"Loading dataset from {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        error_msg = f"Failed to load CSV {file_path}: {e}"
        log.error(error_msg)
        raise RuntimeError(error_msg)

    log.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    verify_dataset_columns(df, required_cols, log)

    return df


# --- File I/O Helpers ---

def ensure_directory(dir_path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Path to the directory.

    Returns:
        The Path object for the directory.
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_dataframe(
    df: pd.DataFrame,
    file_path: str,
    log: Optional[logging.Logger] = None
) -> None:
    """
    Save a DataFrame to a CSV file, ensuring the directory exists.

    Args:
        df: The DataFrame to save.
        file_path: Output file path (CSV).
        log: Optional logger.
    """
    if log is None:
        log = logging.getLogger("molecular_complexity")

    path = Path(file_path)
    ensure_directory(path.parent)

    log.info(f"Saving DataFrame to {file_path} ({len(df)} rows)...")
    df.to_csv(file_path, index=False)
    log.info("Save complete.")


# --- Metadata Join Helper ---

def join_metadata_with_entropy(
    entropy_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    smiles_col: str = "smiles",
    log: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """
    Join an entropy-enriched DataFrame with a metadata DataFrame (containing logS/logP).

    Args:
        entropy_df: DataFrame with computed entropy columns (must have 'smiles').
        metadata_df: DataFrame with 'smiles', 'logS', 'logP' columns.
        smiles_col: Key column name for joining.
        log: Optional logger.

    Returns:
        Joined DataFrame.

    Raises:
        RuntimeError: If join results in loss of rows (indicates mismatched data).
    """
    if log is None:
        log = logging.getLogger("molecular_complexity")

    # Ensure we are joining on the correct column names
    # Assuming both have 'smiles' as the key, or we map them if needed.
    # For this implementation, we assume both use 'smiles'.
    merged = pd.merge(
        entropy_df,
        metadata_df,
        on=smiles_col,
        how='inner'
    )

    if len(merged) != len(entropy_df):
        log.warning(
            f"Join resulted in {len(merged)} rows from {len(entropy_df)} entropy rows. "
            f"Some molecules were not found in metadata. "
            f"This may be expected if metadata was filtered."
        )

    log.info(f"Joined metadata with entropy data. Result: {len(merged)} rows.")
    return merged
"""
Utility functions for the molecular complexity prediction pipeline.

Provides logging setup, SMILES validation, file I/O helpers, and
mandatory dataset verification to ensure input data integrity.
"""
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Callable

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Constants for required columns
REQUIRED_COLUMNS = ['smiles', 'logS', 'logP']
REQUIRED_ENTROPY_COLUMNS = ['atom_entropy', 'bond_entropy']


def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger for the pipeline.
    
    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional path to a log file. If None, logs only to console.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger('molecular_complexity')
    logger.setLevel(log_level)
    
    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)
    
    return logger


def validate_smiles(smiles: str) -> bool:
    """
    Validate a single SMILES string using RDKit.
    
    Args:
        smiles: SMILES string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(smiles, str) or not smiles.strip():
        return False
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False


def validate_smiles_column(df: pd.DataFrame, smiles_col: str = 'smiles') -> Tuple[int, int]:
    """
    Validate all SMILES strings in a DataFrame column.
    
    Args:
        df: Input DataFrame.
        smiles_col: Name of the column containing SMILES strings.
        
    Returns:
        Tuple of (valid_count, invalid_count).
    """
    valid_count = 0
    invalid_count = 0
    
    for idx, smiles in enumerate(df[smiles_col]):
        if validate_smiles(smiles):
            valid_count += 1
        else:
            invalid_count += 1
            logging.warning(f"Invalid SMILES at row {idx}: {smiles[:50]}...")
            
    return valid_count, invalid_count


def verify_dataset_columns(df: pd.DataFrame, required_cols: List[str] = None) -> bool:
    """
    Verify that a DataFrame contains all required columns.
    
    This is a HARD GATE: if required columns are missing, the function
    raises a ValueError to abort execution.
    
    Args:
        df: Input DataFrame.
        required_cols: List of required column names. Defaults to REQUIRED_COLUMNS.
        
    Returns:
        True if all required columns are present.
        
    Raises:
        ValueError: If any required column is missing.
    """
    if required_cols is None:
        required_cols = REQUIRED_COLUMNS
        
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        error_msg = (
            f"Mandatory dataset verification failed: Missing required columns: {missing_cols}. "
            f"Required columns are: {required_cols}. "
            f"Please ensure the input CSV contains 'smiles', 'logS', and 'logP' columns."
        )
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    logging.info(f"Dataset verification passed: All required columns present {required_cols}")
    return True


def load_and_verify_dataset(
    file_path: str, 
    required_cols: List[str] = None,
    smiles_col: str = 'smiles',
    validate_smiles: bool = True
) -> pd.DataFrame:
    """
    Load a CSV dataset and perform mandatory verification checks.
    
    This function enforces:
    1. File existence
    2. Required column presence (HARD GATE)
    3. Optional SMILES validation
    
    Args:
        file_path: Path to the input CSV file.
        required_cols: List of required column names.
        smiles_col: Name of the SMILES column.
        validate_smiles: If True, validate SMILES strings and log warnings.
        
    Returns:
        Validated DataFrame.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing or SMILES validation fails critically.
    """
    path = Path(file_path)
    if not path.exists():
        error_msg = f"Dataset file not found: {file_path}"
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logging.info(f"Loading dataset from: {file_path}")
    df = pd.read_csv(file_path)
    logging.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    
    # HARD GATE: Verify required columns
    verify_dataset_columns(df, required_cols)
    
    # Optional SMILES validation
    if validate_smiles:
        valid_count, invalid_count = validate_smiles_column(df, smiles_col)
        logging.info(f"SMILES validation: {valid_count} valid, {invalid_count} invalid")
        if invalid_count > 0:
            logging.warning(f"Found {invalid_count} invalid SMILES strings. "
                          "These rows may be skipped in downstream processing.")
    
    return df


def ensure_directory(dir_path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory.
        
    Returns:
        Path object for the directory.
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_dataframe(df: pd.DataFrame, file_path: str, index: bool = False) -> None:
    """
    Save a DataFrame to a CSV file.
    
    Args:
        df: DataFrame to save.
        file_path: Output file path.
        index: Whether to write the row index.
    """
    path = Path(file_path)
    ensure_directory(path.parent)
    df.to_csv(file_path, index=index)
    logging.info(f"Saved {len(df)} rows to: {file_path}")


def join_metadata_with_entropy(
    entropy_df: pd.DataFrame, 
    metadata_df: pd.DataFrame, 
    on: str = 'smiles'
) -> pd.DataFrame:
    """
    Join an entropy-enriched DataFrame with metadata (logS, logP).
    
    This function merges the entropy results with the original metadata,
    ensuring that the final dataset contains all required columns for modeling.
    
    Args:
        entropy_df: DataFrame with entropy columns (atom_entropy, bond_entropy).
        metadata_df: DataFrame with metadata columns (logS, logP).
        on: Column name to join on (default: 'smiles').
        
    Returns:
        Merged DataFrame with both entropy and metadata columns.
        
    Raises:
        ValueError: If the join results in an empty DataFrame.
    """
    # Ensure both dataframes have the join key
    if on not in entropy_df.columns:
        raise ValueError(f"Join key '{on}' not found in entropy_df columns: {list(entropy_df.columns)}")
    if on not in metadata_df.columns:
        raise ValueError(f"Join key '{on}' not found in metadata_df columns: {list(metadata_df.columns)}")
        
    merged = pd.merge(
        entropy_df, 
        metadata_df, 
        on=on, 
        how='inner'  # Only keep rows present in both
    )
    
    if len(merged) == 0:
        error_msg = (
            f"Join resulted in an empty DataFrame. "
            f"Entropy rows: {len(entropy_df)}, Metadata rows: {len(metadata_df)}. "
            f"No matching '{on}' values found between the two datasets."
        )
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    logging.info(f"Joined datasets: {len(merged)} rows (from {len(entropy_df)} entropy + {len(metadata_df)} metadata)")
    return merged
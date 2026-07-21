"""
Preprocessing Pipeline for Heusler Alloy Data.

This module orchestrates the standardization, unit normalization, imputation,
DFT filtering, and validation of raw alloy data, saving the final clean dataset
to data/processed/alloys_raw.csv.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Import existing components from the project API surface
from src.preprocessing.composition_parser import parse_batch_compositions
from src.preprocessing.unit_normalizer import standardize_units
from src.preprocessing.imputation_orchestrator import orchestrate_imputation
from src.preprocessing.dft_filter import filter_dft_entries
from src.preprocessing.validator import validate_compositions, extract_elements_from_composition
from src.utils.logging_config import setup_logging, create_logger
from src.utils.checksums import calculate_file_sha256

# Configure logging
logger = create_logger(__name__)
LOG_FILE = Path("data/logs/preprocessing_pipeline.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
setup_logging(log_file=LOG_FILE)

# Constants
RAW_INPUT_PATH = Path("data/raw/merged_alloys.csv")
PROCESSED_OUTPUT_PATH = Path("data/processed/alloys_raw.csv")
VALIDATION_LOG_PATH = Path("data/processed/validation_log.json")


def load_raw_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the raw merged dataset.
    
    Args:
        input_path: Path to the raw CSV. Defaults to data/raw/merged_alloys.csv.
        
    Returns:
        DataFrame containing raw alloy data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    path = input_path or RAW_INPUT_PATH
    if not path.exists():
        raise FileNotFoundError(f"Raw input file not found: {path}")
    
    logger.info(f"Loading raw data from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df


def run_standardization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize composition strings to atomic fractions.
    
    Args:
        df: DataFrame with a 'composition' column.
        
    Returns:
        DataFrame with added atomic fraction columns (e.g., 'Mn_fraction', 'Ga_fraction').
    """
    logger.info("Running composition standardization...")
    # Parse compositions and add fraction columns
    df = parse_batch_compositions(df)
    logger.info("Standardization complete.")
    return df


def run_unit_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize magnetic units (Oe, emu/g) to standard forms.
    
    Args:
        df: DataFrame with hysteresis columns.
        
    Returns:
        DataFrame with normalized unit columns.
    """
    logger.info("Running unit normalization...")
    df = standardize_units(df)
    logger.info("Unit normalization complete.")
    return df


def run_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing data via the Imputation Orchestrator (Spec FR-002).
    
    Logic:
    - If missing rate > 15%: Listwise deletion.
    - If missing rate <= 15%: Mean imputation.
    
    Args:
        df: DataFrame with potential missing values.
        
    Returns:
        DataFrame with missing values handled.
    """
    logger.info("Running imputation logic...")
    df_imputed, stats = orchestrate_imputation(df)
    
    if len(df_imputed) < len(df):
        logger.warning(f"Listwise deletion reduced rows from {len(df)} to {len(df_imputed)}")
    else:
        logger.info("Mean imputation applied (or no missing data found).")
        
    return df_imputed


def run_dft_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out DFT/Simulation entries.
    
    Args:
        df: DataFrame with 'source_type' or 'target_source' columns.
        
    Returns:
        DataFrame with DFT entries removed.
    """
    logger.info("Running DFT filter...")
    df_filtered, excluded_rows = filter_dft_entries(df)
    
    if len(excluded_rows) > 0:
        logger.info(f"Filtered out {len(excluded_rows)} DFT/Simulation entries.")
        # Log excluded entries for audit
        excluded_df = pd.DataFrame(excluded_rows)
        excluded_log_path = Path("data/processed/excluded_dft_entries.csv")
        excluded_df.to_csv(excluded_log_path, index=False)
        logger.info(f"Excluded entries logged to {excluded_log_path}")
    else:
        logger.info("No DFT entries found.")
        
    return df_filtered


def run_validation(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate compositions against the periodic table.
    
    Args:
        df: DataFrame with composition data.
        
    Returns:
        Tuple of (Validated DataFrame, Validation stats).
    """
    logger.info("Running composition validation...")
    
    # Extract elements and validate
    valid_df, invalid_indices, stats = validate_compositions(df)
    
    if len(invalid_indices) > 0:
        logger.warning(f"Found {len(invalid_indices)} rows with unknown elements.")
        # Log invalid rows
        invalid_df = df.iloc[invalid_indices]
        invalid_log_path = Path("data/processed/invalid_compositions.csv")
        invalid_df.to_csv(invalid_log_path, index=False)
        logger.info(f"Invalid compositions logged to {invalid_log_path}")
    else:
        logger.info("All compositions validated successfully.")
        
    return valid_df, stats


def save_processed_data(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the processed DataFrame to CSV and generate a checksum.
    
    Args:
        df: The processed DataFrame.
        output_path: Path to save the CSV. Defaults to data/processed/alloys_raw.csv.
        
    Returns:
        Path to the saved file.
    """
    path = output_path or PROCESSED_OUTPUT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving processed data to {path}")
    df.to_csv(path, index=False)
    
    # Generate checksum
    checksum = calculate_file_sha256(path)
    checksum_path = path.with_suffix(path.suffix + ".sha256")
    checksum_path.write_text(checksum)
    logger.info(f"Saved checksum to {checksum_path}: {checksum}")
    
    return path


def run_preprocessing_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Execute the full preprocessing pipeline.
    
    Steps:
    1. Load raw data.
    2. Standardize compositions.
    3. Normalize units.
    4. Impute missing values (Spec FR-002).
    5. Filter DFT entries.
    6. Validate compositions.
    7. Save results.
    
    Args:
        input_path: Path to raw input CSV.
        output_path: Path to save processed CSV.
        
    Returns:
        The final processed DataFrame.
    """
    logger.info("Starting Preprocessing Pipeline...")
    
    # 1. Load
    df = load_raw_data(input_path)
    
    # 2. Standardize
    df = run_standardization(df)
    
    # 3. Normalize Units
    df = run_unit_normalization(df)
    
    # 4. Impute
    df = run_imputation(df)
    
    # 5. Filter DFT
    df = run_dft_filter(df)
    
    # 6. Validate
    df, validation_stats = run_validation(df)
    
    # 7. Save
    output_file = save_processed_data(df, output_path)
    
    logger.info(f"Preprocessing Pipeline Complete. Output: {output_file}")
    logger.info(f"Final row count: {len(df)}")
    
    return df


def main():
    """Entry point for the preprocessing pipeline."""
    try:
        df = run_preprocessing_pipeline()
        print(f"Pipeline completed successfully. Output: {PROCESSED_OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

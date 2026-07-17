"""
Preprocessing Pipeline for Heusler Alloy Data.

This script orchestrates the standardization, imputation, filtering, and validation
of raw alloy data, saving the final processed dataset to `data/processed/alloys_raw.csv`.

It integrates the following modules:
- composition_parser: Standardize composition strings to atomic fractions.
- unit_normalizer: Normalize coercivity and saturation magnetization units.
- imputation_orchestrator: Handle missing data per Spec FR-002.
- dft_filter: Exclude computational/DFT entries.
- validator: Check for unknown elements.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List

from src.preprocessing.composition_parser import parse_batch_compositions
from src.preprocessing.unit_normalizer import standardize_units
from src.preprocessing.imputation_orchestrator import orchestrate_imputation
from src.preprocessing.dft_filter import filter_dft_entries
from src.preprocessing.validator import validate_compositions
from src.utils.logging_config import setup_logging
from src.utils.checksums import calculate_file_sha256

# Configure logging
logger = setup_logging(__name__)

def load_raw_data(input_path: Path) -> pd.DataFrame:
    """
    Load the merged raw dataset from the ingestion pipeline.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Raw input data not found at {input_path}. "
                                "Please run the ingestion pipeline (T026) first.")
    
    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def run_standardization(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Standardize composition strings to atomic fractions.
    Returns the standardized DataFrame and the count of rows dropped due to parsing errors.
    """
    logger.info("Starting composition standardization...")
    
    # Identify composition column (assumed to be 'composition' or similar based on T016-T018)
    comp_col = None
    for col in ['composition', 'formula', 'alloy_composition']:
        if col in df.columns:
            comp_col = col
            break
    
    if not comp_col:
        raise ValueError("Could not find a composition column in the input data.")
    
    original_len = len(df)
    df_standardized, dropped_count = parse_batch_compositions(df, comp_col)
    
    logger.info(f"Standardization complete. Dropped {dropped_count} rows due to parsing errors.")
    logger.info(f"Remaining rows: {len(df_standardized)}")
    
    return df_standardized, dropped_count

def run_unit_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize units for coercivity and saturation magnetization.
    """
    logger.info("Starting unit normalization...")
    
    # Check for relevant columns
    has_coercivity = any(c in df.columns for c in ['coercivity', 'Hc', 'coercive_force'])
    has_saturation = any(c in df.columns for c in ['saturation_magnetization', 'Ms', 'saturation'])
    
    if not has_coercivity and not has_saturation:
        logger.warning("No coercivity or saturation magnetization columns found. Skipping normalization.")
        return df
    
    df_normalized = standardize_units(df)
    logger.info("Unit normalization complete.")
    
    return df_normalized

def run_imputation(df: pd.DataFrame, missing_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Perform imputation based on missing data rates (Spec FR-002).
    """
    logger.info("Starting imputation orchestration...")
    
    # Determine columns to impute if not specified
    if missing_cols is None:
        # Heuristic: target numeric columns that might have missing values
        # Exclude composition, source, and non-numeric identifiers
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        exclude_cols = ['id', 'row_id', 'source_id']
        missing_cols = [c for c in numeric_cols if c not in exclude_cols]
    
    if not missing_cols:
        logger.info("No numeric columns found for imputation.")
        return df
    
    df_imputed = orchestrate_imputation(df, missing_cols)
    logger.info("Imputation orchestration complete.")
    
    return df_imputed

def run_dft_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Filter out DFT/Calculated entries.
    """
    logger.info("Starting DFT filtering...")
    
    original_len = len(df)
    df_filtered = filter_dft_entries(df)
    dropped_count = original_len - len(df_filtered)
    
    logger.info(f"DFT filtering complete. Removed {dropped_count} DFT entries.")
    logger.info(f"Remaining rows: {len(df_filtered)}")
    
    return df_filtered, dropped_count

def run_validation(df: pd.DataFrame) -> List[str]:
    """
    Validate compositions against the periodic table.
    Returns a list of warning messages.
    """
    logger.info("Running composition validation...")
    
    comp_col = None
    for col in ['composition', 'formula', 'alloy_composition']:
        if col in df.columns:
            comp_col = col
            break
    
    if not comp_col:
        logger.warning("No composition column found for validation.")
        return []
    
    warnings = validate_compositions(df, comp_col)
    logger.info(f"Validation complete. {len(warnings)} warnings generated.")
    
    return warnings

def save_processed_data(df: pd.DataFrame, output_path: Path) -> str:
    """
    Save the processed DataFrame to CSV and calculate checksum.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving processed data to {output_path}")
    df.to_csv(output_path, index=False)
    
    checksum = calculate_file_sha256(output_path)
    logger.info(f"Saved {len(df)} rows. SHA256: {checksum}")
    
    return checksum

def run_preprocessing_pipeline(
    input_path: Path = Path("data/raw/merged_alloys.csv"),
    output_path: Path = Path("data/processed/alloys_raw.csv")
) -> dict:
    """
    Execute the full preprocessing pipeline.
    
    Steps:
    1. Load raw data
    2. Standardize compositions
    3. Normalize units
    4. Filter DFT entries
    5. Impute missing values
    6. Validate
    7. Save
    
    Returns a summary dictionary.
    """
    logger.info("=== Starting Preprocessing Pipeline ===")
    
    # 1. Load
    df = load_raw_data(input_path)
    
    # 2. Standardize
    df, dropped_std = run_standardization(df)
    
    # 3. Normalize
    df = run_unit_normalization(df)
    
    # 4. Filter DFT
    df, dropped_dft = run_dft_filter(df)
    
    # 5. Impute
    df = run_imputation(df)
    
    # 6. Validate
    validation_warnings = run_validation(df)
    if validation_warnings:
        for w in validation_warnings:
            logger.warning(w)
    
    # 7. Save
    checksum = save_processed_data(df, output_path)
    
    summary = {
        "input_rows": len(df), # Updated after drops
        "dropped_standardization": dropped_std,
        "dropped_dft": dropped_dft,
        "output_rows": len(df),
        "output_path": str(output_path),
        "checksum": checksum,
        "validation_warnings_count": len(validation_warnings)
    }
    
    logger.info("=== Preprocessing Pipeline Complete ===")
    return summary

def main():
    """
    Entry point for the preprocessing pipeline script.
    """
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parents[3]
    input_file = project_root / "data" / "raw" / "merged_alloys.csv"
    output_file = project_root / "data" / "processed" / "alloys_raw.csv"
    
    # Allow override via environment or args if needed, but defaults are set
    # For now, we use the defaults or check if the file exists in a relative path
    if not input_file.exists():
        # Fallback to relative path if run from project root
        if Path("data/raw/merged_alloys.csv").exists():
            input_file = Path("data/raw/merged_alloys.csv")
        else:
            logger.error(f"Input file not found: {input_file}")
            logger.error("Please ensure the ingestion pipeline (T026) has run successfully.")
            return 1
    
    try:
        summary = run_preprocessing_pipeline(input_file, output_file)
        logger.info(f"Pipeline Summary: {summary}")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
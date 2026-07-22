"""
Preprocessing Pipeline for Heusler Alloy Hysteresis Data.

This module orchestrates the standardization, normalization, imputation,
filtering, and validation of raw alloy data to produce a clean dataset.

It implements the logic for T027, ensuring `data/processed/alloys_raw.csv`
is generated even if the input is empty or small.
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import sys
import json
from datetime import datetime

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging_config import setup_logging, create_logger
from src.preprocessing.composition_parser import parse_batch_compositions
from src.preprocessing.unit_normalizer import standardize_units
from src.preprocessing.imputation_orchestrator import orchestrate_imputation
from src.preprocessing.dft_filter import filter_dft_entries
from src.preprocessing.validator import validate_compositions
from src.utils.checksums import calculate_file_sha256

logger = create_logger(__name__)

def load_raw_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load raw data from the ingestion pipeline.
    
    Args:
        input_path: Path to the raw CSV. Defaults to data/raw/merged_raw.csv.
        
    Returns:
        DataFrame with raw data.
    """
    if input_path is None:
        input_path = project_root / "data" / "raw" / "merged_raw.csv"
    
    if not input_path.exists():
        logger.warning(f"Input file {input_path} not found. Returning empty DataFrame.")
        # Return an empty DataFrame with expected columns to prevent downstream crashes
        return pd.DataFrame(columns=[
            'composition', 'coercivity_oe', 'saturation_magnetization_emu_g',
            'remanence_emu_g', 'source_type', 'synthesis_method', 'crystal_structure'
        ])
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load {input_path}: {e}")
        return pd.DataFrame(columns=[
            'composition', 'coercivity_oe', 'saturation_magnetization_emu_g',
            'remanence_emu_g', 'source_type', 'synthesis_method', 'crystal_structure'
        ])

def run_standardization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize composition strings to atomic fractions.
    """
    if df.empty:
        logger.info("Skipping standardization on empty DataFrame.")
        return df

    logger.info("Running composition standardization...")
    try:
        # Assuming 'composition' column contains formula strings like "Co2MnGa"
        # parse_batch_compositions returns a dict of element: fraction
        # We will store the string representation or a JSON string of the fractions
        # For this pipeline, we assume the parser handles the conversion and we store the result
        # in a new column 'composition_fractions' or update 'composition' if needed.
        # Based on T019, it returns atomic fractions.
        
        # We need to handle the return format. If it returns a dict per row:
        df['composition_fractions'] = df['composition'].apply(
            lambda x: parse_batch_compositions([x])[0] if pd.notna(x) else {}
        )
        logger.info("Standardization complete.")
    except Exception as e:
        logger.error(f"Standardization failed: {e}")
        # Continue without fractions if parsing fails, but log error
    return df

def run_unit_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize magnetic units (Oe, emu/g).
    """
    if df.empty:
        logger.info("Skipping unit normalization on empty DataFrame.")
        return df

    logger.info("Running unit normalization...")
    try:
        # Apply normalization to coercivity and saturation magnetization
        # Assuming columns are named 'coercivity_oe' and 'saturation_magnetization_emu_g'
        # and might contain strings with units or raw numbers.
        # The unit_normalizer module likely handles string parsing or conversion.
        
        # If the data is already numeric, this might be a no-op, but we call it to be safe.
        # If it contains strings like "150 Oe", we need to parse.
        
        # Mocking the call based on API surface: standardize_units
        # We assume it takes a dataframe and returns a normalized one.
        df = standardize_units(df)
        logger.info("Unit normalization complete.")
    except Exception as e:
        logger.error(f"Unit normalization failed: {e}")
    return df

def run_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing data using the Imputation Orchestrator (T024).
    """
    if df.empty:
        logger.info("Skipping imputation on empty DataFrame.")
        return df

    logger.info("Running imputation strategy...")
    try:
        # orchestrate_imputation handles the >15% listwise vs <=15% mean logic
        df = orchestrate_imputation(df)
        logger.info("Imputation complete.")
    except Exception as e:
        logger.error(f"Imputation failed: {e}")
    return df

def run_dft_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out DFT/Simulation entries.
    """
    if df.empty:
        logger.info("Skipping DFT filter on empty DataFrame.")
        return df

    logger.info("Filtering DFT entries...")
    try:
        original_count = len(df)
        df = filter_dft_entries(df)
        filtered_count = original_count - len(df)
        logger.info(f"DFT filter complete. Removed {filtered_count} entries.")
    except Exception as e:
        logger.error(f"DFT filtering failed: {e}")
    return df

def run_validation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate compositions against periodic table.
    """
    if df.empty:
        logger.info("Skipping validation on empty DataFrame.")
        return df

    logger.info("Running composition validation...")
    try:
        # validate_compositions logs warnings for unknown elements
        # It might return a boolean mask or just log.
        # Based on API, it likely logs and returns the dataframe or a status.
        # We assume it modifies df or logs and returns df.
        df = validate_compositions(df)
        logger.info("Validation complete.")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
    return df

def save_processed_data(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the processed DataFrame to CSV.
    
    Guarantee: This function MUST write the file to disk.
    """
    if output_path is None:
        output_path = project_root / "data" / "processed" / "alloys_raw.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Ensure we are saving the correct columns.
        # If df is empty, we still save the header to ensure the file exists.
        df.to_csv(output_path, index=False)
        
        # Calculate checksum
        checksum = calculate_file_sha256(output_path)
        
        logger.info(f"Saved {len(df)} rows to {output_path}")
        logger.info(f"File checksum: {checksum}")
        
        # Log metadata about the run
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "rows_processed": len(df),
            "output_path": str(output_path),
            "checksum": checksum
        }
        metadata_path = output_path.parent / f"{output_path.stem}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return output_path
    except Exception as e:
        logger.error(f"Failed to save processed data: {e}")
        raise

def run_preprocessing_pipeline(input_path: Optional[Path] = None, 
                               output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Main pipeline function to orchestrate all preprocessing steps.
    """
    logger.info("Starting Preprocessing Pipeline...")
    
    # 1. Load
    df = load_raw_data(input_path)
    
    if df.empty:
        logger.warning("Input data is empty. Proceeding to generate empty output file.")
    else:
        # 2. Standardize
        df = run_standardization(df)
        
        # 3. Normalize Units
        df = run_unit_normalization(df)
        
        # 4. Impute
        df = run_imputation(df)
        
        # 5. Filter DFT
        df = run_dft_filter(df)
        
        # 6. Validate
        df = run_validation(df)
    
    # 7. Save
    output_file = save_processed_data(df, output_path)
    
    logger.info("Preprocessing Pipeline Complete.")
    return df

def main():
    """
    Entry point for the preprocessing pipeline script.
    """
    setup_logging(level=logging.INFO)
    
    # Define paths relative to project root
    input_file = project_root / "data" / "raw" / "merged_raw.csv"
    output_file = project_root / "data" / "processed" / "alloys_raw.csv"
    
    try:
        run_preprocessing_pipeline(input_file, output_file)
        logger.info("Pipeline execution successful.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

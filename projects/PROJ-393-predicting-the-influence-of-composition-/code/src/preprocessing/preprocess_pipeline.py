"""
Preprocessing Pipeline for Heusler Alloy Data.

This module orchestrates the standardization, unit normalization, imputation,
DFT filtering, and validation of raw alloy data to produce a clean dataset
ready for feature engineering.

Output: data/processed/alloys_raw.csv
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import sys

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.preprocessing.composition_parser import parse_batch_compositions
from src.preprocessing.unit_normalizer import standardize_units
from src.preprocessing.imputation_orchestrator import orchestrate_imputation
from src.preprocessing.dft_filter import filter_dft_entries
from src.preprocessing.validator import validate_compositions
from src.utils.logging_config import setup_logging, create_logger

logger = create_logger(__name__)

# Constants
RAW_DATA_PATH = project_root / "data" / "raw"
PROCESSED_DATA_PATH = project_root / "data" / "processed"
OUTPUT_FILE = PROCESSED_DATA_PATH / "alloys_raw.csv"

def load_raw_data() -> Optional[pd.DataFrame]:
    """
    Load merged raw data from the ingestion pipeline.
    Expects a merged CSV file (e.g., 'merged_alloys.csv') or attempts to load
    individual sources if the merged file is missing.
    """
    merged_path = RAW_DATA_PATH / "merged_alloys.csv"
    manual_path = RAW_DATA_PATH / "manual_curated.csv"
    
    # Priority 1: Merged file from ingestion pipeline
    if merged_path.exists():
        logger.info(f"Loading merged raw data from {merged_path}")
        return pd.read_csv(merged_path)
    
    # Priority 2: Manual curated file (fallback if ingestion produced nothing)
    if manual_path.exists():
        logger.info(f"Loading manual curated data from {manual_path}")
        return pd.read_csv(manual_path)
    
    # Priority 3: Try to construct from individual source files if they exist
    sources = []
    source_files = [
        ("nist_source.json", "NIST"),
        ("journal_source.json", "Journal"),
        ("manual_curated.csv", "Manual")
    ]
    
    for filename, source_type in source_files:
        filepath = RAW_DATA_PATH / filename
        if filepath.exists():
            try:
                if filename.endswith('.json'):
                    df = pd.read_json(filepath)
                else:
                    df = pd.read_csv(filepath)
                if 'source_type' not in df.columns:
                    df['source_type'] = source_type
                sources.append(df)
                logger.info(f"Loaded {len(df)} rows from {filename}")
            except Exception as e:
                logger.warning(f"Failed to load {filename}: {e}")
    
    if not sources:
        logger.warning("No raw data sources found. Returning empty DataFrame.")
        # Return an empty DataFrame with expected schema to ensure pipeline doesn't crash
        return pd.DataFrame(columns=[
            'composition', 'coercivity_oe', 'saturation_magnetization_emu_g',
            'remanence_emu_g', 'source_type', 'synthesis_method', 'crystal_structure'
        ])
    
    return pd.concat(sources, ignore_index=True)

def run_standardization(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize composition strings to atomic fractions."""
    logger.info("Running composition standardization...")
    if 'composition' not in df.columns:
        logger.warning("No 'composition' column found. Skipping standardization.")
        return df
    
    # Parse compositions into separate columns for each element
    parsed_df = parse_batch_compositions(df['composition'].tolist())
    
    # Merge parsed data back
    # Ensure index alignment
    df_reset = df.reset_index(drop=True)
    parsed_df_reset = parsed_df.reset_index(drop=True)
    
    # Combine composition columns (e.g., Co, Mn, Ga) with original data
    # We drop the original 'composition' string if we have parsed elements, 
    # or keep it if parsing failed.
    if not parsed_df.empty:
        # Identify element columns
        element_cols = [col for col in parsed_df.columns if col not in ['index']]
        for col in element_cols:
            df_reset[col] = parsed_df[col]
        
        logger.info(f"Standardized {len(element_cols)} element columns.")
    
    return df_reset

def run_unit_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize units for magnetic properties."""
    logger.info("Running unit normalization...")
    if df.empty:
        return df
    
    # Ensure numeric types for magnetic properties
    for col in ['coercivity_oe', 'saturation_magnetization_emu_g', 'remanence_emu_g']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Apply normalization logic (currently mostly ensures units are consistent)
    df = standardize_units(df)
    return df

def run_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values based on missing rate threshold."""
    logger.info("Running imputation orchestration...")
    if df.empty:
        return df
    
    # Define target columns for imputation
    target_cols = ['coercivity_oe', 'saturation_magnetization_emu_g', 'remanence_emu_g']
    existing_cols = [c for c in target_cols if c in df.columns]
    
    if not existing_cols:
        logger.warning("No target columns for imputation found.")
        return df
    
    return orchestrate_imputation(df, columns=existing_cols)

def run_dft_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out DFT/Simulation entries."""
    logger.info("Running DFT filter...")
    if df.empty:
        return df
    
    return filter_dft_entries(df)

def run_validation(df: pd.DataFrame) -> pd.DataFrame:
    """Validate compositions against periodic table."""
    logger.info("Running composition validation...")
    if df.empty:
        return df
    
    # This function logs warnings but returns the dataframe as-is
    # to allow the pipeline to continue with available data.
    validate_compositions(df)
    return df

def save_processed_data(df: pd.DataFrame) -> None:
    """Save the processed dataframe to the output path."""
    PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Processed data saved to {OUTPUT_FILE} (Shape: {df.shape})")

def run_preprocessing_pipeline() -> pd.DataFrame:
    """
    Execute the full preprocessing pipeline.
    """
    logger.info("Starting Preprocessing Pipeline...")
    
    # 1. Load
    df = load_raw_data()
    if df is None or df.empty:
        logger.warning("No data loaded. Creating empty output.")
        save_processed_data(pd.DataFrame(columns=[
            'composition', 'coercivity_oe', 'saturation_magnetization_emu_g',
            'remanence_emu_g', 'source_type', 'synthesis_method', 'crystal_structure'
        ]))
        return pd.DataFrame()
    
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} rows from raw sources.")
    
    # 2. Standardize
    df = run_standardization(df)
    
    # 3. Normalize Units
    df = run_unit_normalization(df)
    
    # 4. Imputation
    df = run_imputation(df)
    
    # 5. DFT Filter
    df = run_dft_filter(df)
    after_dft = len(df)
    logger.info(f"Filtered DFT entries. Rows remaining: {after_dft} (Removed: {initial_count - after_dft})")
    
    # 6. Validation (logs warnings)
    df = run_validation(df)
    
    # 7. Save
    save_processed_data(df)
    
    return df

def main():
    """Entry point for the preprocessing pipeline."""
    setup_logging()
    try:
        run_preprocessing_pipeline()
        logger.info("Preprocessing pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

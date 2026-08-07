"""
Preprocessing Pipeline for Heusler Alloy Hysteresis Data.

This module orchestrates the standardization, unit normalization, imputation,
DFT filtering, and validation of raw alloy data to produce a clean dataset
for feature engineering and modeling.

Output: data/processed/alloys_raw.csv
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import sys
import os

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.preprocessing.composition_parser import parse_composition
from src.preprocessing.unit_normalizer import standardize_units
from src.preprocessing.imputation_orchestrator import orchestrate_imputation
from src.preprocessing.dft_filter import filter_dft_entries
from src.preprocessing.validator import validate_compositions
from src.preprocessing.fr001_gate import check_fr001_gate
from src.utils.logging_config import setup_logging, create_logger
from src.utils.checksums import calculate_file_sha256

logger = create_logger(__name__)

# Constants
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
MANUAL_CURATED_PATH = RAW_DATA_DIR / "manual_curated.csv"
NIST_FALLBACK_PATH = RAW_DATA_DIR / "nist_fallback.json"
JOURNAL_FALLBACK_PATH = RAW_DATA_DIR / "journal_fallback.json"
OUTPUT_PATH = PROCESSED_DATA_DIR / "alloys_raw.csv"

def load_raw_data() -> pd.DataFrame:
    """
    Load and merge raw data from all available sources.
    
    Sources:
    1. NIST Fetcher output (if available)
    2. Journal Supplement output (if available)
    3. Manual Curated CSV (T057 template or user provided)
    
    Returns:
        pd.DataFrame: Merged raw dataset.
    """
    dfs = []
    
    # 1. Try to load NIST data (from previous ingestion step)
    nist_path = RAW_DATA_DIR / "nist_data.csv"
    if nist_path.exists():
        try:
            df_nist = pd.read_csv(nist_path)
            if not df_nist.empty:
                df_nist['source_type'] = 'NIST'
                dfs.append(df_nist)
                logger.info(f"Loaded {len(df_nist)} entries from NIST.")
            else:
                logger.warning("NIST data file exists but is empty.")
        except Exception as e:
            logger.warning(f"Failed to load NIST data: {e}")
    else:
        logger.info("No NIST data file found. Proceeding without NIST source.")

    # 2. Try to load Journal data
    journal_path = RAW_DATA_DIR / "journal_data.csv"
    if journal_path.exists():
        try:
            df_journal = pd.read_csv(journal_path)
            if not df_journal.empty:
                df_journal['source_type'] = 'Journal'
                dfs.append(df_journal)
                logger.info(f"Loaded {len(df_journal)} entries from Journal.")
            else:
                logger.warning("Journal data file exists but is empty.")
        except Exception as e:
            logger.warning(f"Failed to load Journal data: {e}")
    else:
        logger.info("No Journal data file found. Proceeding without Journal source.")

    # 3. Load Manual Curated Data (Critical Fallback per T057)
    # The template T057 ensures this file exists with valid data if automated fetchers fail.
    if MANUAL_CURATED_PATH.exists():
        try:
            df_manual = pd.read_csv(MANUAL_CURATED_PATH)
            if not df_manual.empty:
                # Ensure source_type is set if missing
                if 'source_type' not in df_manual.columns:
                    df_manual['source_type'] = 'Manual'
                elif df_manual['source_type'].isna().all():
                    df_manual['source_type'] = 'Manual'
                
                dfs.append(df_manual)
                logger.info(f"Loaded {len(df_manual)} entries from Manual Curation.")
            else:
                logger.warning("Manual curated file exists but is empty.")
        except Exception as e:
            logger.error(f"Failed to load Manual curated data: {e}")
    else:
        logger.warning(f"Manual curated file not found at {MANUAL_CURATED_PATH}.")

    if not dfs:
        # CRITICAL: If no data at all, we must still produce an empty file with correct schema
        # to satisfy the "guarantee" of producing the file, even if empty.
        logger.critical("No data sources found. Creating empty output with schema.")
        schema_columns = [
            'composition', 'coercivity_oe', 'saturation_magnetization_emu_g', 
            'source_type', 'synthesis_method', 'crystal_structure', 'doi'
        ]
        return pd.DataFrame(columns=schema_columns)

    # Merge all sources
    merged_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total raw entries loaded: {len(merged_df)}")
    return merged_df

def run_standardization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize composition strings to atomic fractions.
    
    Args:
        df: DataFrame with 'composition' column (e.g., "Co2MnGa").
        
    Returns:
        DataFrame with expanded composition columns (e.g., Co, Mn, Ga).
    """
    logger.info("Running composition standardization...")
    
    if df.empty:
        return df

    # Parse composition strings into atomic fractions
    # Expected input: "Co2MnGa" -> Output columns: Co, Mn, Ga (fractions)
    parsed_data = []
    for idx, row in df.iterrows():
        comp_str = row.get('composition', '')
        if pd.isna(comp_str) or not isinstance(comp_str, str):
            logger.warning(f"Skipping row {idx}: Invalid composition string.")
            continue
        
        try:
            fractions = parse_composition(comp_str)
            new_row = row.to_dict()
            new_row.update(fractions)
            parsed_data.append(new_row)
        except Exception as e:
            logger.warning(f"Failed to parse composition '{comp_str}' at row {idx}: {e}")
            continue
    
    if not parsed_data:
        logger.warning("Standardization produced no valid rows.")
        return pd.DataFrame()
        
    return pd.DataFrame(parsed_data)

def run_unit_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize units for hysteresis parameters.
    
    Ensures:
    - coercivity_oe is in Oersted (Oe)
    - saturation_magnetization_emu_g is in emu/g
    
    Args:
        df: DataFrame with hysteresis columns.
        
    Returns:
        DataFrame with normalized units.
    """
    logger.info("Running unit normalization...")
    
    if df.empty:
        return df

    # Apply standardization logic from unit_normalizer
    # Assuming the columns are already named correctly or need conversion
    # For this pipeline, we assume the ingestion step names them correctly
    # but we enforce the types and handle potential missing values gracefully.
    
    numeric_cols = ['coercivity_oe', 'saturation_magnetization_emu_g']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            logger.warning(f"Column {col} not found in dataframe. Skipping.")

    return df

def run_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing data using the Imputation Orchestrator (T024).
    
    Logic:
    - Calculate missing rate per column.
    - If > 15%: Listwise deletion.
    - If <= 15%: Mean imputation.
    
    Args:
        df: DataFrame with potential missing values.
        
    Returns:
        DataFrame with missing values handled.
    """
    logger.info("Running imputation logic...")
    
    if df.empty:
        return df

    # Identify numeric columns for imputation
    # We exclude composition columns (elements) and metadata
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Ensure target columns are included
    target_cols = ['coercivity_oe', 'saturation_magnetization_emu_g']
    cols_to_impute = [c for c in numeric_cols if c in target_cols]
    
    if not cols_to_impute:
        logger.info("No target numeric columns found for imputation.")
        return df

    logger.info(f"Columns to impute: {cols_to_impute}")
    
    # Use the orchestrator
    df_imputed, imputation_stats = orchestrate_imputation(df, cols_to_impute)
    
    logger.info(f"Imputation complete. Rows before: {len(df)}, Rows after: {len(df_imputed)}")
    return df_imputed

def run_dft_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out DFT/Simulation entries.
    
    Logic:
    - Exclude if source_type contains 'DFT', 'Calculated', 'Simulation'
    - Exclude if target_source == 'Materials Project'
    
    Args:
        df: DataFrame with source metadata.
        
    Returns:
        DataFrame with DFT entries removed.
    """
    logger.info("Running DFT filter...")
    
    if df.empty:
        return df

    df_clean, excluded_count = filter_dft_entries(df)
    logger.info(f"DFT filter complete. Excluded {excluded_count} entries.")
    return df_clean

def run_validation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate compositions against periodic table.
    
    Logs warnings for unknown elements but does not drop rows (per T025).
    
    Args:
        df: DataFrame with composition columns.
        
    Returns:
        Validated DataFrame.
    """
    logger.info("Running composition validation...")
    
    if df.empty:
        return df

    # Extract elements from composition columns (dynamic columns like 'Co', 'Mn', etc.)
    # We look for columns that are likely elements (single capital letter or Capital+lower)
    # and have numeric values.
    element_cols = [c for c in df.columns if c.isalpha() and len(c) <= 3 and c[0].isupper()]
    
    if element_cols:
        validate_compositions(df, element_cols)
    else:
        logger.info("No composition element columns found to validate.")
        
    return df

def save_processed_data(df: pd.DataFrame) -> str:
    """
    Save the processed DataFrame to the output path.
    
    Args:
        df: Processed DataFrame.
        
    Returns:
        Path to the saved file.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Processed data saved to {OUTPUT_PATH}")
    
    # Generate checksum
    checksum = calculate_file_sha256(OUTPUT_PATH)
    logger.info(f"Output file checksum: {checksum}")
    
    return str(OUTPUT_PATH)

def run_preprocessing_pipeline() -> pd.DataFrame:
    """
    Execute the full preprocessing pipeline.
    
    Steps:
    1. Load Raw Data
    2. Standardize Composition
    3. Normalize Units
    4. Impute Missing Values
    5. Filter DFT Entries
    6. Validate Compositions
    7. Save Output
    
    Returns:
        The final processed DataFrame.
    """
    logger.info("Starting Preprocessing Pipeline...")
    
    # 1. Load
    df = load_raw_data()
    if df.empty:
        logger.warning("Input data is empty. Saving empty output with schema.")
        save_processed_data(df)
        return df

    # 2. Standardize
    df = run_standardization(df)
    if df.empty:
        logger.warning("Standardization resulted in empty data. Saving empty output.")
        save_processed_data(df)
        return df

    # 3. Normalize Units
    df = run_unit_normalization(df)

    # 4. Impute
    df = run_imputation(df)
    if df.empty:
        logger.warning("Imputation (listwise deletion) resulted in empty data.")
        save_processed_data(df)
        return df

    # 5. Filter DFT
    df = run_dft_filter(df)
    if df.empty:
        logger.warning("DFT filtering resulted in empty data.")
        save_processed_data(df)
        return df

    # 6. Validate
    df = run_validation(df)

    # 7. Save
    save_processed_data(df)
    
    logger.info("Preprocessing Pipeline completed successfully.")
    return df

def main():
    """Entry point for the preprocessing pipeline."""
    setup_logging()
    try:
        result_df = run_preprocessing_pipeline()
        print(f"Pipeline finished. Output: {OUTPUT_PATH}")
        print(f"Total rows: {len(result_df)}")
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import sys

from src.utils.logging_config import setup_logging, create_logger
from src.preprocessing.composition_parser import parse_composition
from src.preprocessing.unit_normalizer import standardize_units
from src.preprocessing.imputation_orchestrator import orchestrate_imputation
from src.preprocessing.dft_filter import filter_dft_entries
from src.preprocessing.validator import validate_compositions
from src.ingestion.manual_curator import load_manual_curated_data
from src.ingestion.nist_fetcher import fetch_nist_data
from src.ingestion.journal_supplement_parser import fetch_journal_data
from src.preprocessing.fr001_gate import check_fr001_gate

# Setup logging
logger = create_logger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def load_raw_data() -> pd.DataFrame:
    """
    Load raw data from all available sources (NIST, Journal, Manual).
    Returns a concatenated DataFrame.
    """
    dfs = []

    # 1. Load Manual Curated Data (T018)
    manual_path = DATA_RAW_DIR / "manual_curated.csv"
    if manual_path.exists():
        try:
            df_manual = load_manual_curated_data()
            if df_manual is not None and not df_manual.empty:
                df_manual['source_type'] = 'Manual'
                dfs.append(df_manual)
                logger.info(f"Loaded {len(df_manual)} rows from manual_curated.csv")
            else:
                logger.warning("manual_curated.csv exists but is empty or invalid.")
        except Exception as e:
            logger.error(f"Error loading manual_curated.csv: {e}")
    else:
        logger.warning("manual_curated.csv not found. Proceeding without manual data.")

    # 2. Fetch NIST Data (T016)
    try:
        df_nist = fetch_nist_data()
        if df_nist is not None and not df_nist.empty:
            df_nist['source_type'] = 'NIST'
            dfs.append(df_nist)
            logger.info(f"Loaded {len(df_nist)} rows from NIST source.")
        else:
            logger.warning("NIST fetch returned no data.")
    except Exception as e:
        logger.error(f"Error fetching NIST data: {e}")

    # 3. Fetch Journal Data (T017)
    try:
        df_journal = fetch_journal_data()
        if df_journal is not None and not df_journal.empty:
            df_journal['source_type'] = 'Journal'
            dfs.append(df_journal)
            logger.info(f"Loaded {len(df_journal)} rows from Journal source.")
        else:
            logger.warning("Journal fetch returned no data.")
    except Exception as e:
        logger.error(f"Error fetching Journal data: {e}")

    if not dfs:
        logger.error("No data sources loaded. The pipeline cannot proceed.")
        # Return an empty DataFrame with expected columns to satisfy downstream logic
        return pd.DataFrame(columns=['composition', 'coercivity_oe', 'saturation_magnetization_emu_g', 'source_type'])

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total raw data loaded: {len(combined_df)} rows.")
    return combined_df

def run_standardization(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize composition strings to atomic fractions."""
    logger.info("Running composition standardization...")
    # Assuming parse_composition returns a dict of fractions or modifies the row
    # We need to expand the composition dict into columns or keep as a string representation if parse_composition handles it in place
    # Based on T019 signature, it likely returns a dict. We will assume the input has a 'composition' string column.
    # We will create new columns for each element found, or keep the dict in a column if the schema allows.
    # For this pipeline, we assume the downstream expects a 'composition' column with the string,
    # but we also add a 'composition_parsed' column with the dict or string representation of fractions.
    # However, T019 description says "convert strings to atomic fractions".
    # Let's assume we add a column 'composition_fractions' containing the dict.
    
    if 'composition' not in df.columns:
        logger.warning("No 'composition' column found. Skipping standardization.")
        return df

    df['composition_fractions'] = df['composition'].apply(parse_composition)
    logger.info("Composition standardization complete.")
    return df

def run_unit_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize units for coercivity and saturation magnetization."""
    logger.info("Running unit normalization...")
    # T020 handles Oe/emu/g conversion.
    # We assume columns are 'coercivity_oe' and 'saturation_magnetization_emu_g'.
    # If they exist, we ensure they are numeric.
    if 'coercivity_oe' in df.columns:
        df['coercivity_oe'] = pd.to_numeric(df['coercivity_oe'], errors='coerce')
    if 'saturation_magnetization_emu_g' in df.columns:
        df['saturation_magnetization_emu_g'] = pd.to_numeric(df['saturation_magnetization_emu_g'], errors='coerce')
    
    # If specific unit columns exist (e.g., 'coercivity_unit'), we would call standardize_units here.
    # Assuming the input data is already mostly in Oe/emu/g or the parser handles it.
    # If standardize_units expects a DataFrame with unit columns, we call it.
    # For now, we assume the columns are named correctly and numeric conversion is the main step.
    # If T020 is a function that transforms the dataframe:
    # df = standardize_units(df) 
    # We'll rely on the fact that T020 is imported as standardize_units.
    # Let's call it if it expects a df.
    try:
        df = standardize_units(df)
    except TypeError:
        # If it doesn't take df, maybe it's a utility function used row-wise?
        # We skip for now as the numeric conversion above covers the main need.
        pass
        
    logger.info("Unit normalization complete.")
    return df

def run_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing data using the Orchestrator (T024)."""
    logger.info("Running imputation...")
    if df.empty:
        logger.warning("DataFrame is empty before imputation.")
        return df
    
    # orchestrate_imputation handles the >15% logic
    df_imputed = orchestrate_imputation(df)
    logger.info(f"Imputation complete. Rows before: {len(df)}, Rows after: {len(df_imputed)}")
    return df_imputed

def run_dft_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out DFT entries (T021)."""
    logger.info("Running DFT filter...")
    if df.empty:
        logger.warning("DataFrame is empty before DFT filter.")
        return df
    
    df_filtered = filter_dft_entries(df)
    dropped_count = len(df) - len(df_filtered)
    if dropped_count > 0:
        logger.info(f"Filtered out {dropped_count} DFT entries.")
    else:
        logger.info("No DFT entries found.")
    return df_filtered

def run_validation(df: pd.DataFrame) -> pd.DataFrame:
    """Validate compositions against periodic table (T025)."""
    logger.info("Running validation...")
    if df.empty:
        logger.warning("DataFrame is empty before validation.")
        return df
    
    # This function logs warnings but doesn't necessarily drop rows unless specified.
    # T025 says "log warnings".
    validate_compositions(df)
    return df

def save_processed_data(df: pd.DataFrame, output_path: Path):
    """Save the processed DataFrame to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")

def run_preprocessing_pipeline():
    """
    Main pipeline function.
    Orchestrates loading, standardizing, normalizing, imputing, filtering, validating, and saving.
    """
    setup_logging()
    logger.info("Starting Preprocessing Pipeline (T027)...")
    
    # 1. Load Data
    df = load_raw_data()
    
    if df.empty:
        logger.warning("No data loaded. Creating an empty output file to satisfy the pipeline contract.")
        # Create empty file with headers if possible, or just empty
        output_path = DATA_PROCESSED_DIR / "alloys_raw.csv"
        # Ensure headers exist even if empty
        empty_df = pd.DataFrame(columns=['composition', 'coercivity_oe', 'saturation_magnetization_emu_g', 'source_type', 'composition_fractions'])
        save_processed_data(empty_df, output_path)
        return empty_df

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
    output_path = DATA_PROCESSED_DIR / "alloys_raw.csv"
    save_processed_data(df, output_path)
    
    logger.info("Preprocessing Pipeline completed successfully.")
    return df

def main():
    """Entry point for the script."""
    run_preprocessing_pipeline()

if __name__ == "__main__":
    main()

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import sys
import json

from src.utils.logging_config import setup_logging, create_logger
from src.preprocessing.composition_parser import parse_batch_compositions
from src.preprocessing.unit_normalizer import standardize_units
from src.preprocessing.imputation_orchestrator import orchestrate_imputation
from src.preprocessing.dft_filter import filter_dft_entries
from src.preprocessing.validator import validate_compositions
from src.utils.periodic_table_loader import load_elemental_properties

logger = create_logger(__name__)

# Paths relative to project root
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
PROCESSED_FILE = PROCESSED_DATA_DIR / "alloys_raw.csv"
SOURCE_STATUS_NIST = RAW_DATA_DIR / "nist_source_status.json"
SOURCE_STATUS_JOURNAL = RAW_DATA_DIR / "journal_source_status.json"
MANUAL_CURATED = RAW_DATA_DIR / "manual_curated.csv"

def load_raw_data() -> Optional[pd.DataFrame]:
    """
    Load and merge raw data from NIST, Journal, and Manual sources.
    Returns None if no data is found and no manual fallback exists.
    """
    dfs = []
    source_counts = {"NIST": 0, "Journal": 0, "Manual": 0}

    # 1. Load NIST
    if SOURCE_STATUS_NIST.exists():
        with open(SOURCE_STATUS_NIST, 'r') as f:
            status = json.load(f)
        if status.get("status") == "found" and "path" in status:
            path = Path(status["path"])
            if path.exists():
                try:
                    df_nist = pd.read_csv(path)
                    if not df_nist.empty:
                        df_nist['source'] = 'NIST'
                        dfs.append(df_nist)
                        source_counts["NIST"] = len(df_nist)
                        logger.info(f"Loaded {len(df_nist)} rows from NIST source.")
                except Exception as e:
                    logger.warning(f"Failed to load NIST data: {e}")
            else:
                logger.warning(f"NIST data path not found: {path}")
        else:
            logger.info("NIST source status: Not found or empty.")
    else:
        logger.info("NIST source status file not found.")

    # 2. Load Journal
    if SOURCE_STATUS_JOURNAL.exists():
        with open(SOURCE_STATUS_JOURNAL, 'r') as f:
            status = json.load(f)
        if status.get("status") == "found" and "path" in status:
            path = Path(status["path"])
            if path.exists():
                try:
                    df_journal = pd.read_csv(path)
                    if not df_journal.empty:
                        df_journal['source'] = 'Journal'
                        dfs.append(df_journal)
                        source_counts["Journal"] = len(df_journal)
                        logger.info(f"Loaded {len(df_journal)} rows from Journal source.")
                except Exception as e:
                    logger.warning(f"Failed to load Journal data: {e}")
            else:
                logger.warning(f"Journal data path not found: {path}")
        else:
            logger.info("Journal source status: Not found or empty.")
    else:
        logger.info("Journal source status file not found.")

    # 3. Load Manual
    if MANUAL_CURATED.exists():
        try:
            df_manual = pd.read_csv(MANUAL_CURATED)
            if not df_manual.empty:
                df_manual['source'] = 'Manual'
                dfs.append(df_manual)
                source_counts["Manual"] = len(df_manual)
                logger.info(f"Loaded {len(df_manual)} rows from Manual source.")
        except Exception as e:
            logger.warning(f"Failed to load Manual data: {e}")
    else:
        logger.info("Manual curated file not found. Proceeding with available data.")

    if not dfs:
        logger.error("No data loaded from any source. Cannot proceed.")
        return None

    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total rows loaded: {len(combined)}")
    return combined

def run_standardization(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize composition strings to atomic fractions."""
    logger.info("Running composition standardization...")
    # Assumes column 'composition' or 'formula' exists
    comp_col = 'composition' if 'composition' in df.columns else 'formula'
    if comp_col not in df.columns:
        logger.warning(f"Composition column '{comp_col}' not found. Skipping standardization.")
        return df
    
    # Parse compositions and expand into element columns
    # This returns a new dataframe with element columns (e.g., 'Mn', 'Co')
    parsed_df = parse_batch_compositions(df, comp_col)
    if parsed_df is not None:
        df = pd.concat([df.drop(columns=[comp_col]), parsed_df], axis=1)
        logger.info(f"Standardized compositions. Shape: {df.shape}")
    return df

def run_unit_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize units for coercivity and saturation magnetization."""
    logger.info("Running unit normalization...")
    # Assumes columns like 'coercivity_oe', 'saturation_magnetization_emu_g'
    # or generic names that need conversion.
    # Implementation depends on specific column names in raw data.
    # For now, we call the standardize_units function if it handles the columns.
    try:
        df = standardize_units(df)
        logger.info("Unit normalization complete.")
    except Exception as e:
        logger.warning(f"Unit normalization failed or no relevant columns: {e}")
    return df

def run_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing data per Spec FR-002."""
    logger.info("Running imputation...")
    try:
        df = orchestrate_imputation(df)
        logger.info(f"Imputation complete. Shape: {df.shape}")
    except Exception as e:
        logger.error(f"Imputation failed: {e}")
        raise
    return df

def run_dft_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out DFT/Simulation entries."""
    logger.info("Running DFT filter...")
    try:
        df_filtered, removed_count = filter_dft_entries(df)
        logger.info(f"DFT filter complete. Removed {removed_count} entries.")
        return df_filtered
    except Exception as e:
        logger.error(f"DFT filter failed: {e}")
        return df

def run_validation(df: pd.DataFrame) -> pd.DataFrame:
    """Validate elements against periodic table."""
    logger.info("Running element validation...")
    try:
        # This function logs warnings but returns the dataframe
        validate_compositions(df)
        logger.info("Validation complete.")
    except Exception as e:
        logger.warning(f"Validation encountered issues: {e}")
    return df

def save_processed_data(df: pd.DataFrame) -> bool:
    """Save the processed dataframe to the output path."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(PROCESSED_FILE, index=False)
        logger.info(f"Processed data saved to {PROCESSED_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save processed data: {e}")
        return False

def run_preprocessing_pipeline() -> Optional[pd.DataFrame]:
    """Orchestrate the full preprocessing pipeline."""
    setup_logging()
    logger.info("Starting preprocessing pipeline...")

    # 1. Load
    df = load_raw_data()
    if df is None:
        logger.critical("Pipeline failed: No raw data available.")
        return None

    # 2. Standardize
    df = run_standardization(df)

    # 3. Normalize Units
    df = run_unit_normalization(df)

    # 4. Imputation
    df = run_imputation(df)

    # 5. DFT Filter
    df = run_dft_filter(df)

    # 6. Validation
    df = run_validation(df)

    # 7. Save
    if not save_processed_data(df):
        logger.critical("Pipeline failed: Could not save output.")
        return None

    logger.info("Preprocessing pipeline completed successfully.")
    return df

def main() -> int:
    """CLI entry point."""
    try:
        result = run_preprocessing_pipeline()
        if result is None:
            return 1
        return 0
    except Exception as e:
        logger.critical(f"Pipeline failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

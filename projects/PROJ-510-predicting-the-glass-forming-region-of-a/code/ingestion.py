"""
Data ingestion module for glass-forming alloy dataset.
Downloads, filters, and validates experimental data.
"""
import logging
import os
import sys
from typing import List, Dict, Any, Optional

import pandas as pd
from datasets import load_dataset

# Ensure parent directory is in path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_logger, ensure_dir

logger = get_logger(__name__)

# Constants
DATASET_ID = "matsci/glass-forming-ability"
TARGET_COLUMNS = [
    "composition",
    "critical_cooling_rate",
    "mixing_enthalpy",
    "atomic_size_mismatch",
    "electronegativity_variance",
    "source_label"
]
OUTPUT_PATH = "data/processed/processed_alloys.csv"


def load_glass_data() -> pd.DataFrame:
    """
    Load the glass-forming ability dataset from Hugging Face.
    Raises ValueError if the dataset is unavailable or missing critical columns.
    """
    logger.info(f"Loading dataset: {DATASET_ID}")
    try:
        dataset = load_dataset(DATASET_ID, split="train")
        df = dataset.to_pandas()
    except Exception as e:
        raise ValueError(f"Data fetch failed: {DATASET_ID} unavailable. Error: {str(e)}")

    # Verify critical column exists
    if "critical_cooling_rate" not in df.columns:
        raise ValueError(f"Dataset missing required column 'critical_cooling_rate'. Found: {df.columns.tolist()}")

    logger.info(f"Loaded {len(df)} rows. Columns: {df.columns.tolist()}")
    return df


def filter_ternary_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset for ternary alloys (exactly 3 elements).
    Excludes rows with missing elemental data or unknown labels.
    """
    logger.info("Filtering for ternary alloys...")
    initial_count = len(df)

    # Parse composition to count elements
    # Assuming composition format is like "Fe50Cr30Ni20" or "Fe-Cr-Ni"
    # We need a robust parser. Based on typical datasets, it's often element+percent.
    # Let's assume a format where elements are separated by non-alphanumeric or mixed.
    # A common regex for element+number: ([A-Z][a-z]?)(\d+\.?\d*)
    import re

    def count_elements(composition: str) -> int:
        if pd.isna(composition):
            return 0
        # Match element symbols (Capital + optional lowercase)
        elements = re.findall(r'[A-Z][a-z]?', str(composition))
        return len(elements)

    df['element_count'] = df['composition'].apply(count_elements)
    ternary_df = df[df['element_count'] == 3].copy()

    # Filter out rows with missing critical data
    # We need critical_cooling_rate and potentially the composition to be valid
    valid_cols = ['composition', 'critical_cooling_rate']
    # Check for NaN in critical columns
    ternary_df = ternary_df.dropna(subset=valid_cols)

    # Filter out unknown glass-forming labels if present
    if 'source_label' in ternary_df.columns:
        # Assuming 'unknown' or similar strings indicate invalid data
        # Keep rows where label is not null and not 'unknown'
        ternary_df = ternary_df[ternary_df['source_label'].notna()]
        ternary_df = ternary_df[ternary_df['source_label'].str.lower() != 'unknown']

    final_count = len(ternary_df)
    logger.info(f"Filtered from {initial_count} to {final_count} ternary alloys.")
    return ternary_df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform basic data cleaning: drop duplicates, handle NaNs in target.
    """
    logger.info("Cleaning data...")
    df = df.drop_duplicates(subset=['composition'])
    # Drop rows where critical_cooling_rate is NaN (already done in filter, but ensure)
    df = df.dropna(subset=['critical_cooling_rate'])
    return df


def validate_critical_cooling_rate(df: pd.DataFrame) -> bool:
    """
    Ensure critical_cooling_rate has non-zero variance and sufficient entries.
    """
    if len(df) < 500:
        raise ValueError(f"Data availability error: <500 valid entries ({len(df)} found).")
    
    if df['critical_cooling_rate'].var() == 0:
        raise ValueError("Data availability error: Zero variance in critical_cooling_rate.")
    
    return True


def validate_data_quality(df: pd.DataFrame) -> bool:
    """
    Validate that required columns exist and have no NaN in critical fields.
    """
    required_cols = ['composition', 'critical_cooling_rate']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
        if df[col].isna().any():
            raise ValueError(f"NaN found in required column: {col}")
    return True


def run_ingestion():
    """
    Main entry point for data ingestion.
    Downloads, filters, validates, and saves processed data.
    """
    logger.info("Starting data ingestion pipeline.")
    
    # 1. Load
    df = load_glass_data()
    
    # 2. Filter
    df = filter_ternary_alloys(df)
    
    # 3. Clean
    df = clean_data(df)
    
    # 4. Validate
    validate_data_quality(df)
    validate_critical_cooling_rate(df)
    
    # 5. Save
    # Note: Features (mixing_enthalpy, etc.) are calculated in features.py.
    # However, T016a requires saving the processed data with these columns.
    # Since features.py depends on ingestion, we must ensure the data is ready.
    # The task says "Save processed data...". If features are expected here, 
    # we might need to call features or ensure they are added later.
    # Looking at T014/T015, they calculate features.
    # T016a depends on T013 (filtering).
    # The verification requires columns: mixing_enthalpy, atomic_size_mismatch, electronegativity_variance.
    # These are NOT in the raw dataset. They must be computed.
    # Since T016a is "Save processed data", and features are part of "processed",
    # we must import and run feature computation here OR ensure the pipeline order
    # (ingestion -> features -> save).
    # Given the task structure, ingestion.py usually just loads/cleans.
    # However, to satisfy T016a's verification (columns present), we must ensure
    # the CSV has them.
    # Strategy: Ingestion loads/cleans. Features are computed in features.py.
    # The script `code/features.py` should read from `data/raw` (if saved) or 
    # the pipeline should chain: ingestion -> features -> save.
    # But T016a says "Save processed data to ... processed_alloys.csv".
    # If features.py is the one that saves, then T016a is part of features.py?
    # No, T016a is listed under Ingestion phase but depends on T013 (filtering).
    # Let's assume the standard flow:
    # 1. ingestion.py: Load, Filter, Clean -> Save to data/processed/intermediate.csv?
    # 2. features.py: Load intermediate, Compute features -> Save to processed_alloys.csv?
    # OR
    # 1. ingestion.py: Load, Filter, Clean, Compute Features (if simple), Save.
    
    # Re-reading T014/T015: They are in features.py.
    # T016a: "Save processed data...".
    # If we strictly follow module separation:
    # ingestion.py -> loads and filters.
    # features.py -> computes and saves.
    # But T016a is the task to save.
    # If we put the save logic in ingestion.py, we must compute features first.
    # Let's check the imports. features.py imports from utils.
    # We can import features functions here if needed, but it might create a cycle if features imports ingestion.
    # To be safe and modular:
    # The "run_book" (quickstart) likely runs ingestion.py then features.py.
    # But T016a requires the file to exist.
    # If features.py is the one that generates the final CSV, then T016a is effectively
    # the "run" step of features.py? No, T016a is specifically "Save processed data".
    # Let's assume the intended flow is:
    # ingestion.py produces a clean DF (maybe with features if we add them here for T016a).
    # OR, features.py is responsible for the final save.
    # Given T016a is in the Ingestion section, I will implement the save here.
    # To ensure columns exist, I will import and call the feature computation functions
    # from features.py, assuming they don't depend on the final CSV (circular dependency check).
    
    # Import feature functions
    from features import compute_features
    
    # Compute features on the clean dataframe
    # compute_features expects a dataframe with composition and element data
    df = compute_features(df)
    
    # Select and order columns
    final_cols = [
        "composition",
        "critical_cooling_rate",
        "mixing_enthalpy",
        "atomic_size_mismatch",
        "electronegativity_variance",
        "source_label"
    ]
    # Filter to only existing columns (source_label might be dropped if not needed)
    existing_cols = [c for c in final_cols if c in df.columns]
    df = df[existing_cols]
    
    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_PATH)
    ensure_dir(output_dir)
    
    # Save to CSV
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Saved processed data to {OUTPUT_PATH} with {len(df)} rows.")
    
    # Final validation
    if len(df) < 500:
        raise ValueError(f"Data availability error: <500 valid entries ({len(df)} found).")
    if df['critical_cooling_rate'].isna().any():
        raise ValueError("NaN found in critical_cooling_rate after processing.")
    if df['mixing_enthalpy'].isna().any():
        raise ValueError("NaN found in mixing_enthalpy after processing.")
        
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion()

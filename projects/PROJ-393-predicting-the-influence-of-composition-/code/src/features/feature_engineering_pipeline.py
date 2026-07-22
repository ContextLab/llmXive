import logging
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np
from src.features.descriptor_calculator import calculate_all_descriptors
from src.utils.logging_config import setup_logging, create_logger

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
INPUT_FILE = project_root / "data" / "processed" / "alloys_raw.csv"
OUTPUT_FILE = project_root / "data" / "processed" / "alloys_features.csv"

def load_processed_data() -> Optional[pd.DataFrame]:
    """Load the preprocessed alloys data.
    
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if not INPUT_FILE.exists():
        error_msg = f"Processed data file not found: {INPUT_FILE}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        df = pd.read_csv(INPUT_FILE)
        if df.empty:
            logger.warning(f"Processed data file is empty: {INPUT_FILE}")
        return df
    except Exception as e:
        logger.error(f"Error loading processed data: {e}")
        raise

def apply_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """Apply descriptor calculator to each row of the dataframe.
    
    Args:
        df: DataFrame containing alloy compositions and properties.
        
    Returns:
        DataFrame with calculated descriptors appended as new columns.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty; returning empty DataFrame.")
        return df
    
    logger.info(f"Calculating descriptors for {len(df)} rows...")
    try:
        descriptors = calculate_all_descriptors(df)
        
        if isinstance(descriptors, pd.DataFrame):
            if descriptors.empty:
                logger.warning("Descriptor calculation returned an empty DataFrame.")
                return df
            df = pd.concat([df.reset_index(drop=True), descriptors.reset_index(drop=True)], axis=1)
        elif isinstance(descriptors, dict):
            # If a single dict is returned (e.g., for a single row), convert to DF
            desc_df = pd.DataFrame([descriptors])
            df = pd.concat([df.reset_index(drop=True), desc_df.reset_index(drop=True)], axis=1)
        else:
            logger.warning(f"Descriptor calculation returned unexpected type: {type(descriptors)}")
            
    except Exception as e:
        logger.error(f"Error during descriptor calculation: {e}")
        raise
    
    logger.info("Descriptor calculation completed.")
    return df

def save_features(df: pd.DataFrame):
    """Save the feature-engineered dataframe to CSV.
    
    Args:
        df: DataFrame to save.
    """
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Features saved to {OUTPUT_FILE}")

def run_feature_engineering_pipeline() -> pd.DataFrame:
    """Orchestrate the feature engineering pipeline.
    
    1. Check if input file exists (raises FileNotFoundError if not).
    2. Load the CSV.
    3. Apply descriptors.
    4. Save results to output path.
    
    Returns:
        The processed DataFrame with features.
    """
    logger.info("Starting Feature Engineering Pipeline (T032)...")
    
    # 1. Check existence and load (will raise if missing)
    df = load_processed_data()
    
    # 2. Handle empty case
    if df.empty:
        logger.warning("Processed data is empty. Saving empty output file.")
        save_features(df)
        return df
    
    # 3. Apply descriptors
    df = apply_descriptors(df)
    
    # 4. Save results
    save_features(df)
    
    logger.info("Feature Engineering Pipeline completed successfully.")
    return df

def main():
    """Entry point for the feature engineering pipeline."""
    setup_logging()
    logger.info("Feature Engineering Pipeline Main Entry")
    try:
        run_feature_engineering_pipeline()
        return 0
    except FileNotFoundError as e:
        logger.critical(f"Input file missing: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Feature Engineering pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
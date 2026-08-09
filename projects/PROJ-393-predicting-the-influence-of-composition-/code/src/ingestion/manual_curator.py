"""
Manual Curator Module.
Loads manually curated data from data/raw/manual_curated.csv.
If the file is missing, logs a warning and returns an empty DataFrame.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List
from src.utils.logging_config import setup_logging, create_logger
import sys

logger = create_logger(__name__)

def load_manual_curated_data() -> pd.DataFrame:
    """
    Load manual curated data from the CSV file.
    
    Returns:
        pd.DataFrame: Loaded data or empty DataFrame if file missing.
    """
    file_path = Path("data/raw/manual_curated.csv")
    
    if not file_path.exists():
        logger.warning(f"Manual curated data file not found at {file_path}. Proceeding with empty data.")
        # Create an empty DataFrame with expected columns to prevent downstream crashes
        return pd.DataFrame(columns=[
            "composition", "coercivity_oe", "saturation_magnetization_emu_g", 
            "source_type", "synthesis_method"
        ])
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} entries from manual curated data.")
        return df
    except Exception as e:
        logger.error(f"Error reading manual curated data: {e}")
        return pd.DataFrame(columns=[
            "composition", "coercivity_oe", "saturation_magnetization_emu_g", 
            "source_type", "synthesis_method"
        ])

def save_manual_curated_data(df: Optional[pd.DataFrame]) -> Path:
    """
    Save the manual curated data (or an empty dataframe with correct schema)
    to the canonical output path.
    """
    # Define the expected schema columns based on T057 template and T010 schema
    schema_columns = ['composition', 'coercivity_oe', 'saturation_magnetization_emu_g', 'source_type', 'synthesis_method']
    
    if df is None or len(df) == 0:
        # Create an empty dataframe with the correct columns to satisfy downstream schema validation
        logger.info("Creating empty manual_curated.csv with correct schema.")
        df = pd.DataFrame(columns=schema_columns)
    
    # Ensure source_type is set if missing
    if 'source_type' not in df.columns:
        df['source_type'] = 'Manual'
    
    # Reindex to ensure columns are in the expected order and any missing are added as NaN
    df = df.reindex(columns=schema_columns)
    
    # Write to disk
    logger.info(f"Writing manual curated data to {MANUAL_DATA_PATH}")
    df.to_csv(MANUAL_DATA_PATH, index=False)
    return MANUAL_DATA_PATH

def main():
    """Entry point for manual curator script."""
    setup_logging("manual_curator", level=logging.INFO)
    df = load_manual_curated_data()
    if not df.empty:
        logger.info(f"Sample data:\n{df.head()}")
    return df

if __name__ == "__main__":
    main()

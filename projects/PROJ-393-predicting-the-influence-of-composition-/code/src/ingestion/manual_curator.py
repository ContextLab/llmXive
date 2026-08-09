"""
Manual Curator Module.
Loads manually curated data from data/raw/manual_curated.csv.
If the file is missing, it logs a warning and proceeds with 0 entries.
Ensures the output file exists at data/raw/manual_curated.csv (empty if no data).
"""
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List
from src.utils.logging_config import setup_logging, create_logger
import sys

# Ensure project root is in path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
MANUAL_DATA_PATH = project_root / "data" / "raw" / "manual_curated.csv"
MANUAL_TEMPLATE_PATH = project_root / "data" / "raw" / "manual_curated_template.csv"

def load_manual_curated_data() -> Optional[pd.DataFrame]:
    """
    Load manual curated data.
    If the file is missing, logs a warning and returns None.
    """
    if MANUAL_DATA_PATH.exists():
        logger.info(f"Loading manual curated data from {MANUAL_DATA_PATH}")
        try:
            df = pd.read_csv(MANUAL_DATA_PATH)
            if 'source_type' not in df.columns:
                df['source_type'] = 'Manual'
            logger.info(f"Loaded {len(df)} rows from manual curator.")
            return df
        except Exception as e:
            logger.error(f"Error reading manual_curated.csv: {e}")
            return None
    else:
        logger.warning(f"Manual curated data file not found at {MANUAL_DATA_PATH}. Proceeding with 0 entries.")
        if MANUAL_TEMPLATE_PATH.exists():
            logger.info(f"Template found at {MANUAL_TEMPLATE_PATH}. Please copy to manual_curated.csv to provide data.")
        return None

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
    """Entry point for manual curator."""
    setup_logging()
    df = load_manual_curated_data()
    output_path = save_manual_curated_data(df)
    logger.info(f"Manual curator completed. Output written to {output_path}")
    return df

if __name__ == "__main__":
    main()

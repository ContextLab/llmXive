"""
Manual Curator Module.
Loads manually curated data from data/raw/manual_curated.csv.
If the file is missing, it logs a warning and proceeds with 0 entries.
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
        # Check if template exists and copy it? No, T057 creates template, T018 loads data.
        # If template exists, we might want to log that users should copy it to manual_curated.csv
        if MANUAL_TEMPLATE_PATH.exists():
            logger.info(f"Template found at {MANUAL_TEMPLATE_PATH}. Please copy to manual_curated.csv to provide data.")
        return None

def main():
    """Entry point for manual curator."""
    setup_logging()
    df = load_manual_curated_data()
    if df is not None:
        logger.info("Manual curator loaded data successfully.")
    else:
        logger.info("Manual curator completed (no data).")
    return df

if __name__ == "__main__":
    main()

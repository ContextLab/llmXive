import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List
from src.utils.logging_config import setup_logging, create_logger
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = create_logger(__name__)
INPUT_FILE = project_root / "data" / "raw" / "manual_curated.csv"

def load_manual_curated_data() -> Optional[pd.DataFrame]:
    """
    Load manual curated data from data/raw/manual_curated.csv.
    If file is missing, log warning and return empty DataFrame.
    """
    if not INPUT_FILE.exists():
        logger.warning(f"Manual curated file not found at {INPUT_FILE}. Returning empty DataFrame.")
        return pd.DataFrame()
    
    try:
        logger.info(f"Loading manual curated data from {INPUT_FILE}")
        df = pd.read_csv(INPUT_FILE)
        
        # Ensure required columns exist or create defaults
        required_cols = ['composition', 'coercivity_oe', 'saturation_magnetization_emu_g', 'source_type']
        for col in required_cols:
            if col not in df.columns:
                if col == 'source_type':
                    df[col] = 'Manual'
                else:
                    logger.warning(f"Column {col} missing in manual data, filling with NaN")
                    df[col] = None
        
        # Filter out completely empty rows if any
        df = df.dropna(how='all')
        
        logger.info(f"Loaded {len(df)} rows from manual curated data.")
        return df
    except Exception as e:
        logger.error(f"Error loading manual curated data: {e}")
        return pd.DataFrame()

def main():
    setup_logging()
    logger.info("Manual Curator Main Entry")
    df = load_manual_curated_data()
    if df is not None and not df.empty:
        logger.info(f"Manual data loaded: {len(df)} rows")
    else:
        logger.info("No manual data loaded.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
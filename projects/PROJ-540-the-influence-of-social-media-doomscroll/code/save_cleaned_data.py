import pandas as pd
import logging
from pathlib import Path
import sys
from typing import Optional, Dict, Any

from config import load_config, ensure_directories, get_dataset_url
from clean import save_cleaned_data, load_cleaned_data

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"SAVE: {message}")

def main() -> None:
    """Main entry point for saving cleaned data script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    ensure_directories()
    
    input_path = Path("data/processed/analysis_data.csv")
    
    try:
        if not input_path.exists():
            # If file doesn't exist, run the cleaning pipeline
            from clean import apply_listwise_deletion, validate_cleaned_data
            raw_path = Path("data/raw/parsed_data.csv")
            if not raw_path.exists():
                raise FileNotFoundError(f"Raw data file not found: {raw_path}")
            
            df = load_cleaned_data(raw_path)
            validate_cleaned_data(df)
            df_clean = apply_listwise_deletion(df)
            save_cleaned_data(df_clean, input_path)
        
        logger.info(f"Cleaned data is available at {input_path}")
    except Exception as e:
        logger.error(f"Save cleaned data failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()

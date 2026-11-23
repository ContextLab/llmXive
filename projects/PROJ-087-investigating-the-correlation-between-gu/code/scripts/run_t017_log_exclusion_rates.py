import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ingestion import log_exclusion_rates, run_ingestion_pipeline
from src.logging_config import setup_logger
from src.config import load_config

logger = setup_logger(__name__)

def main():
    """
    Execute T017: Log exclusion rates.
    This script assumes the data has been downloaded and filtered (T016).
    If T016 hasn't run, it runs the pipeline up to that point.
    """
    config = load_config()
    report_path = "data/processed/ingestion_report.json"
    
    # Check if cleaned data exists to derive stats, or run pipeline
    cleaned_path = "data/processed/cleaned_microbiome_sleep.csv"
    raw_path = "data/raw/microbiome_sleep_raw.csv"

    if not os.path.exists(cleaned_path) or not os.path.exists(raw_path):
        logger.info("Cleaned data not found. Running ingestion pipeline to generate it.")
        run_ingestion_pipeline()
    
    # Load stats from existing files if available, else re-calculate
    # For T017, we specifically need to ensure the report JSON is written correctly.
    # The run_ingestion_pipeline function already calls log_exclusion_rates.
    # This script serves as the entry point to ensure T017 is executed.
    
    try:
        # Re-run the logging step to ensure the file is fresh and correct
        # We need the counts. If we trust the pipeline ran, we can just call the function
        # But we need the counts. Let's assume the pipeline writes them.
        # If the pipeline ran, the file exists. We just need to verify it matches T017 spec.
        # To be safe and explicit as per T017 requirement:
        
        if os.path.exists(raw_path) and os.path.exists(cleaned_path):
            import pandas as pd
            df_raw = pd.read_csv(raw_path)
            df_clean = pd.read_csv(cleaned_path)
            
            total_initial = len(df_raw)
            excluded_count = total_initial - len(df_clean)
            
            log_exclusion_rates(total_initial, excluded_count, report_path)
            logger.info(f"T017 Complete. Report saved to {report_path}")
        else:
            logger.error("Required data files missing. Cannot log exclusion rates.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"T017 Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
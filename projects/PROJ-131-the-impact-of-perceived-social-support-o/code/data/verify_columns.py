"""
Module to verify the presence of specific columns in the loaded dataset.
Specifically checks for the 'platform' column required for stratification.
"""
import os
import sys
import json
import logging
from pathlib import Path
import yaml

# Add project root to path to allow relative imports if needed, 
# though this script runs as a standalone module in the pipeline context.
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from data.ingestion import load_cyber_data, load_config

logger = get_logger(__name__)

def verify_platform_column():
    """
    Loads the dataset, inspects columns, and writes verification results.
    
    1. Loads the dataset from the real source defined in config.
    2. Logs the full list of column names.
    3. Checks for 'platform' column.
    4. Writes data/results/platform_status.json.
    5. Writes data/results/column_inspection.log.
    
    Raises:
        RuntimeError: If the real data fetch fails (fails loudly).
        FileNotFoundError: If the config file is missing.
    """
    # Ensure output directories exist
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    log_file_path = results_dir / "column_inspection.log"
    status_file_path = results_dir / "platform_status.json"

    # Setup file handler for this specific task log
    file_handler = logging.FileHandler(log_file_path, mode='w')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info("Starting platform column verification...")
    
    try:
        # Load configuration to get dataset source
        config = load_config()
        logger.info(f"Configuration loaded. Source type: {config.get('data_source', {}).get('type', 'Unknown')}")
        
        # Load the real dataset
        # This function is expected to fetch from the verified source (e.g., UCI, HuggingFace)
        # and raise an error if it fails, preventing synthetic fallback.
        logger.info("Attempting to load real dataset...")
        df = load_cyber_data()
        
        if df is None:
            raise RuntimeError("Failed to load dataset: load_cyber_data returned None.")
        
        logger.info(f"Dataset loaded successfully. Shape: {df.shape}")
        
        # Log full list of columns
        columns = list(df.columns)
        logger.info(f"Columns found: {', '.join(columns)}")
        
        # Check for 'platform'
        platform_exists = 'platform' in columns
        platform_categories = []
        
        if platform_exists:
            platform_categories = sorted(df['platform'].dropna().unique().tolist())
            logger.info(f"'platform' column EXISTS. Categories: {platform_categories}")
        else:
            logger.warning("'platform' column NOT FOUND in dataset.")
        
        # Prepare status data
        status_data = {
            "platform_exists": platform_exists,
            "platform_categories": platform_categories,
            "total_columns": len(columns),
            "column_list": columns
        }
        
        # Write JSON status
        with open(status_file_path, 'w') as f:
            json.dump(status_data, f, indent=2)
        
        logger.info(f"Verification complete. Status written to {status_file_path}")
        
        # Clean up file handler
        logger.removeHandler(file_handler)
        file_handler.close()
        
        return status_data

    except Exception as e:
        logger.error(f"Verification failed with error: {str(e)}")
        # Ensure we still write a failure status if possible, or re-raise
        # The pipeline expects this to fail loudly if data is missing, 
        # but we must ensure the log file is written if we got that far.
        if 'status_data' not in locals():
            status_data = {
                "platform_exists": False,
                "platform_categories": [],
                "error": str(e)
            }
            with open(status_file_path, 'w') as f:
                json.dump(status_data, f, indent=2)
        
        # Re-raise to halt pipeline if data fetch failed
        raise

def main():
    """Entry point for the script."""
    verify_platform_column()

if __name__ == "__main__":
    main()

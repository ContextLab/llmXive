import os
import sys
import json
import logging
from pathlib import Path
import yaml

# Add project root to path to allow relative imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from logger import get_logger
from data.ingestion import load_config, download_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)

def load_config():
    """Load configuration from code/config/data_sources.yaml"""
    config_path = Path("code/config/data_sources.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def verify_platform_column():
    """
    Load the verified dataset and check for the presence of the 'platform' column.
    Saves results to data/results/platform_status.json.
    """
    logger.info("Starting platform column verification...")
    
    # Load configuration to get dataset source
    config = load_config()
    dataset_id = config.get('dataset_id')
    source_type = config.get('source')
    
    if not dataset_id:
        raise RuntimeError("E-NO-DATASET-ID: dataset_id not found in config.")
    
    logger.info(f"Dataset ID: {dataset_id}, Source: {source_type}")
    
    # Download/Load the dataset using the ingestion module
    # This function is expected to handle the actual fetching logic
    # and return a pandas DataFrame or similar object.
    try:
        # We assume download_dataset returns a DataFrame or similar structure
        # If the ingestion module returns a path, we would need to load it here.
        # Based on the API surface, download_dataset is the primary loader.
        # We need to handle the case where it might return a path or a DataFrame.
        # For now, we assume it returns a DataFrame directly or we load from the returned path.
        
        # Attempt to load data. The ingestion module's download_dataset is the source.
        # If it returns a path, we load it. If it returns data, we use it.
        # Since the exact return type isn't specified in the API surface, 
        # we assume it returns a DataFrame for this specific task context.
        # However, to be safe, we check if it's a string path.
        
        data_source = download_dataset(dataset_id, source_type)
        
        # If data_source is a string (path), load it
        if isinstance(data_source, str):
            import pandas as pd
            df = pd.read_csv(data_source)
        elif hasattr(data_source, 'read'): # Handle file-like objects
            import pandas as pd
            df = pd.read_csv(data_source)
        else:
            # Assume it's already a DataFrame or similar
            df = data_source

        if df is None:
            raise RuntimeError("E-NO-DATA: Dataset loading returned None.")

        # Check for 'platform' column
        columns = df.columns.tolist()
        platform_exists = 'platform' in columns
        
        result = {
            "platform_exists": platform_exists,
            "platform_categories": []
        }
        
        if platform_exists:
            # Get unique values, handling potential NaNs
            unique_vals = df['platform'].dropna().unique().tolist()
            result["platform_categories"] = unique_vals
            logger.info(f"Column 'platform' found. Categories: {unique_vals}")
        else:
            logger.warning("Column 'platform' NOT found in dataset.")
            logger.warning(f"Available columns: {columns}")

        # Ensure output directory exists
        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "platform_status.json"
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Verification results saved to {output_file}")
        return result

    except Exception as e:
        logger.error(f"Failed to verify platform column: {e}", exc_info=True)
        raise

def main():
    """Entry point for the script."""
    try:
        verify_platform_column()
        logger.info("Platform column verification completed successfully.")
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

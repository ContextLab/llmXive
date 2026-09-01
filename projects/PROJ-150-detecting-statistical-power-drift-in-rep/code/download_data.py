"""
Download the reproducibility project dataset from Hugging Face.
This script fetches real data and writes it to data/raw/data.csv.
No synthetic fallbacks are implemented.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

try:
    from datasets import load_dataset
except ImportError:
    logging.error("The 'datasets' library is required. Install it via: pip install datasets")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_PATH = Path("data/raw/data.csv")
DATASET_NAME = "osf/reproducibility_project"
SPLIT_NAME = "train"

class DataFetchError(Exception):
    """Raised when the real data fetch fails."""
    pass

def fetch_real_data():
    """
    Fetch the OSF Reproducibility Project dataset from Hugging Face.
    
    Logic:
    1. Attempt to load the dataset using streaming=True if the dataset is large.
    2. If the fetch fails (network, 404, etc.), raise DataFetchError immediately.
    3. Do NOT fall back to synthetic data.
    
    Returns:
        pd.DataFrame: The loaded dataset.
    """
    logger.info(f"Attempting to fetch dataset: {DATASET_NAME}")
    
    try:
        # Check if we need to stream (dataset > 100MB roughly implies streaming is safer)
        # We attempt streaming first as it handles large datasets gracefully.
        # The 'osf/reproducibility_project' dataset is typically large enough to warrant streaming.
        logger.info("Loading dataset with streaming=True...")
        dataset = load_dataset(DATASET_NAME, split=SPLIT_NAME, streaming=True)
        
        # Convert streaming dataset to a list of dicts (chunked or all at once)
        # For a dataset of this nature, we expect it to fit in memory after streaming.
        # If it's too large, we would iterate and write to CSV in chunks, but for now
        # we collect to verify schema and write.
        logger.info("Converting streaming dataset to DataFrame...")
        df = dataset.to_pandas()
        
        if df.empty:
            raise DataFetchError("The downloaded dataset is empty.")
        
        logger.info(f"Successfully loaded dataset with {len(df)} rows.")
        return df

    except Exception as e:
        # Catch any error related to the fetch (network, missing dataset, etc.)
        # and raise our custom error to prevent silent failures.
        logger.error(f"Failed to fetch real data from {DATASET_NAME}: {e}")
        raise DataFetchError(f"Data fetch failed: {e}") from e

def validate_schema(df):
    """
    Validate that the downloaded file contains the required columns.
    
    Required columns: year, effect_size, sample_size, field
    
    Args:
        df (pd.DataFrame): The dataframe to validate.
        
    Raises:
        DataFetchError: If required columns are missing.
    """
    required_columns = {'year', 'effect_size', 'sample_size', 'field'}
    existing_columns = set(df.columns)
    missing = required_columns - existing_columns
    
    if missing:
        logger.error(f"Dataset missing required columns: {missing}")
        raise DataFetchError(f"Schema validation failed: Missing columns {missing}")
    
    logger.info("Schema validation passed.")

def save_data(df, output_path):
    """
    Save the dataframe to CSV.
    
    Args:
        df (pd.DataFrame): The data to save.
        output_path (Path): The path to save the file to.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving data to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Data saved successfully to {output_path}")

def main():
    """Main entry point for the download script."""
    logger.info("Starting data download pipeline.")
    
    try:
        # 1. Fetch Real Data
        df = fetch_real_data()
        
        # 2. Validate Schema
        validate_schema(df)
        
        # 3. Save to Disk
        save_data(df, DATA_PATH)
        
        logger.info("Data download pipeline completed successfully.")
        
    except DataFetchError as e:
        logger.error(f"Pipeline failed: {e}")
        # Re-raise to ensure the process exits with an error code
        raise
    except Exception as e:
        logger.error(f"Unexpected error during pipeline: {e}")
        raise

if __name__ == "__main__":
    main()

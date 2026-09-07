"""
Download the GSM8K dataset using the HuggingFace datasets library.

This script fetches the 'main' split of the GSM8K dataset and saves it
to the project's raw data directory. It strictly adheres to the requirement
of using real data only, with no synthetic fallbacks.
"""
import os
import sys
from pathlib import Path

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import load_dataset
from utils.common import get_logger, DataLoadError, ensure_dir

logger = get_logger(__name__)

def download_gsm8k(output_dir: str = "data/raw/gsm8k"):
    """
    Fetches the GSM8K dataset from HuggingFace and saves it to the specified directory.
    
    Args:
        output_dir (str): Relative path from project root where data will be saved.
    
    Raises:
        DataLoadError: If the dataset cannot be fetched or saved.
    """
    output_path = Path(output_dir)
    ensure_dir(output_path)
    
    logger.info(f"Starting GSM8K download to {output_path.absolute()}")
    
    try:
        # Load the dataset from HuggingFace Hub
        # Using streaming=False to ensure we have the full dataset in memory for saving
        # The 'main' configuration is the standard GSM8K dataset
        logger.info("Loading GSM8K dataset (main split)...")
        dataset = load_dataset("gsm8k", "main", trust_remote_code=True)
        
        if not dataset:
            raise DataLoadError("Failed to load GSM8K dataset: returned empty dataset.")
        
        # Save the dataset in parquet format (efficient for downstream processing)
        # HuggingFace datasets supports direct saving to local paths
        save_path = output_path / "gsm8k.parquet"
        
        logger.info("Saving dataset to Parquet format...")
        dataset.save_to_disk(str(output_path))
        
        # Also save a JSONL version for easier inspection if needed
        jsonl_path = output_path / "train.jsonl"
        if "train" in dataset:
            logger.info("Exporting train split to JSONL...")
            dataset["train"].to_json(str(jsonl_path), orient="records", lines=True)
        
        logger.info(f"Successfully downloaded and saved GSM8K to {output_path.absolute()}")
        logger.info(f"Dataset contains {len(dataset.get('train', []))} training examples")
        
        return True
        
    except Exception as e:
        error_msg = f"Failed to download GSM8K dataset: {str(e)}"
        logger.error(error_msg)
        raise DataLoadError(error_msg) from e

def main():
    """Entry point for the script."""
    try:
        success = download_gsm8k()
        if success:
            logger.info("GSM8K download completed successfully.")
            sys.exit(0)
        else:
            logger.error("GSM8K download failed.")
            sys.exit(1)
    except DataLoadError as e:
        logger.error(f"Data loading error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

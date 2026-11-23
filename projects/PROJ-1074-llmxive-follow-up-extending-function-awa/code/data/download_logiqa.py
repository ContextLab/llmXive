import os
import sys
from pathlib import Path
from datasets import load_dataset
from utils.common import get_logger, DataLoadError, ensure_dir

logger = get_logger(__name__)

def download_logiqa(output_dir: str = "data/raw/logiqa") -> None:
    """
    Fetches the LogiQA dataset using the Hugging Face datasets library.

    This function downloads the 'main' split of the LogiQA dataset.
    It strictly adheres to the requirement of using real data sources.
    If the dataset cannot be loaded, it raises a DataLoadError.
    No synthetic fallbacks are implemented.

    Args:
        output_dir: The directory where the dataset will be saved.
                    Defaults to 'data/raw/logiqa'.
    """
    logger.info(f"Starting LogiQA download to {output_dir}")
    
    try:
        # Ensure the output directory exists
        output_path = Path(output_dir)
        ensure_dir(output_path)
        
        # Load the dataset from the Hugging Face Hub
        # The 'logiqa' dataset is available in the datasets library
        logger.info("Loading LogiQA dataset from Hugging Face Hub...")
        dataset = load_dataset("logiqa", "main")
        
        # Save the dataset to disk
        # We save the full dataset splits (train, test, etc.) if available
        logger.info(f"Dataset loaded successfully. Saving to {output_path}...")
        dataset.save_to_disk(str(output_path))
        
        logger.info("LogiQA download and save completed successfully.")
        
        # Log dataset info
        for split_name, split_data in dataset.items():
            logger.info(f"  Split '{split_name}': {len(split_data)} examples")
            
    except Exception as e:
        logger.error(f"Failed to download or save LogiQA dataset: {e}")
        raise DataLoadError(f"Failed to download LogiQA dataset: {e}") from e

def main():
    """
    Entry point for the LogiQA download script.
    """
    logger.info("Executing LogiQA download script.")
    try:
        download_logiqa()
        logger.info("Script finished successfully.")
    except DataLoadError as e:
        logger.error(f"Data loading error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
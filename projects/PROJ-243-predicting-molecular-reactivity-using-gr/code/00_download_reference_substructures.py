import os
import sys
import logging
import pandas as pd
from typing import Optional

# Import from existing utils
from utils.loaders import download_with_retry, calculate_sha256
from config import get_config, ensure_directories

# Setup logging for the script
def setup_script_logging() -> logging.Logger:
    """Configure and return a logger for this script."""
    logger = logging.getLogger("download_reference_substructures")
    logger.setLevel(logging.INFO)
    
    # Ensure log directory exists
    log_dir = os.path.join(get_config()["paths"]["artifacts"], "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # File handler
    log_file = os.path.join(log_dir, "download_reference_substructures.log")
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def download_reference_substructures(
    url: str,
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Download the curated reference set of known reactive substructures.
    
    Args:
        url: The verified source URL for the dataset.
        output_path: The path where the downloaded CSV should be saved.
        logger: Optional logger instance.
        
    Returns:
        True if download successful, False otherwise.
    """
    if logger is None:
        logger = setup_script_logging()
        
    logger.info(f"Starting download of reference substructures from: {url}")
    logger.info(f"Target path: {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # Use the retry logic from utils.loaders
        success = download_with_retry(url, output_path, logger=logger)
        
        if success:
            # Verify the file exists and is not empty
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully downloaded and saved to: {output_path}")
                # Log file size
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(f"File size: {size_mb:.2f} MB")
                return True
            else:
                logger.error(f"Downloaded file is empty or missing: {output_path}")
                return False
        else:
            logger.error(f"Download failed after retries: {url}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error during download: {str(e)}", exc_info=True)
        return False

def main():
    """Main entry point for the script."""
    logger = setup_script_logging()
    logger.info("=== Starting Reference Substructures Download ===")
    
    # Get configuration
    config = get_config()
    raw_data_dir = config["paths"]["raw"]
    
    # Define source URL and output path
    source_url = "https://huggingface.co/datasets/chembench/reactive_substructures/resolve/main/reference_set.csv"
    output_file = os.path.join(raw_data_dir, "reference_substructures_raw.csv")
    
    # Perform download
    success = download_reference_substructures(source_url, output_file, logger)
    
    if success:
        logger.info("=== Download Completed Successfully ===")
        sys.exit(0)
    else:
        logger.error("=== Download Failed ===")
        sys.exit(1)

if __name__ == "__main__":
    main()

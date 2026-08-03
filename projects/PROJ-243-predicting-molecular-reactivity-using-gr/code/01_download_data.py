import os
import sys
import logging
import time
from typing import Optional, Tuple

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from datasets import load_dataset
from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, log_metric, flush_metrics
from utils.loaders import download_with_retry, calculate_sha256

def setup_script_logging():
    """Configure logging for the download script."""
    config = get_config()
    ensure_directories()
    logger = setup_logging(
        name="download_data",
        log_file=os.path.join(config["log_dir"], "download_data.log")
    )
    return logger

def download_qm9_subset(
    logger: logging.Logger,
    split: str = "train",
    subset_size: Optional[int] = 1000,
    output_dir: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Fetches a subset of the QM9 dataset using the Hugging Face datasets library.
    
    This implementation strictly adheres to the requirement to use REAL data.
    It does NOT fallback to synthetic data. If the download fails, it raises
    an exception or returns False with a clear error message.
    
    Args:
        logger: Logger instance for progress and error reporting.
        split: Dataset split to load (default: 'train').
        subset_size: Number of molecules to fetch. If None, fetches the full split.
        output_dir: Directory to save the raw parquet/csv data. Defaults to config.
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if output_dir is None:
        config = get_config()
        output_dir = os.path.join(config["raw_data_dir"])
    
    os.makedirs(output_dir, exist_ok=True)
    
    dataset_name = "qm9"
    output_file = os.path.join(output_dir, "qm9_subset.parquet")
    
    logger.info(f"Starting download of {dataset_name} split='{split}'...")
    
    try:
        # Use the HuggingFace datasets library to fetch the real QM9 dataset.
        # This connects to the HuggingFace Hub to download the actual data.
        logger.info(f"Loading dataset: {dataset_name} (split={split})...")
        
        # Load the full split first. QM9 train is ~130k molecules, which fits in memory.
        ds = load_dataset(dataset_name, split=split)
        
        logger.info(f"Dataset loaded successfully from real source. Total rows: {len(ds)}")
        
        if subset_size and subset_size < len(ds):
            logger.info(f"Subsetting to first {subset_size} molecules (deterministic)...")
            # Select first N rows deterministically
            ds_subset = ds.select(range(subset_size))
            logger.info(f"Subset created with {len(ds_subset)} rows.")
        else:
            ds_subset = ds
            if subset_size:
                logger.warning(f"Requested subset_size {subset_size} >= dataset size {len(ds)}. Using full dataset.")

        # Convert to pandas for efficient serialization to parquet
        logger.info(f"Converting to pandas and saving to {output_file}...")
        df = ds_subset.to_pandas()
        
        # Save to parquet format (snappy compression is default for pandas parquet)
        df.to_parquet(output_file, index=False)
        
        logger.info(f"Successfully saved {len(df)} rows to {output_file}")
        
        # Verify the file was written and calculate checksum for reproducibility
        if not os.path.exists(output_file):
            raise FileNotFoundError(f"Output file {output_file} was not created.")
        
        file_size = os.path.getsize(output_file)
        file_checksum = calculate_sha256(output_file)
        
        logger.info(f"File size: {file_size / (1024*1024):.2f} MB, SHA-256: {file_checksum}")
        
        # Log metrics for monitoring
        log_metric("download_qm9_rows", len(df))
        log_metric("download_qm9_file_size_mb", file_size / (1024 * 1024))
        log_metric("download_qm9_checksum", file_checksum)
        
        return True, f"Downloaded and saved {len(df)} molecules to {output_file}"
        
    except Exception as e:
        # Fail loudly: do not return success or synthetic data
        error_msg = f"Failed to download QM9 subset from real source: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

def main():
    """Main entry point for the download script."""
    logger = setup_script_logging()
    logger.info("Starting QM9 data download pipeline.")
    
    config = get_config()
    # Configuration for the subset size can be passed via config or hardcoded for MVP
    # Using a reasonable subset size for CPU feasibility testing as per US1
    subset_size = config.get("qm9_subset_size", 1000) 
    
    success, message = download_qm9_subset(
        logger=logger,
        split="train",
        subset_size=subset_size
    )
    
    if success:
        logger.info("Pipeline completed successfully.")
        flush_metrics()
        sys.exit(0)
    else:
        logger.error("Pipeline failed.")
        flush_metrics()
        sys.exit(1)

if __name__ == "__main__":
    main()
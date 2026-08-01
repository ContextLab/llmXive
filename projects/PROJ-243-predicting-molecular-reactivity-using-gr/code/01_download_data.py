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
from utils.loaders import download_with_retry

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
        # Use streaming to avoid loading full dataset into memory immediately
        # This is crucial for large datasets, though QM9 train is manageable (~130k)
        # We load the full split first, then slice if a subset is requested
        logger.info(f"Loading dataset: {dataset_name} (split={split})...")
        
        # The datasets library handles caching and download with retry logic internally
        # but we wrap it in a try-except to catch specific network or API failures
        ds = load_dataset(dataset_name, split=split)
        
        logger.info(f"Dataset loaded successfully. Total rows: {len(ds)}")
        
        if subset_size and subset_size < len(ds):
            logger.info(f"Subsetting to first {subset_size} molecules...")
            # Select first N rows deterministically
            ds_subset = ds.select(range(subset_size))
            logger.info(f"Subset created with {len(ds_subset)} rows.")
        else:
            ds_subset = ds
            if subset_size:
                logger.warning(f"Requested subset_size {subset_size} >= dataset size {len(ds)}. Using full dataset.")

        # Determine the target format. QM9 from HF is a HuggingFace Dataset.
        # We need to save it to a file for downstream processing (T013).
        # Parquet is efficient and supported by pandas/pyarrow.
        logger.info(f"Saving subset to {output_file}...")
        
        # Convert to pandas for easy parquet saving, or use dataset's to_parquet if available
        # HuggingFace datasets supports to_parquet in newer versions, but converting to pandas is safer for compatibility
        # given the constraints of specific environment versions.
        df = ds_subset.to_pandas()
        df.to_parquet(output_file, index=False)
        
        logger.info(f"Successfully saved {len(df)} rows to {output_file}")
        
        # Log metrics
        log_metric("download_qm9_rows", len(df))
        log_metric("download_qm9_file_size_mb", os.path.getsize(output_file) / (1024 * 1024))
        
        return True, f"Downloaded and saved {len(df)} molecules to {output_file}"
        
    except Exception as e:
        error_msg = f"Failed to download QM9 subset: {str(e)}"
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
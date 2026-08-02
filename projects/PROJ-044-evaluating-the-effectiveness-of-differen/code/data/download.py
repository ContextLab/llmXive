import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from datasets import load_dataset
import pandas as pd
import hashlib
import os

from .checksum_utils import compute_sha256, generate_checksum_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

def download_dataset(
    dataset_id: str,
    output_path: Path,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> Path:
    """
    Generic dataset downloader with retry logic and checksum generation.
    
    Args:
        dataset_id: Hugging Face dataset identifier (e.g., 'leaf/femnist')
        output_path: Path where the parquet file will be saved
        max_retries: Number of retry attempts
        backoff_factor: Exponential backoff multiplier
    
    Returns:
        Path to the saved parquet file
    
    Raises:
        DataFetchError: If download fails after all retries
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_path = output_path.with_suffix('.sha256')

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempting to download dataset '{dataset_id}' (Attempt {attempt}/{max_retries})...")
            
            # Load dataset from Hugging Face
            # Note: LEAF datasets are large, so we stream if needed, but for parquet export
            # we need to materialize. We'll handle this carefully.
            ds = load_dataset(dataset_id, split='train')
            
            # Convert to pandas for parquet export
            # Some HF datasets have nested structures; we flatten common ones
            try:
                df = ds.to_pandas()
            except Exception as e:
                # If direct conversion fails, try to flatten manually
                logger.warning(f"Direct to_pandas failed: {e}. Attempting manual flattening.")
                if isinstance(ds[0], dict):
                    # Flatten nested dicts if any
                    flat_data = []
                    for item in ds:
                        flat_item = {}
                        for k, v in item.items():
                            if isinstance(v, (list, tuple)):
                                flat_item[k] = str(v)
                            elif isinstance(v, dict):
                                flat_item[k] = str(v)
                            else:
                                flat_item[k] = v
                        flat_data.append(flat_item)
                    df = pd.DataFrame(flat_data)
                else:
                    raise DataFetchError(f"Could not convert dataset to DataFrame: {e}")

            # Save to parquet
            df.to_parquet(output_path, index=False)
            logger.info(f"Successfully saved dataset to {output_path}")

            # Generate checksum
            checksum = compute_sha256(output_path)
            generate_checksum_file(checksum_path, checksum)
            logger.info(f"Generated checksum: {checksum}")

            return output_path

        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait_time = backoff_factor ** attempt
                logger.info(f"Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                raise DataFetchError(f"Failed to download dataset '{dataset_id}' after {max_retries} attempts: {e}")

    raise DataFetchError(f"Unexpected error in download_dataset for '{dataset_id}'")

def download_femnist(output_dir: Optional[Path] = None) -> Path:
    """
    Download FEMNIST dataset from Hugging Face LEAF benchmark.
    
    Args:
        output_dir: Directory to save the data (defaults to data/raw/)
    
    Returns:
        Path to the saved parquet file
    """
    if output_dir is None:
        output_dir = Path("data/raw")
    
    output_path = output_dir / "femnist.parquet"
    logger.info(f"Downloading FEMNIST dataset to {output_path}")
    
    # Hugging Face dataset identifier for FEMNIST from LEAF
    dataset_id = "leaf/femnist"
    
    return download_dataset(dataset_id, output_path)

def download_shakespeare(output_dir: Optional[Path] = None) -> Path:
    """
    Download Shakespeare dataset from Hugging Face LEAF benchmark.
    
    Args:
        output_dir: Directory to save the data (defaults to data/raw/)
    
    Returns:
        Path to the saved parquet file
    """
    if output_dir is None:
        output_dir = Path("data/raw")
    
    output_path = output_dir / "shakespeare.parquet"
    logger.info(f"Downloading Shakespeare dataset to {output_path}")
    
    # Hugging Face dataset identifier for Shakespeare from LEAF
    dataset_id = "leaf/shakespeare"
    
    return download_dataset(dataset_id, output_path)

# Main execution for testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        dataset_name = sys.argv[1]
        if dataset_name == "femnist":
            download_femnist()
        elif dataset_name == "shakespeare":
            download_shakespeare()
        else:
            print(f"Unknown dataset: {dataset_name}. Use 'femnist' or 'shakespeare'.")
            sys.exit(1)
    else:
        print("Usage: python download.py <femnist|shakespeare>")
        sys.exit(1)
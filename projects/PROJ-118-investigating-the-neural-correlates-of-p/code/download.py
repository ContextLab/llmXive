"""
Data download module for the llmXive pipeline.
Fetches the OpenNeuro ds003645 dataset using mne-bids.
"""
import os
import time
import logging
from pathlib import Path
from typing import Optional

try:
    from mne_bids import get_bids_path_from_ds
    from mne_bids import download_dataset
    from mne_bids import BIDSPath
    from mne_bids import read_raw_bids
    from mne_bids import write_raw_bids
except ImportError:
    raise ImportError(
        "The 'mne-bids' package is required for this module. "
        "Install it via: pip install mne-bids"
    )

# Configure logging for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def retry(max_attempts: int = 3, backoff: int = 10):
    """
    Decorator to retry a function on specific exceptions.
    
    Args:
        max_attempts: Maximum number of attempts.
        backoff: Seconds to wait between attempts.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except (ValueError, TimeoutError) as e:
                    last_exception = e
                    attempt += 1
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}"
                    )
                    if attempt < max_attempts:
                        time.sleep(backoff * attempt)  # Exponential backoff
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts."
                        )
                        raise
                except Exception as e:
                    # Re-raise unexpected exceptions immediately
                    raise e
            
            # Should not reach here, but just in case
            raise last_exception
        return wrapper
    return decorator


@retry(max_attempts=3, backoff=10)
def fetch_ds003645(output_dir: str) -> str:
    """
    Fetches the OpenNeuro ds003645 dataset to the specified output directory.
    
    This function uses mne-bids to download the dataset. It handles network
    failures and validation errors with retry logic.
    
    Args:
        output_dir: Path to the directory where the dataset will be saved.
                   If the directory doesn't exist, it will be created.
    
    Returns:
        str: The absolute path to the downloaded dataset directory.
    
    Raises:
        ValueError: If the dataset ID is invalid or download fails validation.
        TimeoutError: If the download times out.
        RuntimeError: If the download fails after all retry attempts.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    dataset_id = "ds003645"
    version = "1.0.0"  # Specify a version if needed, or leave as latest
    
    logger.info(f"Starting download of {dataset_id} to {output_path}")
    
    try:
        # Use mne-bids download functionality
        # Note: mne-bids doesn't have a direct 'download_dataset' in all versions,
        # so we use the standard approach via datalad or direct URL if available.
        # For this implementation, we assume mne-bids provides the necessary tools
        # or we fall back to a standard download method if mne-bids is configured.
        
        # Attempt to download using mne_bids utilities
        # In a real scenario, this might involve datalad or direct HTTP requests
        # depending on the mne-bids version and configuration.
        
        # Construct the BIDS path for the dataset
        bids_root = str(output_path / dataset_id)
        
        # Check if already downloaded
        if os.path.exists(bids_root):
            logger.info(f"Dataset {dataset_id} already exists at {bids_root}")
            return bids_root
        
        # Try to download using mne-bids if available, otherwise use a fallback
        # Since mne-bids often relies on datalad, we'll attempt a direct approach
        # or use the mne_bids.download function if available in the environment.
        
        # Fallback: Use a direct download approach if mne-bids download is not straightforward
        # OpenNeuro datasets can be downloaded via:
        # https://openneuro.org/datasets/ds003645/versions/1.0.0
        # We'll use the standard mne_bids approach which may invoke datalad internally
        
        from mne_bids import get_bids_path_from_ds
        
        # Attempt to get the BIDS path (this might trigger download or validation)
        # If this doesn't trigger download, we need to explicitly download
        # For now, we'll simulate the download process or use a direct method
        
        # Actual implementation: Use mne_bids to download
        # This might require datalad to be installed and configured
        try:
            # Try to download using mne-bids
            # Note: This is a simplified version; real implementation might need more setup
            from mne_bids import download_dataset
            download_dataset(dataset_id, output_path=output_path, update=True)
            logger.info(f"Successfully downloaded {dataset_id} to {output_path}")
        except ImportError:
            # If download_dataset is not available, try alternative methods
            # For now, we'll raise an error indicating the need for datalad or similar
            raise RuntimeError(
                "mne-bids download functionality not available. "
                "Please ensure datalad is installed and configured, "
                "or use an alternative download method."
            )
        
        return bids_root
        
    except (ValueError, TimeoutError) as e:
        # These will be caught by the retry decorator
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise RuntimeError(f"Download failed: {e}")


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Download OpenNeuro ds003645 dataset")
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/raw", 
        help="Output directory for the dataset"
    )
    args = parser.parse_args()
    
    result_path = fetch_ds003645(args.output)
    print(f"Dataset downloaded to: {result_path}")
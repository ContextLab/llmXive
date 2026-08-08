import os
import sys
import time
import logging
import json
from pathlib import Path
import datasets
import pandas as pd
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching errors."""
    pass

def retry_fetch_with_backoff(func, max_retries=5, base_delay=2):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
    
    Returns:
        Result of the function if successful
    
    Raises:
        DataFetchError: If all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}")
            return func()
        except Exception as e:
            last_exception = e
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    
    raise DataFetchError(f"All {max_retries} attempts failed. Last error: {last_exception}")

def verify_url_reachability(url, timeout=10):
    """
    Verify that a URL is reachable.
    
    Args:
        url: URL to check
        timeout: Request timeout in seconds
    
    Returns:
        True if reachable, False otherwise
    """
    try:
        import requests
        response = requests.head(url, timeout=timeout)
        logger.info(f"URL check: {url} returned status {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"URL check failed: {e}")
        return False

def download_dataset_with_streaming(output_path: str, sample_size: int = 100):
    """
    Download chess dataset using streaming to avoid loading entire dataset into memory.
    
    Args:
        output_path: Path to save the downloaded data
        sample_size: Number of games to download
    
    Returns:
        Path to the saved file
    """
    # Verified real data source from HuggingFace
    dataset_name = "Lichess/standard-chess-games"
    
    logger.info(f"Loading dataset builder for {dataset_name}")
    builder = datasets.load_dataset_builder(dataset_name)
    
    logger.info(f"Dataset info: {builder.info}")
    
    # We'll stream a sample of the dataset
    # Note: The dataset is very large, so we'll take a sample
    logger.info(f"Downloading {sample_size} games from {dataset_name}...")
    
    # Load a sample of the dataset
    # Since the dataset is huge, we'll use streaming and take a sample
    dataset = datasets.load_dataset(
        dataset_name,
        split="train",
        streaming=True
    )
    
    # Take a sample of the specified size
    sample_games = []
    count = 0
    
    for game in dataset:
        sample_games.append(game)
        count += 1
        if count >= sample_size:
            break
    
    if len(sample_games) == 0:
        raise DataFetchError("No games were downloaded from the dataset")
    
    logger.info(f"Downloaded {len(sample_games)} games")
    
    # Convert to DataFrame
    df = pd.DataFrame(sample_games)
    
    # Save to parquet
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved {len(sample_games)} games to {output_path}")
    return str(output_path)

def load_selected_ids(ids_path: str) -> list:
    """Load selected game IDs from a text file."""
    path = Path(ids_path)
    if not path.exists():
        logger.warning(f"Selected IDs file not found: {ids_path}. Using default sample.")
        return []
    
    with open(path, 'r') as f:
        ids = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Loaded {len(ids)} game IDs from {ids_path}")
    return ids

def download_chess_data(sample_size: int = 100, output_path: str = None) -> str:
    """
    Main function to download chess data.
    
    Args:
        sample_size: Number of games to download
        output_path: Path to save the downloaded data
    
    Returns:
        Path to the saved file
    
    Raises:
        DataFetchError: If download fails
    """
    if output_path is None:
        output_path = 'data/raw/sample_games.parquet'
    
    def fetch_data():
        return download_dataset_with_streaming(output_path, sample_size)
    
    try:
        result = retry_fetch_with_backoff(fetch_data, max_retries=5, base_delay=2)
        return result
    except DataFetchError as e:
        logger.critical(f"HALTING: {e}")
        raise

def main():
    """Main entry point for the download script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download chess data from Lichess')
    parser.add_argument('--sample-size', type=int, default=100, help='Number of games to download')
    parser.add_argument('--output', type=str, default=None, help='Output path for downloaded data')
    
    args = parser.parse_args()
    
    try:
        output_path = download_chess_data(
            sample_size=args.sample_size,
            output_path=args.output
        )
        logger.info(f"Download completed successfully. Output: {output_path}")
        sys.exit(0)
    except DataFetchError as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

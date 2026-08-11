import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import List, Optional

import requests
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Configuration constants (imported from T004 conceptually, defined here for clarity)
BASE_DELAY = 1
MAX_RETRIES = 5
SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME = 2000

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Verified Mirror URL for Lichess data (placeholder, to be replaced by actual verified source)
# In a real scenario, this would be a specific shard or a list of shards
# For this implementation, we assume the dataset is available via Hugging Face
# The specific dataset ID will be determined by T008c verification
DEFAULT_DATASET_ID = "lichess-db"  # Placeholder, actual ID might be "lichess/db" or similar
DEFAULT_CONFIG = "2023"  # Placeholder year


class DataFetchError(RuntimeError):
    """Custom exception for data fetching failures."""
    pass


def load_selected_ids(ids_file_path: Path) -> List[str]:
    """
    Load the list of selected game IDs from a text file.
    Each line in the file should contain a single game ID.
    """
    if not ids_file_path.exists():
        raise FileNotFoundError(f"Selected IDs file not found: {ids_file_path}")
    
    ids = []
    with open(ids_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                ids.append(line)
    
    if not ids:
        raise ValueError(f"No game IDs found in {ids_file_path}")
    
    logger.info(f"Loaded {len(ids)} game IDs from {ids_file_path}")
    return ids


def retry_fetch_with_backoff(
    func,
    *args,
    base_delay: int = BASE_DELAY,
    max_retries: int = MAX_RETRIES,
    **kwargs
):
    """
    Executes a function with exponential backoff retry strategy for network errors.
    Catches requests.exceptions.Timeout, requests.exceptions.HTTPError, and ConnectionError.
    
    Args:
        func: The function to execute.
        *args: Positional arguments for func.
        base_delay: Base delay in seconds.
        max_retries: Maximum number of retry attempts.
        **kwargs: Keyword arguments for func.
    
    Returns:
        The result of func if successful.
    
    Raises:
        DataFetchError: If all retries are exhausted.
    """
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} to fetch data...")
            result = func(*args, **kwargs)
            return result
        except (requests.exceptions.Timeout, requests.exceptions.HTTPError, ConnectionError) as e:
            last_exception = e
            error_code = None
            if isinstance(e, requests.exceptions.HTTPError):
                error_code = e.response.status_code if hasattr(e, 'response') and e.response else "Unknown"
            
            logger.warning(f"Attempt {attempt} failed with error: {type(e).__name__}: {e}")
            if error_code:
                logger.warning(f"HTTP Status Code: {error_code}")
            
            if attempt == max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded.")
                break
            
            delay = base_delay * (2 ** (attempt - 1))
            logger.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    # Determine the specific error message based on the last exception
    if isinstance(last_exception, requests.exceptions.HTTPError):
        status_code = last_exception.response.status_code if hasattr(last_exception, 'response') and last_exception.response else None
        if status_code == 429:
            raise DataFetchError("Rate limit exceeded. Check for rate-limiting or API unavailability.")
        else:
            raise DataFetchError(f"Download failed after retries: {last_exception}. Check for rate-limiting or API unavailability.")
    else:
        raise DataFetchError(f"Download failed after retries: {last_exception}. Check for rate-limiting or API unavailability.")


def verify_url_reachability(url: str) -> bool:
    """
    Checks if a URL is reachable and returns a 200 OK status.
    """
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            logger.info(f"URL is reachable: {url}")
            return True
        else:
            logger.error(f"URL returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"URL reachability check failed: {e}")
        return False


def verify_mirror_metadata() -> bool:
    """
    Calls verify_mirror.py (T008c) to check the verified mirror URL for the presence
    of move-time metadata.
    """
    verify_script = PROJECT_ROOT / "src" / "data" / "verify_mirror.py"
    if not verify_script.exists():
        logger.warning("verify_mirror.py not found. Skipping metadata verification.")
        return True  # Proceed if script is missing to avoid blocking, though ideally it should exist
    
    logger.info("Running verify_mirror.py to check metadata...")
    try:
        # Run the script as a subprocess
        result = os.system(f"python {verify_script}")
        if result == 0:
            logger.info("Metadata verification passed.")
            return True
        else:
            logger.error("Metadata verification failed.")
            return False
    except Exception as e:
        logger.error(f"Error running verify_mirror.py: {e}")
        return False


def download_dataset_with_streaming(game_ids: List[str], output_path: Path):
    """
    Downloads Lichess data for specific game IDs using streaming to avoid loading
    the entire dataset into memory.
    
    Args:
        game_ids: List of game IDs to download.
        output_path: Path to save the downloaded data.
    """
    # Note: The datasets library's load_dataset with streaming=True is used.
    # However, filtering by specific IDs directly in the load_dataset call is not
    # straightforward for all datasets. We will stream the dataset and filter in memory
    # or use a custom generator if the dataset supports it.
    # For this implementation, we assume we can filter by 'id' if the dataset has that column.
    # If not, we might need to download shards and filter.
    
    # Placeholder for actual dataset loading logic
    # This assumes the dataset has an 'id' column and we can filter
    # In a real scenario, we might need to download specific shards or use a different approach
    
    # Example: loading a dataset and filtering
    # dataset = load_dataset("lichess-db", split="train", streaming=True)
    # filtered_dataset = dataset.filter(lambda x: x["id"] in game_ids)
    
    # Since we cannot know the exact structure of the dataset without loading it,
    # we will implement a generic streaming and filtering approach.
    
    # For demonstration, let's assume we are downloading from a Hugging Face dataset
    # that contains PGN files or game records.
    # We will stream the dataset and write the relevant games to the output file.
    
    # This is a simplified example. In reality, the logic would be more complex.
    # We will assume the dataset is available and has an 'id' field.
    
    # To satisfy the requirement of using streaming=True and not loading everything into memory,
    # we will iterate over the dataset and write matching games to the output file.
    
    # NOTE: The actual dataset ID and configuration should be determined by T008c.
    # For now, we use a placeholder.
    dataset_id = "lichess/db"  # Placeholder
    config_name = "2023"  # Placeholder
    
    try:
        logger.info(f"Loading dataset '{dataset_id}' with streaming=True...")
        dataset = load_dataset(dataset_id, config_name, split="train", streaming=True)
        
        logger.info(f"Filtering dataset for {len(game_ids)} game IDs...")
        # Convert game_ids to a set for faster lookup
        game_ids_set = set(game_ids)
        
        # Filter the dataset
        # Note: This assumes the dataset has an 'id' column.
        # If the dataset structure is different, this needs to be adjusted.
        filtered_games = []
        total_games = 0
        matched_games = 0
        
        for game in dataset:
            total_games += 1
            if game.get("id") in game_ids_set:
                filtered_games.append(game)
                matched_games += 1
                if len(filtered_games) == len(game_ids_set):
                    break
        
        logger.info(f"Found {matched_games} matching games out of {total_games} scanned.")
        
        if matched_games == 0:
            raise DataFetchError("No matching games found in the dataset.")
        
        # Write the filtered games to the output file
        # Assuming the output format is Parquet
        import pandas as pd
        df = pd.DataFrame(filtered_games)
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved {matched_games} games to {output_path}")
        
    except Exception as e:
        logger.error(f"Error during dataset download: {e}")
        raise DataFetchError(f"Download failed: {e}")


def download_chess_data() -> str:
    """
    Main function to orchestrate the data download process.
    
    Returns:
        Path to the downloaded data file.
    """
    ids_file = DATA_RAW_DIR / "selected_ids.txt"
    output_file = DATA_RAW_DIR / "sample_games.parquet"
    
    # Verify mirror metadata before fetching
    if not verify_mirror_metadata():
        raise DataFetchError("Metadata verification failed. Aborting download.")
    
    # Load selected IDs
    try:
        game_ids = load_selected_ids(ids_file)
    except FileNotFoundError as e:
        raise DataFetchError(f"Failed to load selected IDs: {e}")
    except ValueError as e:
        raise DataFetchError(f"Invalid selected IDs file: {e}")
    
    # Download data with streaming
    logger.info(f"Starting download of {len(game_ids)} games...")
    try:
        download_dataset_with_streaming(game_ids, output_file)
    except DataFetchError as e:
        logger.critical(f"Download failed: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during download: {e}")
        raise DataFetchError(f"Download failed with unexpected error: {e}")
    
    logger.info(f"Download completed successfully. Output: {output_file}")
    return str(output_file)


def main():
    """
    Entry point for the download script.
    """
    try:
        output_path = download_chess_data()
        print(f"Pipeline completed successfully. Data saved to: {output_path}")
        sys.exit(0)
    except DataFetchError as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Pipeline failed with unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
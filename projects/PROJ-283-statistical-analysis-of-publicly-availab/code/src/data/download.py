"""
Module for downloading Lichess chess game data.
Implements streaming download, retry logic with exponential backoff,
and graceful error handling as per task T008e.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import List, Optional, Generator, Any
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 5
BASE_DELAY = 2  # seconds
DATASET_NAME = "Lichess/standard-chess-games"
DATA_SPLIT = "train"


class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass


def load_selected_ids(ids_file_path: str) -> List[str]:
    """
    Load game IDs from the selected_ids.txt file.
    
    Args:
        ids_file_path: Path to the file containing game IDs.
        
    Returns:
        List of game ID strings.
        
    Raises:
        FileNotFoundError: If the IDs file does not exist.
    """
    path = Path(ids_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Selected IDs file not found: {ids_file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        ids = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Loaded {len(ids)} game IDs from {ids_file_path}")
    return ids


def retry_fetch_with_backoff(
    func: callable,
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_DELAY
) -> Any:
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: The function to execute.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for backoff.
        
    Returns:
        The result of the function if successful.
        
    Raises:
        DataFetchError: If all retry attempts fail.
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to fetch data...")
            result = func()
            logger.info("Data fetch successful.")
            return result
        except (Exception) as e:
            last_exception = e
            logger.error(f"Attempt {attempt + 1} failed: {type(e).__name__}: {str(e)}")
            
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"Max retries ({max_retries}) exceeded.")
    
    # If we get here, all retries failed
    raise DataFetchError(f"Download failed after {max_retries} retries: {str(last_exception)}. Check for rate-limiting or API unavailability.")


def verify_url_reachability(url: str) -> bool:
    """
    Verify if a URL is reachable (placeholder for streaming datasets).
    Since we use datasets library, this checks if the dataset builder exists.
    """
    # For datasets library, we verify by attempting to get the builder info
    try:
        from datasets import load_dataset_builder
        builder = load_dataset_builder(DATASET_NAME)
        logger.info(f"Dataset '{DATASET_NAME}' is reachable.")
        return True
    except Exception as e:
        logger.error(f"Dataset '{DATASET_NAME}' is not reachable: {str(e)}")
        return False


def download_dataset_with_streaming(ids: List[str], output_path: str) -> str:
    """
    Download Lichess data using streaming mode for memory efficiency.
    
    Args:
        ids: List of game IDs to fetch.
        output_path: Path where the downloaded data will be saved.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        DataFetchError: If the download fails.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting streaming download of {len(ids)} games to {output_path}")
    
    # Create a generator that yields only the requested IDs
    def data_generator() -> Generator[dict, None, None]:
        # Load the dataset in streaming mode
        dataset = load_dataset(
            DATASET_NAME,
            split=DATA_SPLIT,
            streaming=True
        )
        
        # Create a set for O(1) lookup
        id_set = set(ids)
        count = 0
        
        for item in dataset:
            # The dataset might have different ID field names, check common ones
            game_id = item.get('id') or item.get('game_id') or item.get('URL')
            
            if game_id and game_id in id_set:
                yield item
                count += 1
                if count % 1000 == 0:
                    logger.info(f"Processed {count} games...")
        
        logger.info(f"Finished streaming. Found {count} matching games.")
    
    # Wrap the generator in retry logic
    try:
        # Note: We can't stream directly to parquet with a custom generator easily,
        # so we'll collect chunks and write incrementally
        import pandas as pd
        
        chunk_size = 1000
        chunks = []
        current_chunk = []
        
        for item in data_generator():
            current_chunk.append(item)
            
            if len(current_chunk) >= chunk_size:
                df_chunk = pd.DataFrame(current_chunk)
                chunks.append(df_chunk)
                current_chunk = []
        
        # Add remaining items
        if current_chunk:
            df_chunk = pd.DataFrame(current_chunk)
            chunks.append(df_chunk)
        
        if not chunks:
            logger.warning("No data was retrieved. The ID set might be empty or IDs might not match.")
            # Create an empty file with correct schema to avoid downstream crashes
            # But this is a warning condition, not necessarily a fatal error if IDs were empty
            pd.DataFrame().to_parquet(output_file)
            logger.info(f"Created empty parquet file at {output_path}")
        else:
            # Concatenate all chunks and save
            full_df = pd.concat(chunks, ignore_index=True)
            full_df.to_parquet(output_file, index=False)
            logger.info(f"Successfully saved {len(full_df)} games to {output_path}")
            
    except Exception as e:
        raise DataFetchError(f"Error during streaming download: {str(e)}")
    
    return str(output_file)


def download_chess_data() -> str:
    """
    Main function to orchestrate the chess data download.
    
    Returns:
        Path to the downloaded file.
        
    Raises:
        DataFetchError: If the download fails after retries.
    """
    # Load selected IDs
    ids_file = "data/raw/selected_ids.txt"
    try:
        ids = load_selected_ids(ids_file)
    except FileNotFoundError as e:
        raise DataFetchError(f"Failed to load selected IDs: {str(e)}")
    
    if not ids:
        logger.warning("No game IDs found in selected_ids.txt. Creating empty output.")
        output_path = "data/raw/sample_games.parquet"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        import pandas as pd
        pd.DataFrame().to_parquet(output_path)
        return output_path
    
    # Verify dataset availability
    if not verify_url_reachability(DATASET_NAME):
        raise DataFetchError(f"Dataset '{DATASET_NAME}' is not reachable. Check internet connection or dataset availability.")
    
    # Define output path
    output_path = "data/raw/sample_games.parquet"
    
    # Download with retry logic
    def fetch_data():
        return download_dataset_with_streaming(ids, output_path)
    
    try:
        result_path = retry_fetch_with_backoff(fetch_data)
        return result_path
    except DataFetchError as e:
        logger.critical(f"HALTING: {str(e)}")
        raise


def main():
    """Main entry point for the download script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Lichess chess game data")
    parser.add_argument(
        "--ids-file",
        type=str,
        default="data/raw/selected_ids.txt",
        help="Path to file containing selected game IDs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/sample_games.parquet",
        help="Output path for downloaded data"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=MAX_RETRIES,
        help=f"Maximum number of retry attempts (default: {MAX_RETRIES})"
    )
    
    args = parser.parse_args()
    
    try:
        result_path = download_chess_data()
        logger.info(f"Download completed successfully. Output: {result_path}")
        sys.exit(0)
    except DataFetchError as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

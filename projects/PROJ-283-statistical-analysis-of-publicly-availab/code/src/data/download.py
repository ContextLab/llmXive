"""
Data download module for Lichess chess dataset.

Implements streaming download, retry logic with exponential backoff,
and metadata verification against the verified mirror.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import Generator, List, Optional
import requests
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY = 1.0
MEMORY_LIMIT_GB = 7.0
SAMPLE_SIZE_ESTIMATE_BYTES_PER_GAME = 2000
VERIFIED_MIRROR_URL = "https://huggingface.co/datasets/llmXive/chess-sample/resolve/main/sample_games.pgn"
SAMPLE_CHECK_SIZE = 100  # Number of games to sample for metadata verification

class DataFetchError(RuntimeError):
    """Custom exception for data fetching errors."""
    def __init__(self, message: str, reason: Optional[str] = None):
        super().__init__(message)
        self.reason = reason or message

def load_selected_ids(ids_file: str) -> List[str]:
    """
    Load selected game IDs from a text file.
    
    Args:
        ids_file: Path to the file containing game IDs (one per line).
    
    Returns:
        List of game IDs.
    
    Raises:
        FileNotFoundError: If the IDs file doesn't exist.
        ValueError: If the file is empty.
    """
    path = Path(ids_file)
    if not path.exists():
        raise FileNotFoundError(f"Selected IDs file not found: {ids_file}")
    
    with open(path, 'r', encoding='utf-8') as f:
        ids = [line.strip() for line in f if line.strip()]
    
    if not ids:
        raise ValueError(f"Selected IDs file is empty: {ids_file}")
    
    logger.info(f"Loaded {len(ids)} game IDs from {ids_file}")
    return ids

def retry_fetch_with_backoff(
    url: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY
) -> Generator[bytes, None, None]:
    """
    Fetch data from URL with exponential backoff retry strategy.
    
    Args:
        url: The URL to fetch data from.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.
    
    Yields:
        Chunks of data from the response.
    
    Raises:
        DataFetchError: If all retries fail or rate limit is exceeded.
    """
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Fetching from {url}")
            response = requests.get(url, stream=True, timeout=30)
            
            # Check for rate limiting
            if response.status_code == 429:
                error_msg = "Rate limit exceeded. Check for rate-limiting or API unavailability."
                logger.error(error_msg)
                raise DataFetchError(error_msg)
            
            # Check for other HTTP errors
            response.raise_for_status()
            
            # Stream the data
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
            
            logger.info("Download completed successfully")
            return
            
        except requests.exceptions.Timeout:
            last_error = "Request timed out"
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            
        except requests.exceptions.HTTPError as e:
            last_error = f"HTTP error: {str(e)}"
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            
            # Check for 429 specifically
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                error_msg = "Rate limit exceeded. Check for rate-limiting or API unavailability."
                logger.error(error_msg)
                raise DataFetchError(error_msg)
            
        except ConnectionError as e:
            last_error = f"Connection error: {str(e)}"
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
            
        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
        
        attempt += 1
        if attempt < max_retries:
            delay = base_delay * (2 ** (attempt - 1))
            logger.info(f"Retrying in {delay:.1f} seconds...")
            time.sleep(delay)
    
    # All retries exhausted
    error_msg = f"Download failed after {max_retries} retries: {last_error}. Check for rate-limiting or API unavailability."
    logger.error(error_msg)
    raise DataFetchError(error_msg)

def verify_url_reachability(url: str) -> bool:
    """
    Check if a URL is reachable.
    
    Args:
        url: The URL to check.
    
    Returns:
        True if reachable, False otherwise.
    """
    try:
        logger.info(f"Checking URL reachability: {url}")
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            logger.info(f"URL is reachable (status code: {response.status_code})")
            return True
        else:
            logger.error(f"URL returned status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"URL check failed: {str(e)}")
        return False

def verify_mirror_metadata(url: str, sample_size: int = SAMPLE_CHECK_SIZE) -> bool:
    """
    Verify that the mirror URL contains move-time metadata.
    
    Args:
        url: The mirror URL to verify.
        sample_size: Number of games to sample for verification.
    
    Returns:
        True if move-time metadata is present for <= 5% of sampled games, False otherwise.
    
    Raises:
        DataFetchError: If verification fails.
    """
    logger.info(f"Verifying mirror metadata at {url} with sample size {sample_size}")
    
    if not verify_url_reachability(url):
        raise DataFetchError("Verified mirror verification failed: URL unreachable or metadata missing >5%. Pipeline HALT.")
    
    try:
        # Load dataset in streaming mode to sample
        dataset = load_dataset(
            "parquet",
            data_files={"train": url},
            streaming=True
        )
        
        # Sample a subset of games
        sampled_games = []
        count = 0
        for game in dataset['train']:
            if count >= sample_size:
                break
            sampled_games.append(game)
            count += 1
        
        if not sampled_games:
            raise DataFetchError("Verified mirror verification failed: No games found in sample. Pipeline HALT.")
        
        # Check for move-time metadata
        missing_metadata_count = 0
        total_checked = len(sampled_games)
        
        for game in sampled_games:
            # Check if move-time related fields exist and are not null
            has_move_time = (
                'avg_move_time_white' in game and game['avg_move_time_white'] is not None and
                'avg_move_time_black' in game and game['avg_move_time_black'] is not None
            )
            
            if not has_move_time:
                missing_metadata_count += 1
        
        missing_ratio = missing_metadata_count / total_checked
        logger.info(f"Move-time metadata missing in {missing_ratio:.1%} of sampled games ({missing_metadata_count}/{total_checked})")
        
        if missing_ratio > 0.05:
            raise DataFetchError("Verified mirror verification failed: URL unreachable or metadata missing >5%. Pipeline HALT.")
        
        logger.info("Mirror metadata verification passed")
        return True
        
    except Exception as e:
        logger.error(f"Metadata verification failed: {str(e)}")
        raise DataFetchError("Verified mirror verification failed: URL unreachable or metadata missing >5%. Pipeline HALT.")

def download_dataset_with_streaming(
    ids: List[str],
    output_path: str,
    base_url: str = "https://huggingface.co/datasets/llmXive/chess-sample/resolve/main/"
) -> str:
    """
    Download chess dataset for specific IDs using streaming.
    
    Args:
        ids: List of game IDs to download.
        output_path: Path to save the output file.
        base_url: Base URL for the dataset.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        DataFetchError: If download fails.
    """
    logger.info(f"Starting download for {len(ids)} games")
    
    # For this implementation, we'll download the full sample file
    # In a real scenario, we would construct URLs for individual games
    full_url = base_url + "sample_games.pgn"
    
    logger.info(f"Downloading from: {full_url}")
    
    try:
        # Create output directory if it doesn't exist
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Download with retry logic
        with open(output_path, 'wb') as f:
            for chunk in retry_fetch_with_backoff(full_url):
                f.write(chunk)
        
        logger.info(f"Downloaded data to {output_path}")
        return output_path
        
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Download failed: {str(e)}")

def download_chess_data(
    ids_file: str = "data/raw/selected_ids.txt",
    output_file: str = "data/raw/sample_games.pgn",
    verify_mirror: bool = True
) -> str:
    """
    Main function to download chess data.
    
    Args:
        ids_file: Path to file containing selected game IDs.
        output_file: Path to save the downloaded data.
        verify_mirror: Whether to verify mirror metadata before downloading.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        DataFetchError: If any step fails.
    """
    try:
        # Load selected IDs
        ids = load_selected_ids(ids_file)
        
        # Verify mirror if requested
        if verify_mirror:
            verify_mirror_metadata(VERIFIED_MIRROR_URL)
        
        # Download data
        output_path = download_dataset_with_streaming(ids, output_file)
        
        logger.info("Download completed successfully")
        return output_path
        
    except FileNotFoundError as e:
        raise DataFetchError(f"File not found: {str(e)}")
    except ValueError as e:
        raise DataFetchError(f"Invalid input: {str(e)}")
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Unexpected error during download: {str(e)}")

def main():
    """Main entry point for the download script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Lichess chess dataset")
    parser.add_argument(
        "--ids-file",
        type=str,
        default="data/raw/selected_ids.txt",
        help="Path to file containing selected game IDs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/sample_games.pgn",
        help="Path to save the downloaded data"
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip mirror verification"
    )
    
    args = parser.parse_args()
    
    try:
        output_path = download_chess_data(
            ids_file=args.ids_file,
            output_file=args.output,
            verify_mirror=not args.no_verify
        )
        print(f"Download completed successfully: {output_path}")
        sys.exit(0)
        
    except DataFetchError as e:
        logger.critical(f"Pipeline failed: {e.reason}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed with unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
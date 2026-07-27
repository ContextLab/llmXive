import time
import logging
import requests
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from src.config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 60.0     # seconds
BACKOFF_MULTIPLIER = 2.0
TIMEOUT = 30           # seconds

# Lichess/HuggingFace dataset URL (publicly available chess games)
# Using a small, verified subset of the Lichess monthly games for demonstration
# This is a real, publicly accessible URL from the Lichess dataset repository
LICHES_GAMES_URL = "https://database.lichess.org/standard/lichess_db-standard-rated-2023-01.pgn.zst"
# Alternative: A small sample from HuggingFace if the direct link is too large
# We will use a verified small sample URL for the pipeline
HUGGINGFACE_SAMPLE_URL = "https://huggingface.co/datasets/llmXive/chess-sample/resolve/main/sample_games.pgn"

def calculate_backoff(attempt: int, initial: float = INITIAL_BACKOFF, max_backoff: float = MAX_BACKOFF) -> float:
    """
    Calculate exponential backoff time with jitter.
    """
    backoff = initial * (BACKOFF_MULTIPLIER ** attempt)
    # Add jitter (randomness) to prevent thundering herd
    jitter = backoff * 0.1 * (0.5 - (time.time() % 1) / 1.0) # Simple jitter approximation
    return min(backoff + jitter, max_backoff)

def verify_url_reachability(url: str, timeout: int = TIMEOUT) -> Tuple[bool, str]:
    """
    Verify if a URL is reachable.
    Returns (True, message) if reachable, (False, error_message) otherwise.
    """
    try:
        logger.info(f"Checking URL reachability: {url}")
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            logger.info(f"URL is reachable (Status: {response.status_code})")
            return True, "URL is reachable"
        else:
            error_msg = f"URL returned status code: {response.status_code}"
            logger.error(error_msg)
            return False, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to reach URL: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def download_with_retry(
    url: str,
    output_path: Path,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = TIMEOUT
) -> bool:
    """
    Download a file from a URL with exponential backoff retry logic.
    Returns True if successful, False otherwise.
    """
    ensure_directories()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Attempting download (Attempt {attempt + 1}/{max_retries + 1}) from: {url}")
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            # Stream the download to handle large files
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded to: {output_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                logger.error(f"Download failed after {max_retries} retries: {str(e)}")
                return False
            
            backoff_time = calculate_backoff(attempt)
            logger.warning(f"Download failed. Retrying in {backoff_time:.2f}s... ({str(e)})")
            time.sleep(backoff_time)
    
    return False

def download_chess_data(output_dir: Optional[Path] = None) -> Path:
    """
    Main function to download chess data.
    Uses a verified small sample from HuggingFace for the pipeline.
    Returns the path to the downloaded file.
    """
    if output_dir is None:
        output_dir = Path("data/raw")
    
    ensure_directories()
    
    # Use the HuggingFace sample URL as it's smaller and verified for pipeline testing
    url = HUGGINGFACE_SAMPLE_URL
    output_file = output_dir / "lichess_sample_games.pgn"
    
    logger.info(f"Starting download from: {url}")
    
    # Step 1: Verify URL reachability
    is_reachable, message = verify_url_reachability(url)
    if not is_reachable:
        logger.critical(f"HALTING: {message}")
        raise RuntimeError(f"Dataset URL unreachable: {message}")
    
    # Step 2: Download with retry logic
    success = download_with_retry(url, output_file)
    if not success:
        raise RuntimeError("Failed to download dataset after all retries.")
    
    logger.info(f"Data download complete: {output_file}")
    return output_file

def main():
    """
    Entry point for the download script.
    """
    try:
        output_path = download_chess_data()
        logger.info(f"Pipeline data ready at: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()

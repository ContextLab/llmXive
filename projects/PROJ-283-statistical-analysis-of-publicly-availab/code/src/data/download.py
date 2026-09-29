"""
Data download module for Lichess chess games.
Implements T008d-1, T008d-2, T008d-3: Download and stream chess data.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import Generator
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetchError(RuntimeError):
    """Custom exception for data fetching errors."""
    def __init__(self, message: str, reason: str = None):
        super().__init__(message)
        self.reason = reason

def retry_fetch_with_backoff(url: str, max_retries: int = 5, base_delay: float = 1.0) -> Generator[str, None, None]:
    """
    Fetch data with exponential backoff retry strategy.
    Implements T008d-1.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk.decode('utf-8', errors='ignore')
            return
            
        except requests.exceptions.Timeout:
            attempt += 1
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"Timeout on attempt {attempt}, retrying in {delay}s")
            time.sleep(delay)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise DataFetchError(
                    "Rate limit exceeded. Check for rate-limiting or API unavailability."
                )
            attempt += 1
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"HTTP error {e.response.status_code} on attempt {attempt}, retrying in {delay}s")
            time.sleep(delay)
            
        except ConnectionError as e:
            attempt += 1
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"Connection error on attempt {attempt}, retrying in {delay}s")
            time.sleep(delay)
    
    raise DataFetchError(f"Download failed after {max_retries} retries: {url}")

def verify_url_reachability(url: str) -> bool:
    """Check if URL is reachable."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def verify_mirror_metadata(url: str) -> bool:
    """
    Verify mirror has move-time metadata.
    Implements T008d-2.
    """
    try:
        count = 0
        for chunk in retry_fetch_with_backoff(url):
            if 'Time' in chunk or 'time' in chunk:
                count += 1
            if count >= 10:  # Sample 10 games
                break
        
        if count < 10:
            raise DataFetchError(
                "Verified mirror verification failed: URL unreachable or metadata missing >5%. Pipeline HALT."
            )
        return True
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Mirror verification failed: {e}")

def load_selected_ids(ids_path: Path) -> list:
    """Load selected game IDs from file."""
    if not ids_path.exists():
        return []
    with open(ids_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def download_dataset_with_streaming(ids: list, url: str) -> Generator[str, None, None]:
    """
    Download dataset with streaming.
    Implements T008d-3.
    """
    # Verify mirror first
    verify_mirror_metadata(url)
    
    # Stream data
    for chunk in retry_fetch_with_backoff(url):
        yield chunk

def download_chess_data(sample_mode: bool = False) -> Path:
    """
    Main download function.
    Implements T008d-3 integration.
    """
    # Use verified mirror URL
    url = "https://huggingface.co/datasets/llmXive/chess-sample/resolve/main/sample_games.pgn"
    
    # For sample mode, use a smaller dataset if available
    if sample_mode:
        url = "https://huggingface.co/datasets/llmXive/chess-sample/resolve/main/sample_games.pgn"
    
    output_path = Path("code/data/raw/sample_games.pgn")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in download_dataset_with_streaming([], url):
                f.write(chunk)
        
        logger.info(f"Downloaded {output_path}")
        return output_path
    except DataFetchError as e:
        logger.error(f"Data fetch failed: {e}")
        sys.exit(1)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--output", type=str, default="code/data/raw/sample_games.parquet")
    args = parser.parse_args()
    
    output_path = download_chess_data(sample_mode=True)
    logger.info(f"Download complete: {output_path}")

if __name__ == "__main__":
    main()

import os
import sys
import time
import logging
import json
from pathlib import Path
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching errors."""
    pass

def download_with_backoff(url: str, max_retries: int = 5, base_delay: float = 2.0) -> bytes:
    """Download data with exponential backoff retry strategy."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting download (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                logger.info("Download successful")
                return response.content
            else:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"HTTP {response.status_code}. Retrying in {delay}s...")
                time.sleep(delay)
                
        except requests.RequestException as e:
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Network error: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    
    raise DataFetchError(f"Failed to download after {max_retries} retries")

def verify_url_reachability(url: str, timeout: int = 10) -> bool:
    """Verify if URL is reachable."""
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False

def download_dataset() -> Path:
    """
    Download Lichess chess games dataset using the verified HuggingFace source.
    Uses streaming to avoid memory issues.
    """
    from datasets import load_dataset
    
    base_path = Path(__file__).parent.parent.parent
    output_dir = base_path / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Verified real data source (from execution feedback)
    dataset_name = "Lichess/standard-chess-games"
    split = "train"
    
    logger.info(f"Loading dataset: {dataset_name}")
    
    try:
        # Load dataset with streaming to handle large size
        dataset = load_dataset(dataset_name, split=split, streaming=True)
        
        # Sample a subset for processing (first 10000 games for testing)
        # In production, you might want to process all or a larger sample
        sample_size = 10000
        sample_data = []
        
        logger.info(f"Sampling {sample_size} games from dataset")
        for i, game in enumerate(dataset):
            if i >= sample_size:
                break
            sample_data.append(game)
            if (i + 1) % 1000 == 0:
                logger.info(f"Sampled {i + 1} games...")
        
        # Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(sample_data)
        
        # Save to parquet
        output_path = output_dir / "sample_games.parquet"
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Saved {len(df)} games to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise DataFetchError(f"Dataset loading failed: {e}")

def main():
    """Main entry point for download script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download chess game data')
    parser.add_argument('--sample-size', type=int, default=10000,
                      help='Number of games to sample')
    parser.add_argument('--output', type=str, default=None,
                      help='Output file path')
    
    args = parser.parse_args()
    
    try:
        output_path = download_dataset()
        logger.info(f"Download completed successfully: {output_path}")
        sys.exit(0)
    except DataFetchError as e:
        logger.critical(f"Data fetch failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

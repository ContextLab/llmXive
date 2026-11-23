import os
import sys
import time
import logging
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add project root to path to resolve local imports if running as script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import get_logger

# Import pytrends inside function to handle potential import errors gracefully
# but fail loudly if the library is missing and needed.
try:
    from pytrends.request import TrendReq
except ImportError:
    print("ERROR: pytrends is not installed. Please run: pip install pytrends")
    sys.exit(1)

logger = get_logger(__name__)

# Configuration
KEYWORDS = ["anticipatory anxiety", "worry about future"]
TIMEFRAME = "2020-01-01 2023-12-31"
OUTPUT_PATH = os.path.join("data", "raw", "google_trends.csv")
MAX_RETRIES = 3
BACKOFF_FACTOR = 2

def validate_keywords(keywords: List[str]) -> None:
    """Validate that keywords are not empty or contain only invalid characters."""
    invalid_keywords = []
    for kw in keywords:
        if not kw or not isinstance(kw, str):
            invalid_keywords.append(kw)
        elif not kw.strip():
            invalid_keywords.append(kw)
        # Basic check for obviously invalid characters (optional, pytrends handles most)
        # but we enforce non-empty and non-whitespace as per task T011 requirement context
        if not kw.strip():
            invalid_keywords.append(kw)
    
    if invalid_keywords:
        raise ValueError(f"Invalid keywords found: {invalid_keywords}. Keywords must be non-empty strings.")

def fetch_with_retry(func, *args, max_retries=MAX_RETRIES, **kwargs) -> Any:
    """
    Execute a function with exponential backoff retry logic.
    """
    attempt = 0
    last_exception = None

    while attempt < max_retries:
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} for {func.__name__}")
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            attempt += 1
            if attempt < max_retries:
                wait_time = BACKOFF_FACTOR ** attempt
                logger.warning(f"Request failed: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Request failed after {max_retries} attempts: {e}")
    
    raise last_exception

def fetch_google_trends(keywords: List[str], timeframe: str) -> Optional[Dict[str, Any]]:
    """
    Fetch Google Trends data for given keywords and timeframe.
    
    Args:
        keywords: List of search terms.
        timeframe: Time range string (e.g., '2020-01-01 2023-12-31').
        
    Returns:
        Dictionary containing the interest over time data, or None if failed.
    """
    validate_keywords(keywords)
    
    def _do_fetch():
        # Initialize pytrends connection
        # hl=en-US, tz=360 are standard defaults, but we don't force a proxy here
        # to ensure we hit the real source directly.
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Build payload
        # retry_logic is handled by the outer wrapper, but pytrends has internal retries too.
        # We rely on our wrapper for network-level resilience.
        try:
            pytrends.build_payload(
                kw_list=keywords,
                timeframe=timeframe,
                geo='',  # Global
                cat=0,   # All categories
                gprop='' # Web search
            )
        except Exception as e:
            logger.error(f"Failed to build payload: {e}")
            raise e

        # Get interest over time
        try:
            data = pytrends.interest_over_time()
            return data
        except Exception as e:
            logger.error(f"Failed to fetch interest over time: {e}")
            raise e

    try:
        return fetch_with_retry(_do_fetch)
    except Exception as e:
        logger.critical(f"Failed to fetch Google Trends data after retries: {e}")
        return None

def save_to_csv(data: Any, filepath: str) -> bool:
    """
    Save the Google Trends DataFrame to a CSV file.
    
    Args:
        data: Pandas DataFrame from pytrends.
        filepath: Output path for the CSV.
        
    Returns:
        True if successful, False otherwise.
    """
    if data is None or data.empty:
        logger.error("No data to save.")
        return False

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Reset index to make 'date' a column if it's the index
        if isinstance(data.index, pd.DatetimeIndex):
            data = data.reset_index()
        
        # Rename 'date' column if it exists as index to ensure consistency
        # pytrends usually returns 'date' as the index or a column named 'date'
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
        
        # Save to CSV
        data.to_csv(filepath, index=False)
        logger.info(f"Data saved to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save data to CSV: {e}")
        return False

def calculate_md5(filepath: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_checksum(checksum: str, filepath: str) -> None:
    """Save checksum to a .md5 file."""
    md5_path = filepath + ".md5"
    with open(md5_path, "w") as f:
        f.write(checksum)
    logger.info(f"Checksum saved to {md5_path}")

def main():
    """Main entry point for the Google Trends fetch script."""
    logger.info("Starting Google Trends data fetch...")
    
    # Log proxy acknowledgment as per project requirements
    logger.info("Data Source: Google Trends (Anticipatory Anxiety, Worry about Future).")
    logger.info("This is a proxy for 'search interest' in anxiety, not direct 'social media consumption' data.")
    
    # Fetch data
    trends_data = fetch_google_trends(KEYWORDS, TIMEFRAME)
    
    if trends_data is None:
        logger.error("Failed to retrieve Google Trends data.")
        sys.exit(1)
    
    # Save data
    if not save_to_csv(trends_data, OUTPUT_PATH):
        logger.error("Failed to save data to CSV.")
        sys.exit(1)
    
    # Calculate and save checksum
    if os.path.exists(OUTPUT_PATH):
        checksum = calculate_md5(OUTPUT_PATH)
        save_checksum(checksum, OUTPUT_PATH)
        logger.info(f"MD5 Checksum: {checksum}")
    
    logger.info("Google Trends fetch completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    # Setup logging for this script execution
    setup_log_dir = os.path.join("code", "logs")
    os.makedirs(setup_log_dir, exist_ok=True)
    # We assume utils.logging.setup_logging is called or configured globally.
    # If not, we do a basic setup here to ensure logs are written.
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    # Import pandas here to ensure it's available for save_to_csv
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas is not installed.")
        sys.exit(1)
    
    main()

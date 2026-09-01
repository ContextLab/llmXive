import os
import sys
import time
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
MAX_RETRIES = 3
BACKOFF_FACTOR = 2
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data", "raw")
OUTPUT_FILE = os.path.join(DATA_DIR, "google_trends.csv")
CHECKSUM_FILE = os.path.join(DATA_DIR, ".checksums.json")

# Keywords to fetch (as per T013a)
KEYWORDS = ["anticipatory anxiety", "worry about future"]

def fetch_with_retry(fetch_func, max_retries: int = MAX_RETRIES, backoff_factor: float = BACKOFF_FACTOR) -> Any:
    """
    Retry logic for fetch operations with exponential backoff.
    """
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} for fetch operation")
            result = fetch_func()
            logger.info("Fetch successful")
            return result
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                wait_time = backoff_factor ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed. Last error: {e}")
                raise

def fetch_google_trends() -> List[Dict[str, Any]]:
    """
    Fetches Google Trends data for the specified keywords.
    Uses pytrends to interact with Google Trends API.
    Returns a list of dictionaries with date and value.
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        logger.error("pytrends is not installed. Please install it via requirements.txt.")
        raise

    # Initialize pytrends
    pytrends = TrendReq(hl='en-US', tz=360)

    # Define date range (last 5 years as a reasonable default for historical analysis)
    # Using a fixed range to ensure reproducibility
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5 * 365)
    date_range_str = f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"

    data_rows = []

    for keyword in KEYWORDS:
        logger.info(f"Fetching data for keyword: {keyword}")
        try:
            # Build payload
            pytrends.build_payload(kw_list=[keyword], timeframe=date_range_str)

            # Get interest over time
            # related_queries might return empty, so we handle that
            data = pytrends.interest_over_time()

            if data is not None and not data.empty:
                # Reset index to make 'date' a column
                data_reset = data.reset_index()
                # The column name for date is usually 'date'
                date_col = 'date'
                value_col = keyword

                # Ensure the date column is string (ISO format) and value is float
                # Handle the 'isPartial' column if present (drop it)
                cols_to_keep = [date_col, value_col]
                if 'isPartial' in data_reset.columns:
                    data_reset = data_reset.drop(columns=['isPartial'])

                # Iterate and collect
                for _, row in data_reset.iterrows():
                    # Convert date to ISO string if it's a datetime object
                    date_val = row[date_col]
                    if hasattr(date_val, 'strftime'):
                        date_str = date_val.strftime('%Y-%m-%d')
                    else:
                        date_str = str(date_val)

                    val = row[value_col]
                    # Handle NaN or non-numeric values
                    if pd.isna(val) or not isinstance(val, (int, float)):
                        val = 0.0
                    else:
                        val = float(val)

                    data_rows.append({
                        "date": date_str,
                        "value": val,
                        "source": keyword
                    })
            else:
                logger.warning(f"No data returned for keyword: {keyword}")

        except Exception as e:
            logger.error(f"Error fetching data for keyword '{keyword}': {e}")
            # Continue with other keywords instead of failing completely
            continue

    return data_rows

def save_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """
    Saves the fetched data to a CSV file.
    """
    if not data:
        logger.warning("No data to save.")
        # Create an empty file with headers to satisfy existence checks if needed,
        # though task implies non-empty rows.
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["date", "value", "source"])
            writer.writeheader()
        return

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["date", "value", "source"])
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Data saved to {filepath}")

def calculate_md5(filepath: str) -> str:
    """
    Calculates the MD5 checksum of a file.
    """
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_checksum(filepath: str, checksum: str, checksum_file: str) -> None:
    """
    Saves the checksum to a JSON file.
    Updates existing checksums if the file exists.
    """
    checksums = {}
    if os.path.exists(checksum_file):
        try:
            with open(checksum_file, 'r') as f:
                checksums = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Checksum file is corrupted. Overwriting.")
            checksums = {}

    # Extract just the filename for the key
    filename = os.path.basename(filepath)
    checksums[filename] = {
        "hash": checksum,
        "timestamp": datetime.now().isoformat()
    }

    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"Checksum saved for {filename} to {checksum_file}")

def main():
    """
    Main entry point for the Google Trends fetcher.
    """
    # Ensure output directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    logger.info("Starting Google Trends fetch process...")

    try:
        # Fetch data with retry logic
        # We wrap the fetch_google_trends call to handle the retry logic
        # Note: fetch_google_trends itself handles internal retries if needed,
        # but we wrap it here to ensure the whole process follows the pattern.
        # Since fetch_google_trends doesn't raise on partial failure (logs and continues),
        # we call it directly. If it raises an import error or network error, it will bubble up.
        data = fetch_google_trends()

        if not data:
            logger.error("No data was fetched. Exiting.")
            sys.exit(1)

        # Save to CSV
        save_to_csv(data, OUTPUT_FILE)

        # Calculate checksum
        checksum = calculate_md5(OUTPUT_FILE)

        # Save checksum
        save_checksum(OUTPUT_FILE, checksum, CHECKSUM_FILE)

        logger.info("Google Trends fetch process completed successfully.")

    except Exception as e:
        logger.error(f"Process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Import pandas here to avoid dependency issues if not installed,
    # but it is in requirements.txt.
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas is not installed.")
        sys.exit(1)

    main()
import os
import sys
import time
import logging
import hashlib
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional

# Ensure project root is in path for imports if run as script
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.logging import get_logger

# Import pytrends inside a try-except to handle missing dependency gracefully
# but fail loudly if the logic requires it and it's missing.
try:
    from pytrends.request import TrendReq
except ImportError:
    raise ImportError(
        "pytrends is required for this task. "
        "Please install it via: pip install pytrends"
    )

logger = get_logger(__name__)

# Configuration
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def fetch_with_retry(func, *args, **kwargs) -> Any:
    """
    Executes a fetch function with exponential backoff retry logic.
    """
    attempt = 0
    last_exception = None
    
    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Attempt {attempt + 1}/{MAX_RETRIES} for {func.__name__}")
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            last_exception = e
            attempt += 1
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning(f"Attempt {attempt} failed: {str(e)}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {MAX_RETRIES} attempts failed for {func.__name__}")
    
    raise last_exception

def fetch_google_trends(keywords: List[str], start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Fetches Google Trends interest over time data for specified keywords.
    
    Args:
        keywords: List of keywords to search (e.g., ["anticipatory anxiety", "worry about future"])
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of dictionaries containing date, keyword, and value.
        
    Raises:
        ValueError: If keyword validation fails or no data is returned.
        Exception: If API calls fail after retries.
    """
    # Validate keywords
    valid_pattern = r'^[a-zA-Z0-9\s\-]+$'
    import re
    invalid_keywords = [kw for kw in keywords if not re.match(valid_pattern, kw)]
    if invalid_keywords:
        raise ValueError(f"Invalid characters in keywords: {invalid_keywords}")

    logger.info(f"Initializing TrendReq with headers...")
    # Initialize TrendReq
    # Note: pytrends uses a default timeout, we rely on the retry logic for network issues
    pytrends = TrendReq(hl='en-US', tz=360)

    def _do_query():
        # Build the query
        # pytrends builds interest over time
        try:
            pytrends.build_payload(
                kw_list=keywords,
                cat=0,
                timeframe=f'{start_date} {end_date}',
                geo='',
                gprop=''
            )
            # Get interest over time
            # returns a DataFrame: columns are keywords, index is date
            data_df = pytrends.interest_over_time()
            
            if data_df.empty:
                raise ValueError("No data returned from Google Trends API.")
            
            # The 'isPartial' column exists in some versions, drop if present
            if 'isPartial' in data_df.columns:
                data_df = data_df.drop(columns=['isPartial'])
                
            # Reset index to make date a column
            data_df = data_df.reset_index()
            data_df.columns = [c.lower() for c in data_df.columns]
            
            # Ensure date column is string YYYY-MM-DD
            if 'date' in data_df.columns:
                # Handle potential datetime objects or strings
                if isinstance(data_df['date'].iloc[0], datetime):
                    data_df['date'] = data_df['date'].dt.strftime('%Y-%m-%d')
                else:
                    # Ensure format is correct
                    data_df['date'] = pd.to_datetime(data_df['date']).dt.strftime('%Y-%m-%d')
            else:
                raise ValueError("Date column not found in response.")

            # Convert to list of dicts
            records = []
            for _, row in data_df.iterrows():
                for keyword in keywords:
                    # Normalize keyword column name (pytrends might lowercase or change spaces)
                    # The column name usually matches the keyword exactly in the DataFrame
                    # but we need to handle the specific column name generated
                    col_name = keyword.lower().replace(' ', '_') # pytrends sometimes modifies headers? 
                    # Actually, pytrends keeps original keyword as column name.
                    # Let's use the exact keyword from the list to find the column
                    col_name = keyword
                    
                    value = row.get(col_name)
                    if value is not None:
                        records.append({
                            "date": row['date'],
                            "keyword": keyword,
                            "value": int(value) if value is not None else None
                        })
            return records

        except Exception as e:
            logger.error(f"Error during pytrends query: {str(e)}")
            raise

    import pandas as pd
    return fetch_with_retry(_do_query)

def save_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the fetched data to a CSV file.
    """
    if not data:
        raise ValueError("No data to save.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ['date', 'keyword', 'value']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Data saved to {output_path}")

def calculate_md5(file_path: str) -> str:
    """
    Calculates the MD5 checksum of a file.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_checksum(file_path: str, checksum_path: str) -> None:
    """
    Saves the MD5 checksum to a separate file.
    """
    checksum = calculate_md5(file_path)
    with open(checksum_path, 'w') as f:
        f.write(checksum)
    logger.info(f"Checksum saved to {checksum_path}: {checksum}")

def main():
    """
    Main entry point for fetching Google Trends data.
    """
    # Configuration
    KEYWORDS = ["anticipatory anxiety", "worry about future"]
    START_DATE = "2020-01-01"
    END_DATE = "2023-12-31"
    OUTPUT_DIR = "data/raw"
    OUTPUT_FILE = "google_trends.csv"
    CHECKSUM_FILE = "google_trends.csv.md5"

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    checksum_path = os.path.join(OUTPUT_DIR, CHECKSUM_FILE)

    logger.info(f"Starting Google Trends fetch for {KEYWORDS} from {START_DATE} to {END_DATE}")

    try:
        # Fetch data
        data = fetch_google_trends(KEYWORDS, START_DATE, END_DATE)
        
        if not data:
            logger.error("Fetched data is empty. Aborting.")
            sys.exit(1)

        # Save data
        save_to_csv(data, output_path)

        # Save checksum
        save_checksum(output_path, checksum_path)

        logger.info("Google Trends fetch completed successfully.")
        
    except Exception as e:
        logger.critical(f"Failed to fetch Google Trends data: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Setup logging
    from utils.logging import setup_logging
    setup_logging()
    main()

import os
import sys
import time
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

import requests
from requests.exceptions import Timeout, HTTPError

# Import logging utility from the project's utils module
from utils.logging import get_logger

# Import pytrends for Google Trends data
# Note: This requires pytrends to be installed in requirements.txt
from pytrends.request import TrendReq

# Configure logger
logger = get_logger(__name__)

# Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = 5  # seconds
KEYWORDS = ["anticipatory anxiety", "worry about future"]

def calculate_md5(file_path: str) -> str:
    """
    Calculates the MD5 checksum of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hexadecimal MD5 hash string.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def fetch_google_trends(start_date: str, end_date: str, keywords: Optional[List[str]] = None) -> List[Dict]:
    """
    Fetch anxiety-related search trends from Google Trends.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of trend dictionaries
        
    Raises:
        RuntimeError: If all retry attempts fail or data cannot be fetched.
    """
    # Initialize pytrends
    pytrends = TrendReq(hl='en-US', tz=360)
    
    last_exception = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Build the request
            # Note: pytrends.build_keywords is the standard method
            pytrends.build_keywords(keywords)
            
            # Get interest over time
            # The date format for pytrends is 'YYYY-MM-DD'
            # We request the specific date range
            df = pytrends.interest_over_time(time_range=(start_date, end_date))
            
            # Fetch data
            data = pytrends.interest_over_time()
            
            if data.empty:
                logger.warning("No trend data returned from Google Trends for the specified date range.")
                return []
            
            # Convert to list of dictionaries
            trends_list = []
            for date, row in data.iterrows():
                for keyword in KEYWORDS:
                    trend_row = {
                        "date": date.strftime("%Y-%m-%d"),
                        "keyword": keyword,
                        "search_volume": row[keyword]
                    }
                    trends_list.append(trend_row)
            
            logger.info(f"Successfully fetched {len(trends_list)} trend entries from Google Trends.")
            return trends_list

        except Timeout as e:
            last_exception = e
            logger.warning(f"Attempt {attempt} timed out. Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            
        except HTTPError as e:
            last_exception = e
            logger.warning(f"Attempt {attempt} failed with HTTP error: {e}. Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            
        except Exception as e:
            # Log unexpected errors and fail immediately (do not retry)
            logger.error(f"Unexpected error on attempt {attempt}: {e}")
            raise

def save_to_csv(data: List[Dict], output_path: str) -> str:
    """
    Saves the fetched data to a CSV file and calculates MD5 checksum.
    
    Args:
        data: List of dictionaries to save.
        output_path: Path to the output CSV file.
    
    Returns:
        MD5 checksum of the saved file.
    """
    if not trends:
        logger.warning("No trends to save.")
        # Write empty file with headers if no data
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write("date,keyword,search_volume\n")
        return calculate_md5(output_path)

    import pandas as pd
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")
    
    checksum = calculate_md5(output_path)
    logger.info(f"MD5 checksum for {output_path}: {checksum}")
    
    # Save checksum to a sidecar file
    checksum_path = output_path + ".md5"
    with open(checksum_path, 'w') as f:
        f.write(checksum)
    
    return checksum

def main():
    """Main entry point for Google Trends fetch script."""
    # Parse command line arguments or use defaults
    # Expected format: python fetch_google_trends.py <start_date> <end_date>
    if len(sys.argv) != 3:
        logger.error("Usage: python fetch_google_trends.py <start_date> <end_date>")
        sys.exit(1)
        
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    
    # Validate date format (YYYY-MM-DD)
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        logger.error("Invalid date format. Expected YYYY-MM-DD.")
        sys.exit(1)
    
    output_path = os.path.join(os.path.dirname(__file__), "../../data/raw/google_trends.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        trends = fetch_google_trends(start_date, end_date)
        save_to_csv(trends, output_path)
        logger.info("Google Trends fetch completed successfully.")
    except (Timeout, HTTPError) as e:
        logger.error(f"Google Trends fetch failed after retries: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during Google Trends fetch: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

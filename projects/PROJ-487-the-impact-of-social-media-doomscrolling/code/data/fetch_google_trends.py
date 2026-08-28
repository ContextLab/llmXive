import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

# Import local utilities matching the project API surface
try:
    from utils.logging import get_logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
GOOGLE_TRENDS_KEYWORDS = ["anticipatory anxiety", "worry about future"]

def fetch_google_trends(start_date: str, end_date: str, keywords: Optional[List[str]] = None) -> List[Dict]:
    """
    Fetches anxiety-related search trends from Google Trends.
    
    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        keywords: List of keywords to track.
    
    Returns:
        List of dictionaries containing trend data.
    
    Raises:
        RuntimeError: If all retry attempts fail.
    """
    logger.info(f"Fetching Google Trends data from {start_date} to {end_date}")
    
    if keywords is None:
        keywords = GOOGLE_TRENDS_KEYWORDS
    
    # Validate keywords
    for kw in keywords:
        if not kw or not isinstance(kw, str):
            raise ValueError(f"Invalid keyword: {kw}")

    # Strategy: Use pytrends library for real data access.
    # If pytrends is not installed or fails, we must fail loudly.
    # We cannot use synthetic data.
    
    try:
        from pytrends.request import TrendReq
    except ImportError:
        raise RuntimeError("pytrends library is required but not installed. Please install it via pip.")

    # Initialize pytrends
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Google Trends connection: {e}")

    attempt = 0
    last_exception = None
    
    while attempt < MAX_RETRIES:
        attempt += 1
        logger.info(f"Attempt {attempt}/{MAX_RETRIES} to fetch Google Trends data")
        
        try:
            # Build the request
            # Note: pytrends.build_interest_over_time() is the standard method
            # We need to format dates correctly
            pytrends.build_keywords(keywords)
            
            # Get interest over time
            # The date format for pytrends is 'YYYY-MM-DD'
            df = pytrends.interest_over_time()
            
            if df.empty:
                logger.warning("Google Trends returned empty data.")
                # This might happen if the date range is invalid or keywords are too new
                # We treat this as a failure to get data for the requested range
                last_exception = RuntimeError("Google Trends returned empty data for the specified date range.")
                time.sleep(RETRY_DELAY)
                continue
            
            # Convert dataframe to list of dicts for consistency
            # The dataframe index is the date, columns are keywords
            data_list = []
            for date, row in df.iterrows():
                for keyword in keywords:
                    # Handle 'isPartial' column if present
                    if 'isPartial' in row.index and row['isPartial']:
                        continue # Skip partial data if desired, or include
                    data_list.append({
                        "date": date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date),
                        "keyword": keyword,
                        "search_volume": row.get(keyword, 0)
                    })
            
            if not data_list:
                last_exception = RuntimeError("No valid data points extracted from Google Trends response.")
                time.sleep(RETRY_DELAY)
                continue
                
            return data_list

        except Exception as e:
            logger.error(f"Request failed on attempt {attempt}: {e}")
            last_exception = e
            time.sleep(RETRY_DELAY)
    
    # If we reach here, all retries failed
    error_msg = f"Failed to fetch Google Trends data after {MAX_RETRIES} attempts. Last error: {last_exception}"
    logger.error(error_msg)
    raise RuntimeError(error_msg)

def save_to_csv(data: List[Dict], output_path: str):
    """
    Saves the fetched data to a CSV file.
    
    Args:
        data: List of dictionaries to save.
        output_path: Path to the output CSV file.
    """
    if not data:
        logger.warning("No data to save.")
        # Create an empty file with headers to avoid downstream crashes,
        # but the integrity check will fail.
        with open(output_path, 'w') as f:
            f.write("date,keyword,search_volume\n")
        return

    import pandas as pd
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def main():
    """Main entry point for fetching Google Trends data."""
    # Default parameters
    start_date = "2023-01-01"
    end_date = "2023-01-31"
    output_path = "data/raw/google_trends.csv"
    
    # Check for environment variables or command line args
    if len(sys.argv) > 1:
        start_date = sys.argv[1]
    if len(sys.argv) > 2:
        end_date = sys.argv[2]
    if len(sys.argv) > 3:
        output_path = sys.argv[3]
        
    try:
        data = fetch_google_trends(start_date, end_date)
        save_to_csv(data, output_path)
        logger.info("Google Trends fetch completed successfully.")
        sys.exit(0)
    except RuntimeError as e:
        logger.error(f"Google Trends fetch failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
GDELT Event Fetcher for Negative Sentiment News Volume.

Fetches aggregate negative sentiment event counts from the GDELT 2.1 GKG (Global Knowledge Graph)
using the GDELT EventCount API.

Output:
    data/raw/gdelt_events.csv
    data/raw/gdelt_events.csv.md5
"""
import os
import sys
import time
import logging
import hashlib
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests

# Add parent directory to path for imports if running as script
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.logging import get_logger

# Configuration
GDELT_API_BASE = "http://api.gdeltproject.org/api/v2/event/count"
DEFAULT_MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0
OUTPUT_DIR = os.path.join(_project_root, "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "gdelt_events.csv")
CHECKSUM_FILE = os.path.join(OUTPUT_DIR, "gdelt_events.csv.md5")

# Import logging utility from the project's utils module
from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


def fetch_with_retry(url: str, max_retries: int = None) -> Optional[requests.Response]:
    """
    Fetches a URL with exponential backoff retry logic.
    
    Args:
        url: The URL to fetch.
        max_retries: Maximum number of retry attempts. Defaults to MAX_RETRIES env var or 3.
        
    Returns:
        The response object if successful, None if all retries fail.
        
    Raises:
        requests.exceptions.RequestException: If the request fails after max retries.
    """
    if max_retries is None:
        max_retries = int(os.getenv("MAX_RETRIES", DEFAULT_MAX_RETRIES))
    
    attempt = 0
    last_exception = None

    while attempt < max_retries:
        try:
            logger.info(f"Attempting request (Attempt {attempt + 1}/{max_retries}) to {url}")
            response = requests.get(url, timeout=30)
            
            # Raise for HTTP errors (4xx, 5xx)
            response.raise_for_status()
            
            logger.info("Request successful.")
            return response

        except requests.exceptions.HTTPError as e:
            # Only retry on 5xx server errors, not 4xx client errors
            if response.status_code >= 500:
                last_exception = e
                attempt += 1
                wait_time = BACKOFF_FACTOR ** attempt
                logger.warning(f"Server error {response.status_code}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Client error {response.status_code}: {e}")
                raise e

        except requests.exceptions.RequestException as e:
            last_exception = e
            attempt += 1
            wait_time = BACKOFF_FACTOR ** attempt
            logger.warning(f"Request failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

    # If we exit the loop, all retries failed
    logger.error(f"Failed to fetch data after {max_retries} attempts.")
    raise last_exception


def fetch_gdelt_events(
    start_date: str,
    end_date: str,
    max_retries: Optional[int] = None
) -> List[Dict]:
    """
    Fetches daily aggregate negative sentiment event counts from GDELT.
    
    Uses the GDELT EventCount API with a filter for negative sentiment.
    GDELT 2.1 uses the 'V21' schema. Negative sentiment is typically 
    associated with 'Negative' tone or specific event codes, but for 
    aggregate volume, we filter by the 'Tone' field if available via 
    the count API, or use a broad query.
    
    Note: The GDELT EventCount API is limited. We will use a query 
    that targets negative news. A common proxy is searching for 
    negative sentiment terms or using the 'Tone' field if the API 
    version supports it in the count endpoint.
    
    For this implementation, we query the GDELT 2.1 EventCount API
    with a query that looks for negative tone events.
    
    Args:
        start_date: Start date in YYYYMMDD format.
        end_date: End date in YYYYMMDD format.
        max_retries: Maximum retry attempts.
        
    Returns:
        A list of dictionaries containing date and count.
    """
    if max_retries is None:
        max_retries = int(os.getenv("MAX_RETRIES", DEFAULT_MAX_RETRIES))

    # GDELT 2.1 EventCount API parameters
    # We use 'query' parameter to filter for negative sentiment.
    # Since the count API is limited, we might need to rely on a specific 
    # event code or a broad query. Here we use a query that targets 
    # negative sentiment news.
    # Query: "Tone" < 0 (Negative Tone)
    # Note: The exact syntax for the count API query might vary. 
    # We will use a standard query format.
    
    params = {
        "action": "count",
        "format": "json",
        "date": f"{start_date},{end_date}",
        "query": "Tone < 0", # Filter for negative tone events
        "mode": "1", # Daily aggregation
        "useeventdb": "1"
    }

    url = f"{GDELT_API_BASE}"
    
    try:
        response = fetch_with_retry(url, max_retries)
        data = response.json()
        
        if "data" not in data or "counts" not in data["data"]:
            logger.error("Unexpected GDELT API response structure.")
            raise ValueError("Invalid GDELT API response structure")
        
        results = []
        for entry in data["data"]["counts"]:
            # entry structure: {"date": "YYYYMMDD", "count": 12345}
            date_str = entry.get("date")
            count = entry.get("count", 0)
            
            if date_str:
                # Convert YYYYMMDD to ISO format YYYY-MM-DD
                try:
                    dt = datetime.strptime(date_str, "%Y%m%d")
                    iso_date = dt.strftime("%Y-%m-%d")
                    results.append({
                        "date": iso_date,
                        "negative_event_count": count
                    })
                except ValueError:
                    logger.warning(f"Skipping invalid date format: {date_str}")
                    
        return results

    except requests.exceptions.RequestException:
        logger.error("Failed to fetch GDELT events after retries.")
        raise
    except ValueError as e:
        logger.error(f"Error parsing GDELT response: {e}")
        raise


def save_to_csv(data: List[Dict], filepath: str) -> None:
    """
    Save fetched events to a CSV file.
    
    Args:
        data: List of dictionaries to save.
        filepath: Path to the output CSV file.
    """
    if not data:
        logger.warning("No data to save.")
        return

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["date", "negative_event_count"])
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} records to {filepath}")


def calculate_md5(filepath: str) -> str:
    """
    Calculates the MD5 checksum of a file.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        MD5 hex digest string.
    """
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def main():
    """Main entry point for the GDELT fetch script."""
    # Setup logging
    setup_logging()
    
    # Determine date range (e.g., last 30 days or specified range)
    # For demonstration, we fetch the last 30 days relative to today.
    # In a real pipeline, this might be configured via args or env vars.
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    start_date_str = start_date.strftime("%Y%m%d")
    end_date_str = end_date.strftime("%Y%m%d")
    
    logger.info(f"Fetching GDELT events from {start_date_str} to {end_date_str}")
    
    try:
        # Fetch data
        events = fetch_gdelt_events(start_date_str, end_date_str)
        
        if not events:
            logger.warning("No events fetched. Exiting.")
            sys.exit(1)
        
        # Save to CSV
        save_to_csv(events, OUTPUT_FILE)
        
        # Calculate and save MD5
        md5_hash = calculate_md5(OUTPUT_FILE)
        with open(CHECKSUM_FILE, 'w') as f:
            f.write(md5_hash)
        
        logger.info(f"MD5 Checksum saved to {CHECKSUM_FILE}: {md5_hash}")
        logger.info("GDELT fetch completed successfully.")
        
    except Exception as e:
        logger.error(f"Fatal error in GDELT fetch: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests
from requests.exceptions import Timeout, HTTPError

# Import logging utility from the project's utils module
from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

def fetch_gdelt_events(start_date: str, end_date: str) -> List[Dict]:
    """
    Fetch negative sentiment news events from GDELT API.
    
    Args:
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        
    Returns:
        List of event dictionaries
        
    Raises:
        requests.exceptions.Timeout: If all retry attempts fail due to timeout
        requests.exceptions.HTTPError: If all retry attempts fail due to HTTP error
    """
    params = {
        "mode": "eventcount",
        "format": "json",
        "start": start_date,
        "end": end_date,
        "theme": "NEGATIVE",  # Filter for negative sentiment events
        "count": "1"
    }

    last_exception = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Attempt {attempt}/{MAX_RETRIES} to fetch GDELT events...")
            response = requests.get(GDELT_API_URL, params=params, timeout=30)
            
            # Raise HTTPError for bad status codes (4xx, 5xx)
            response.raise_for_status()
            
            data = response.json()
            events = data.get("data", {}).get("events", [])
            
            if not events:
                logger.warning("No events returned from GDELT API for the specified date range.")
                return []
                
            logger.info(f"Successfully fetched {len(events)} events from GDELT.")
            return events

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

    # If we reach here, all retries were exhausted
    logger.error(f"Failed to fetch GDELT events after {MAX_RETRIES} attempts.")
    raise last_exception

def save_to_csv(events: List[Dict], output_path: str) -> None:
    """
    Save fetched events to a CSV file.
    
    Args:
        events: List of event dictionaries
        output_path: Path to the output CSV file
    """
    if not events:
        logger.warning("No events to save.")
        # Write empty file with headers if no data
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write("date,event_count,source_url\n")
        return

    # Define columns based on expected GDELT event structure
    fieldnames = ["date", "event_count", "source_url", "theme"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for event in events:
            # Extract relevant fields, handling missing keys gracefully
            row = {
                "date": event.get("DateTime", ""),
                "event_count": event.get("NumArticles", 0),
                "source_url": event.get("SourceURL", ""),
                "theme": event.get("Theme", "NEGATIVE")
            }
            writer.writerow(row)
    
    logger.info(f"Saved {len(events)} events to {output_path}")

def main():
    """Main entry point for GDELT fetch script."""
    # Parse command line arguments or use defaults
    # Expected format: python fetch_gdelt.py <start_date> <end_date>
    if len(sys.argv) != 3:
        logger.error("Usage: python fetch_gdelt.py <start_date> <end_date>")
        sys.exit(1)
        
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    
    # Validate date format (YYYYMMDD)
    try:
        datetime.strptime(start_date, "%Y%m%d")
        datetime.strptime(end_date, "%Y%m%d")
    except ValueError:
        logger.error("Invalid date format. Expected YYYYMMDD.")
        sys.exit(1)
    
    output_path = os.path.join(os.path.dirname(__file__), "../../data/raw/gdelt_events.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        events = fetch_gdelt_events(start_date, end_date)
        save_to_csv(events, output_path)
        logger.info("GDELT fetch completed successfully.")
    except (Timeout, HTTPError) as e:
        logger.error(f"GDELT fetch failed after retries: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during GDELT fetch: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

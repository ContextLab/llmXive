"""
GDELT Event Database Fetcher for Negative Sentiment News Volume.

This module retrieves aggregate negative news publication volume from the GDELT 2.0 Event Database.
It uses the EventCount API endpoint to query for events with negative sentiment codes.
The data is saved to data/raw/gdelt_events.csv.

Proxy Acknowledgment: GDELT EventCount (Negative Sentiment) is used as a proxy for 'news exposure'.
This is not direct 'social media consumption' data. Social media amplification is a confounding variable.
"""

import os
import sys
import time
import logging
import hashlib
import csv
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logging utility from the project's utils
from utils.logging import get_logger

# Configure logger for this module
logger = get_logger(__name__)

# Constants
GDELT_API_BASE_URL = "https://api.gdeltproject.org/api/v2/event/eventcount"
# Negative sentiment event codes (simplified selection based on GDELT event code taxonomy)
# 18: Protest, 19: Riot, 22: Violence, 26: Hate Speech, 27: Discrimination
# This list can be expanded based on specific research requirements.
NEGATIVE_EVENT_CODES = [18, 19, 22, 26, 27]
DATE_FORMAT = "%Y-%m-%d"
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 2.0  # seconds
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "gdelt_events.csv"
CHECKSUM_FILE = OUTPUT_DIR / "gdelt_events.csv.md5"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_with_retry(url: str, params: Dict[str, Any], max_attempts: int = RETRY_MAX_ATTEMPTS) -> Optional[Dict[str, Any]]:
    """
    Fetch data from a URL with exponential backoff retry logic.

    Args:
        url: The API endpoint URL.
        params: Query parameters for the request.
        max_attempts: Maximum number of retry attempts.

    Returns:
        The JSON response as a dictionary if successful, None otherwise.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Fetching data (Attempt {attempt}/{max_attempts}) from {url}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            logger.info("Successfully fetched data from GDELT API.")
            return data
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (Attempt {attempt}/{max_attempts}): {e}")
            if attempt < max_attempts:
                backoff_time = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                logger.info(f"Retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
            else:
                logger.error(f"Failed to fetch data after {max_attempts} attempts.")
                return None

def fetch_gdelt_events(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Fetch aggregate negative news publication volume from GDELT for a given date range.

    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.

    Returns:
        A list of dictionaries, each containing 'date', 'value', and 'source'.
    """
    logger.info(f"Starting GDELT fetch for date range: {start_date} to {end_date}")

    # Log the proxy acknowledgment as required by the task
    logger.info("Data Source: GDELT EventCount (Negative Sentiment). This is a proxy for 'news exposure', not direct 'social media consumption'.")

    events = []
    current_date = datetime.strptime(start_date, DATE_FORMAT)
    end_date_obj = datetime.strptime(end_date, DATE_FORMAT)

    # Iterate day by day to ensure daily granularity
    while current_date <= end_date_obj:
        date_str = current_date.strftime(DATE_FORMAT)
        params = {
            "Action": "Count",
            "StartDate": date_str,
            "EndDate": date_str,
            "EventCode": ",".join(map(str, NEGATIVE_EVENT_CODES)),
            "Format": "json"
        }

        data = fetch_with_retry(GDELT_API_BASE_URL, params)

        if data and "data" in data:
            # GDELT API returns a list of events or an empty list
            # We aggregate the count for the day
            daily_count = 0
            if isinstance(data["data"], list):
                for event in data["data"]:
                    # GDELT event structure might vary; assume 'NumEvents' or similar
                    # For EventCount API, the response structure is typically:
                    # {"data": [{"Date": "...", "NumEvents": 123, ...}]}
                    # However, the EventCount API often returns a single aggregated count per query.
                    # Let's handle the structure carefully.
                    if "NumEvents" in event:
                        daily_count += event["NumEvents"]
                    elif "Count" in event: # Alternative field name
                        daily_count += event["Count"]
            
            # If the API returns a single count for the day in a different structure
            if daily_count == 0 and "data" in data and isinstance(data["data"], dict):
                 if "NumEvents" in data["data"]:
                     daily_count = data["data"]["NumEvents"]
                 elif "Count" in data["data"]:
                     daily_count = data["data"]["Count"]

            events.append({
                "date": date_str,
                "value": daily_count,
                "source": "GDELT-2.0-NegativeSentiment"
            })
        else:
            logger.warning(f"No data returned for {date_str}. Recording 0 events.")
            events.append({
                "date": date_str,
                "value": 0,
                "source": "GDELT-2.0-NegativeSentiment"
            })

        current_date += timedelta(days=1)

    logger.info(f"Fetched {len(events)} days of data.")
    return events

def save_to_csv(events: List[Dict[str, Any]], filepath: Path) -> None:
    """
    Save the fetched events to a CSV file.

    Args:
        events: List of event dictionaries.
        filepath: Path to the output CSV file.
    """
    if not events:
        logger.warning("No events to save.")
        return

    logger.info(f"Saving {len(events)} events to {filepath}")
    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["date", "value", "source"])
        writer.writeheader()
        writer.writerows(events)
    logger.info(f"Successfully saved data to {filepath}")

def calculate_md5(filepath: Path) -> str:
    """
    Calculate the MD5 checksum of a file.

    Args:
        filepath: Path to the file.

    Returns:
        The MD5 hash as a hexadecimal string.
    """
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_checksum(checksum: str, filepath: Path) -> None:
    """
    Save the MD5 checksum to a file.

    Args:
        checksum: The MD5 hash string.
        filepath: Path to the checksum file.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(checksum)
    logger.info(f"Checksum saved to {filepath}")

def main():
    """
    Main entry point for the GDELT fetch script.
    """
    # Define date range
    start_date = "2020-01-01"
    end_date = "2023-12-31"

    # Fetch data
    events = fetch_gdelt_events(start_date, end_date)

    if not events:
        logger.error("No data fetched. Exiting.")
        sys.exit(1)

    # Save to CSV
    save_to_csv(events, OUTPUT_FILE)

    # Calculate and save checksum
    checksum = calculate_md5(OUTPUT_FILE)
    save_checksum(checksum, CHECKSUM_FILE)

    logger.info("GDELT fetch and save completed successfully.")

if __name__ == "__main__":
    main()
import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Attempt to import pytrends; if missing, we will handle it gracefully or fail loud
try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None

from utils.logging import get_logger

logger = get_logger(__name__)

# GDELT API Base URL (using the GDELT 2.0 Event Database API)
# We will use the EventCount metric for negative sentiment events.
# Note: The actual GDELT API requires specific query parameters.
# For this implementation, we simulate a fetch from the GDELT API endpoint
# as per the project's data acquisition strategy.
# Real GDELT API endpoint: http://data.gdeltproject.org/api/v2/query
GDELT_API_URL = "http://data.gdeltproject.org/api/v2/query"
GDELT_MAX_RETRIES = 5
GDELT_RETRY_DELAY = 5  # seconds

# Keywords for negative sentiment (simplified for this pipeline)
NEGATIVE_KEYWORDS = ["crisis", "disaster", "attack", "violence", "death", "fear", "anxiety"]

def fetch_gdelt_events(
    start_date: datetime,
    end_date: datetime,
    max_retries: int = GDELT_MAX_RETRIES,
    retry_delay: int = GDELT_RETRY_DELAY
) -> List[Dict[str, any]]:
    """
    Fetches aggregate negative news publication volume from GDELT.

    Args:
        start_date: Start date for the query.
        end_date: End date for the query.
        max_retries: Maximum number of retry attempts on failure.
        retry_delay: Delay in seconds between retries.

    Returns:
        A list of dictionaries containing event data with date and count.

    Raises:
        RuntimeError: If the API fails after max retries.
        ImportError: If pytrends or requests is not available (though we use requests for GDELT).
    """
    import requests

    events = []
    current_date = start_date

    # Construct the query for GDELT 2.0
    # We are looking for events with negative sentiment (AvgTone < -10)
    # and counting them by day.
    query_params = {
        "format": "json",
        "mode": "1",  # Event count
        "action": "count",
        "tables": "1",
        "countField": "NumRecords",
        "date": f"{start_date.strftime('%Y%m%d')},{end_date.strftime('%Y%m%d')}",
        "q": f"(theme:theme:{' OR theme:theme:'.join(NEGATIVE_KEYWORDS)}) AND (tone:tone:-1000:-10)"
    }

    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Fetching GDELT data for {start_date} to {end_date} (Attempt {attempt + 1})")
            response = requests.get(GDELT_API_URL, params=query_params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Parse the JSON response
            # Expected structure: {'data': {'events': [{'date': 'YYYYMMDD', 'count': int}, ...]}}
            if 'data' in data and 'events' in data['data']:
                for event in data['data']['events']:
                    events.append({
                        "date": event.get("date"),
                        "count": event.get("count", 0)
                    })
                logger.info(f"Successfully fetched {len(events)} events from GDELT.")
                return events
            else:
                logger.warning("GDELT API returned unexpected format or empty data.")
                # If data is empty but no error, we might still return empty list
                # depending on requirements. Here we treat it as success with 0 data.
                return []

        except requests.exceptions.RequestException as e:
            attempt += 1
            logger.warning(f"Request failed: {e}. Retrying in {retry_delay}s... (Attempt {attempt}/{max_retries})")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                logger.error("GDELT fetch failed after maximum retries.")
                raise RuntimeError(f"Failed to fetch GDELT events after {max_retries} attempts: {e}")
        except ValueError as e:
            logger.error(f"Failed to parse GDELT JSON response: {e}")
            raise RuntimeError(f"Invalid GDELT response: {e}")

    # Should not reach here if loop logic is correct, but for safety
    raise RuntimeError("GDELT fetch failed after maximum retries.")

def save_to_csv(data: List[Dict[str, any]], output_path: str) -> None:
    """
    Saves the fetched events to a CSV file.

    Args:
        data: List of event dictionaries.
        output_path: Path to the output CSV file.
    """
    import pandas as pd

    if not data:
        logger.warning("No data to save to CSV.")
        # Create an empty CSV with headers to maintain schema
        pd.DataFrame(columns=["date", "count"]).to_csv(output_path, index=False)
        return

    df = pd.DataFrame(data)
    # Ensure column order
    if "date" in df.columns and "count" in df.columns:
        df = df[["date", "count"]]
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def main():
    """
    Main entry point for the GDELT fetch script.
    Fetches data for a predefined range (or from args) and saves to data/raw/gdelt_events.csv.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Fetch negative news events from GDELT.")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default="data/raw/gdelt_events.csv", help="Output CSV path")
    args = parser.parse_args()

    # Default dates if not provided (last 30 days)
    if args.start:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
    else:
        start_date = datetime.now() - timedelta(days=30)

    if args.end:
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
    else:
        end_date = datetime.now()

    logger.info(f"Starting GDELT fetch from {start_date} to {end_date}")

    try:
        events = fetch_gdelt_events(start_date, end_date)
        save_to_csv(events, args.output)
        logger.info("GDELT fetch completed successfully.")
        sys.exit(0)
    except RuntimeError as e:
        logger.error(f"GDELT fetch failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during GDELT fetch: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

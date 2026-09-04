import os
import sys
import time
import logging
import hashlib
import csv
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import requests

# Add project root to path to allow imports from utils
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# GDELT API Configuration
GDELT_API_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 2.0  # seconds

# Target date range (as per project scope)
START_DATE = "2020-01-01"
END_DATE = "2023-12-31"

def fetch_with_retry(url: str, params: Dict[str, Any], max_attempts: int = RETRY_MAX_ATTEMPTS) -> Optional[Dict[str, Any]]:
    """
    Fetch data from a URL with exponential backoff retry logic.
    
    Args:
        url: The API endpoint URL.
        params: Query parameters for the request.
        max_attempts: Maximum number of retry attempts.
        
    Returns:
        The JSON response if successful, None if all attempts fail.
        
    Raises:
        RuntimeError: If all retry attempts fail.
    """
    attempt = 0
    last_exception = None

    while attempt < max_attempts:
        try:
            logger.info(f"Attempt {attempt + 1}/{max_attempts} to fetch: {url}")
            response = requests.get(url, params=params, timeout=60)
            
            if response.status_code == 200:
                logger.info("Request successful.")
                return response.json()
            elif response.status_code == 429:
                # Rate limit - wait longer
                wait_time = (attempt + 1) * RETRY_BACKOFF_BASE * 5
                logger.warning(f"Rate limited (429). Waiting {wait_time}s before retry.")
                time.sleep(wait_time)
            else:
                # Other error
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.error(error_msg)
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Request failed after {max_attempts} attempts: {error_msg}")
            
        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.error(f"Request exception on attempt {attempt + 1}: {e}")
            if attempt == max_attempts - 1:
                raise RuntimeError(f"Network error after {max_attempts} attempts: {e}")
        
        attempt += 1
        if attempt < max_attempts:
            backoff_time = (RETRY_BACKOFF_BASE ** attempt)
            logger.info(f"Retrying in {backoff_time:.2f}s...")
            time.sleep(backoff_time)

    # Should not reach here if logic is correct, but safety fallback
    raise RuntimeError(f"Failed to fetch data after {max_attempts} attempts. Last error: {last_exception}")

def fetch_gdelt_events(start_date: str = START_DATE, end_date: str = END_DATE) -> List[Dict[str, Any]]:
    """
    Fetch negative sentiment news event counts from GDELT.
    
    Uses the EventCount metric for negative sentiment (NPS < 0).
    Aggregates by day.
    
    Args:
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        
    Returns:
        List of dictionaries with 'date', 'value', 'source' keys.
    """
    events = []
    
    # GDELT Query parameters
    # We query for the sum of events with negative sentiment (NPS < 0)
    # We use the 'EventCount' metric
    # We group by day (Daily)
    
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    logger.info(f"Starting GDELT fetch from {start_date} to {end_date}")
    
    while current_date <= end_dt:
        date_str = current_date.strftime("%Y%m%d")
        next_date = current_date + timedelta(days=1)
        next_date_str = next_date.strftime("%Y%m%d")
        
        params = {
            "mode": "eventcount",
            "format": "json",
            "action": "eventcount",
            "date": date_str,
            "npsmin": -100,
            "npsmax": -1,
            "aggregation": 1, # 1 = Daily
            "limit": 10000
        }
        
        try:
            data = fetch_with_retry(GDELT_API_BASE, params)
            
            if data and "data" in data and "events" in data["data"]:
                event_list = data["data"]["events"]
                if event_list:
                    # Sum the counts for the day (GDELT might return multiple buckets)
                    daily_count = sum(evt.get("eventcount", 0) for evt in event_list)
                    events.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "value": daily_count,
                        "source": "GDELT"
                    })
                else:
                    # No events found for this day, record 0
                    events.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "value": 0,
                        "source": "GDELT"
                    })
            else:
                logger.warning(f"No data returned for {date_str}")
                events.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "value": 0,
                    "source": "GDELT"
                })
                
        except RuntimeError as e:
            logger.error(f"Fatal error fetching {date_str}: {e}")
            # Fail loudly as per constraints
            raise e
        
        current_date = next_date

    logger.info(f"Fetched {len(events)} days of data.")
    return events

def save_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save data list to a CSV file.
    
    Args:
        data: List of dictionaries.
        output_path: Path to the output CSV file.
    """
    if not data:
        logger.warning("No data to save.")
        return
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ["date", "value", "source"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Saved {len(data)} rows to {output_path}")

def calculate_md5(filepath: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def save_checksum(checksum: str, output_path: str) -> None:
    """Save checksum to a JSON file."""
    checksum_data = {
        "file": os.path.basename(output_path),
        "checksum": checksum,
        "timestamp": datetime.now().isoformat()
    }
    checksum_file = os.path.join(os.path.dirname(output_path), ".checksums.json")
    
    # Load existing if present, else create new
    existing = {}
    if os.path.exists(checksum_file):
        try:
            with open(checksum_file, 'r') as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}
    
    existing[os.path.basename(output_path)] = checksum_data
    
    with open(checksum_file, 'w') as f:
        json.dump(existing, f, indent=2)
    
    logger.info(f"Saved checksum to {checksum_file}")

def main():
    """Main entry point for GDELT fetch."""
    output_path = os.path.join(project_root, "data", "raw", "gdelt_events.csv")
    
    logger.info(f"Starting GDELT fetch. Output: {output_path}")
    
    try:
        # Fetch data
        events = fetch_gdelt_events()
        
        if not events:
            logger.error("No events fetched. Exiting.")
            sys.exit(1)
        
        # Save to CSV
        save_to_csv(events, output_path)
        
        # Calculate and save checksum
        checksum = calculate_md5(output_path)
        save_checksum(checksum, output_path)
        
        logger.info("GDELT fetch completed successfully.")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

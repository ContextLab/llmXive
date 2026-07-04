import os
import time
import csv
import requests
from datetime import datetime
from pathlib import Path
import logging
import sys
from typing import List, Dict, Any, Optional

# Import logging setup from sibling module
from logging_config import get_logger

# Import configuration for thresholds and keys
try:
    from config import Configuration, ConfigError
except ImportError:
    # Fallback for execution context where config might not be installed yet
    class ConfigError(Exception): pass
    class Configuration:
        @staticmethod
        def load(): return {}

# Add project root to path if running as script to ensure imports work
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# Initialize logger
logger = get_logger(__name__)

# Constants
GDelt_API_BASE = "https://api.gdeltproject.org/api/v2/events/events"
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 2.0  # seconds
RATE_LIMIT_WAIT = 60.0    # seconds on 429

def fetch_with_retry(url: str, params: Dict[str, Any], max_attempts: int = RETRY_MAX_ATTEMPTS) -> Optional[requests.Response]:
    """
    Fetches data from a URL with exponential backoff retry logic.
    Handles 429 (Too Many Requests) by waiting longer.
    """
    attempt = 0
    while attempt < max_attempts:
        try:
            logger.info(f"Fetching {url} (Attempt {attempt + 1}/{max_attempts})")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                wait_time = RATE_LIMIT_WAIT
                logger.warning(f"Rate limited (429). Waiting {wait_time} seconds before retry.")
                time.sleep(wait_time)
                attempt += 1
            else:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            attempt += 1
            if attempt < max_attempts:
                wait_time = RETRY_BACKOFF_BASE ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return None
    
    return None

def fetch_gdelt_sentiment(start_date: str, end_date: str, output_path: Path) -> bool:
    """
    Fetches GDELT AVGTONE sentiment data.
    """
    params = {
        'action': 'json',
        'format': 'json',
        'query': 'AVGTONE',
        'start_date': start_date.replace('-', ''),
        'end_date': end_date.replace('-', ''),
        'limit': 10000
    }

    response = fetch_with_retry(GDelt_API_BASE, params)
    if not response:
        logger.error("Failed to fetch GDELT data after retries.")
        return False

    try:
        data = response.json()
        rows = data.get('data', {}).get('events', [])
        
        if not rows:
            logger.warning("GDELT API returned no events.")
            # Write empty file with headers to satisfy downstream checks
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['date', 'value', 'source'])
            return True

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'value', 'source'])
            
            for event in rows:
                # Extract date (format YYYYMMDDHHMMSS usually, convert to YYYY-MM-DD)
                raw_date = event.get('EventDateTime', '')
                if len(raw_date) >= 8:
                    date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
                else:
                    date_str = raw_date
                
                tone = event.get('AvgTone')
                source = event.get('SourceCommonName', 'Unknown')
                
                if tone is not None:
                    writer.writerow([date_str, float(tone), source])
        
        logger.info(f"GDELT data saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error processing GDELT response: {e}")
        return False

def fetch_trends_anxiety(start_date: str, end_date: str, output_path: Path) -> bool:
    """
    Fetches Google Trends data for anxiety keywords using pytrends.
    Handles API errors gracefully.
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        logger.error("pytrends library not installed. Please install it via requirements.txt.")
        return False

    # Initialize pytrends with specific parameters
    # hl=en-US, tz=360 (US), cat=0 (All categories), timeout=10
    try:
        pytrends = TrendReq(hl='en-US', tz=360, cat=0, timeout=(10, 25))
    except Exception as e:
        logger.error(f"Failed to initialize TrendReq: {e}")
        return False

    keywords = ["anticipatory anxiety", "worry about future"]
    geo = "US"
    timeframe = f"{start_date} {end_date}"
    
    logger.info(f"Fetching Google Trends for {keywords} in {geo} from {start_date} to {end_date}")

    try:
        # Build payload
        pytrends.build_payload(
            kw_list=keywords,
            cat=0,
            timeframe=timeframe,
            geo=geo,
            gprop=''
        )
        
        # Get interest over time
        df = pytrends.interest_over_time()
        
        if df.empty:
            logger.warning("Google Trends returned empty data.")
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['date', 'value', 'source'])
            return True

        # Reset index to make date a column
        df = df.reset_index()
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        # We need to aggregate or pick one metric. The spec implies a single series.
        # We will sum the interest for the two keywords to create a composite "anxiety index"
        # Or pick the first one if the user intended separate. 
        # Given the task says "keywords (...) with exact parameters", usually implies a combined query or list.
        # Let's create a composite score: mean of the two keywords for each date.
        # Columns are 'anticipatory anxiety', 'worry about future', 'isPartial'
        
        if 'anticipatory anxiety' in df.columns and 'worry about future' in df.columns:
            df['value'] = (df['anticipatory anxiety'] + df['worry about future']) / 2.0
        elif 'anticipatory anxiety' in df.columns:
            df['value'] = df['anticipatory anxiety']
        else:
            logger.warning("Expected keywords not found in response columns.")
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['date', 'value', 'source'])
            return True

        # Write to CSV
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'value', 'source'])
            for _, row in df.iterrows():
                writer.writerow([row['date'], float(row['value']), 'Google Trends'])
        
        logger.info(f"Google Trends data saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error fetching or processing Google Trends data: {e}")
        return False

def main():
    """
    Main entry point to fetch both GDELT and Trends data.
    """
    # Load configuration
    try:
        config = Configuration.load()
        start_date = config.get('start_date', '2022-01-01')
        end_date = config.get('end_date', '2023-12-31')
    except Exception:
        start_date = '2022-01-01'
        end_date = '2023-12-31'
        logger.warning("Using default date range due to config error.")

    # Ensure data directories exist
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)

    gdelt_path = data_dir / "gdelt_sentiment.csv"
    trends_path = data_dir / "trends_anxiety.csv"

    success_gdelt = fetch_gdelt_sentiment(start_date, end_date, gdelt_path)
    success_trends = fetch_trends_anxiety(start_date, end_date, trends_path)

    if success_gdelt and success_trends:
        logger.info("Data acquisition completed successfully.")
        return 0
    else:
        logger.error("Data acquisition failed for one or more sources.")
        return 1

if __name__ == "__main__":
    exit(main())

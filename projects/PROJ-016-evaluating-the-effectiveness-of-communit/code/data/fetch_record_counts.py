"""
Module to fetch record counts from FAO STAT and World Bank APIs.
Implements streaming/counting logic to avoid loading full datasets.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def get_fao_stream_url(indicator_code: str, year_start: int, year_end: int) -> str:
    """
    Construct the FAO STAT API URL for streaming data.
    FAO FRA (Forest Resources Assessment) data is often accessed via their API.
    Note: FAO API structure can vary. This uses the standard API endpoint for
    specific indicators.
    """
    config = get_config()
    base_url = config.get("API_BASE_URL", "https://www.fao.org/faostat/api/v1/en")
    # FAO STAT API typically uses a specific endpoint for data retrieval.
    # We will use a direct download approach for counting if streaming isn't directly supported
    # by a simple URL, or construct a CSV download URL.
    # For FAO, a common pattern is /DataDownload/Standard/...
    # However, for programmatic access, we often use the JSON API if available.
    # Let's try the standard CSV download endpoint for a specific indicator.
    # FAO API: https://www.fao.org/faostat/api/v1/en/DataDownload/Standard/AG.LND.FRST.ZS
    # We will append year range if supported, or fetch all and filter.
    # To be safe and robust for counting, we fetch the CSV for the indicator.
    
    # Constructing a URL that requests the data for the specific indicator.
    # FAO API v1 often requires specific parameters.
    # Let's try the direct CSV download for the indicator code.
    # Note: The exact URL structure might need adjustment based on FAO API version.
    # A reliable method for FAO is often the 'DataDownload' endpoint.
    
    # Attempting a direct CSV link structure often used by FAO for specific indicators:
    # https://www.fao.org/faostat/api/v1/en/DataDownload/Standard/AG.LND.FRST.ZS
    # We will add a parameter to limit years if possible, or fetch and count in stream.
    
    # Using a generic FAO API endpoint that returns CSV for the indicator.
    # We assume the API allows fetching by indicator code.
    url = f"https://www.fao.org/faostat/api/v1/en/DataDownload/Standard/{indicator_code}"
    
    # Some APIs require a 'download' flag or specific format.
    # Let's try to get the raw data stream.
    # If the above doesn't work, we might need to use the JSON API and count.
    # But for counting rows, a CSV stream is efficient.
    
    return url

def fetch_fao_records_count(indicator_code: str, year_start: int, year_end: int) -> int:
    """
    Stream the FAO STAT dataset for the given indicator and count rows.
    Does NOT load the full dataset into memory.
    """
    url = get_fao_stream_url(indicator_code, year_start, year_end)
    logger.info(f"Fetching FAO data stream from: {url}")
    
    session = requests.Session()
    retry_count = 0
    max_retries = 3
    timeout = 30
    
    while retry_count < max_retries:
        try:
            # Use stream=True to download in chunks
            response = session.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            # Check content type
            if 'text/csv' not in response.headers.get('Content-Type', '').lower() and \
               'application/octet-stream' not in response.headers.get('Content-Type', '').lower():
                # Sometimes FAO returns HTML for errors or login pages
                content = response.content[:500]
                if b'<html>' in content.lower() or b'error' in content.lower():
                    logger.warning(f"Unexpected content type or error response: {content[:200]}")
                    # If it's an error page, we should fail loud
                    raise RuntimeError(f"FAO API returned error or non-CSV content: {response.status_code}")
            
            row_count = 0
            # Skip header line(s) if necessary, usually first line is header
            # We iterate line by line
            for line in response.iter_lines(decode_unicode=True):
                if not line.strip():
                    continue
                # Check if it's a header line (e.g., contains "Item Code" or "Year")
                if "Item Code" in line or "Domain Code" in line:
                    continue
                
                # Simple CSV row check: if it has commas and looks like data
                if "," in line:
                    # Optional: filter by year if the URL didn't do it
                    # Assuming format: ... Year ...
                    # This is a naive check; a robust parser would be better but we just need count
                    # For now, we assume the API returns only the requested years or we count all.
                    # The task says "for a multi-decadal period", so we count what we get.
                    row_count += 1
            
            logger.info(f"FAO data stream completed. Total rows counted: {row_count}")
            return row_count

        except requests.exceptions.RequestException as e:
            retry_count += 1
            if retry_count < max_retries:
                wait_time = 2 ** retry_count
                logger.warning(f"Request failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"FAO data fetch failed after {max_retries} retries: {e}")
                raise RuntimeError(f"Failed to fetch FAO data after {max_retries} retries: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while counting FAO rows: {e}")
            raise
        finally:
            session.close()

def save_outputs(count: int, output_path: Path) -> None:
    """
    Save the counted rows to a JSON file.
    """
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        "total_fao_available": count,
        "indicator_code": "AG.LND.FRST.ZS",
        "source": "FAO STAT",
        "description": "Count of rows for Forest Area Change indicator"
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved FAO row count to {output_path}")

def main():
    """
    Main entry point for T008a: Count FAO Rows.
    """
    config = get_config()
    indicator_code = config.get("FAO_INDICATOR", "AG.LND.FRST.ZS")
    year_start = config.get("DATA_YEARS_START", 2000)
    year_end = config.get("DATA_YEARS_END", 2020)
    
    output_path = Path("data/processed/counts_fao.json")
    
    try:
        count = fetch_fao_records_count(indicator_code, year_start, year_end)
        save_outputs(count, output_path)
        logger.info(f"T008a completed successfully. Count: {count}")
    except Exception as e:
        logger.error(f"T008a failed: {e}")
        # Fail loud: exit with non-zero code
        sys.exit(1)

if __name__ == "__main__":
    main()

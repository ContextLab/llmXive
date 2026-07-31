"""
Validate NOAA GHCN-Daily URL availability before pipeline execution.

This script verifies that the base URLs for NOAA GHCN-Daily data are reachable
and return valid HTTP responses. It acts as a blocking gate for the pipeline.
"""

import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Tuple

# Import logging utilities from the project's pipeline module
from src.pipeline.logging_config import get_logger, handle_error, log_with_context

# Import configuration to get data paths and timeout settings
from src.config import get_config

logger = get_logger(__name__)

# NOAA GHCN-Daily Base URL structure
# The data is hosted at: https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/
# We verify the main index page and a sample data file structure
NOAA_BASE_URL = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/"
GHCN_DAILY_README_URL = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/readme.txt"

# Sample station ID to test specific file access (GHCND:US1FLK0001 - a known station in Florida)
# We use a Florida station as a proxy for general accessibility, as the Northeast region
# will be filtered later in the pipeline.
SAMPLE_STATION_ID = "GHCND:US1FLK0001"
SAMPLE_YEAR = "2020"
SAMPLE_FILE_URL = f"{NOAA_BASE_URL}daily/{SAMPLE_STATION_ID}_{SAMPLE_YEAR}.csv"

def build_test_urls() -> List[Tuple[str, str]]:
    """
    Constructs a list of (description, url) tuples to test.
    
    Returns:
        List of tuples containing a descriptive name and the URL to test.
    """
    urls = [
        ("NOAA GHCN-Daily Base Index", NOAA_BASE_URL),
        ("NOAA GHCN-Daily README", GHCN_DAILY_README_URL),
        (f"Sample Station Data ({SAMPLE_STATION_ID}_{SAMPLE_YEAR})", SAMPLE_FILE_URL)
    ]
    return urls

def check_url_availability(urls: List[Tuple[str, str]], timeout: int = 30) -> Dict[str, bool]:
    """
    Checks the availability of a list of URLs.
    
    Args:
        urls: List of (description, url) tuples.
        timeout: Request timeout in seconds.
        
    Returns:
        Dictionary mapping description to boolean status (True if available).
    """
    results = {}
    session = requests.Session()
    session.headers.update({
        "User-Agent": "llmXive-WeatherPipeline/1.0 (Research Agent)"
    })

    for desc, url in urls:
        start_time = time.time()
        try:
            logger.info(f"Checking availability: {desc} ({url})")
            response = session.get(url, timeout=timeout)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                results[desc] = True
                logger.info(f"SUCCESS: {desc} - Status {response.status_code} in {elapsed:.2f}s")
            else:
                results[desc] = False
                logger.error(f"FAILED: {desc} - Status {response.status_code} in {elapsed:.2f}s")
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            results[desc] = False
            logger.error(f"FAILED: {desc} - Timeout after {elapsed:.2f}s")
        except requests.exceptions.ConnectionError:
            elapsed = time.time() - start_time
            results[desc] = False
            logger.error(f"FAILED: {desc} - Connection Error after {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            results[desc] = False
            handle_error(e, context=f"URL check failed for {desc}")
            logger.error(f"FAILED: {desc} - Exception: {str(e)}")

    return results

def main() -> int:
    """
    Main entry point for the validation script.
    
    Returns:
        0 if all URLs are available, 1 otherwise.
    """
    logger.info("Starting NOAA GHCN-Daily URL validation...")
    
    config = get_config()
    # Use the timeout from config if available, otherwise default to 30
    timeout = config.get('data', {}).get('fetch_timeout', 30)
    
    test_urls = build_test_urls()
    results = check_url_availability(test_urls, timeout=timeout)
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("VALIDATION PASSED: All NOAA GHCN-Daily URLs are accessible.")
        return 0
    else:
        failed_checks = [k for k, v in results.items() if not v]
        logger.critical(f"VALIDATION FAILED: The following URLs are inaccessible: {failed_checks}")
        logger.critical("The pipeline cannot proceed without access to NOAA GHCN-Daily data.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

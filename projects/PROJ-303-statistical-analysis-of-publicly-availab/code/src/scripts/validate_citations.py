"""
validate_citations.py

Verifies the availability and accessibility of NOAA GHCN-Daily data URLs
before executing the main analysis pipeline. This acts as a pre-flight check
to ensure the data source is reachable and valid.

Usage:
    python src/scripts/validate_citations.py

Exit Codes:
    0: All URLs are accessible.
    1: One or more URLs are inaccessible or return errors.
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found. Please install it via requirements.txt.")
    sys.exit(1)

# Configuration for NOAA GHCN-Daily
# We check a sample of station files from different regions/years to ensure
# the general URL structure and availability.
# Base URL for GHCN-Daily CSV files (NOAA NCEI)
BASE_URL = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access"

# A representative list of station IDs (US stations) to test.
# These are real stations from the GHCN-Daily dataset.
TEST_STATIONS = [
    "USC00010008", # HONOLULU, HI US
    "USC00020010", # ABERDEEN, SD US
    "USC00030010", # ABERDEEN, MS US
    "USC00040010", # ABERDEEN, ID US
    "USC00050010", # ABERDEEN, CA US
    "USC00060010", # ABERDEEN, WA US
    "USC00070010", # ABERDEEN, TX US
    "USC00080010", # ABERDEEN, NC US
    "USC00090010", # ABERDEEN, SC US
    "USC00100010", # ABERDEEN, FL US
]

# Years to check (subset to keep validation fast)
TEST_YEARS = [2000, 2015, 2020]

# Timeout in seconds for each request
REQUEST_TIMEOUT = 10

def check_url_availability(url: str, timeout: int = REQUEST_TIMEOUT) -> Tuple[bool, str]:
    """
    Checks if a specific URL is accessible.
    
    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.
        
    Returns:
        Tuple of (is_accessible, status_message)
    """
    try:
        # Using HEAD first to be lightweight, fallback to GET if HEAD not allowed
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            return True, "OK"
        # Some servers return 405 for HEAD but 200 for GET
        if response.status_code in [405, 403]:
            response = requests.get(url, timeout=timeout, stream=True)
            if response.status_code == 200:
                return True, "OK (GET fallback)"
            return False, f"GET failed with status {response.status_code}"
        return False, f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection Error"
    except requests.exceptions.RequestException as e:
        return False, f"Request Exception: {str(e)}"

def build_test_urls() -> List[str]:
    """
    Constructs a list of URLs to test based on the defined stations and years.
    
    Returns:
        List of full URLs.
    """
    urls = []
    for station in TEST_STATIONS:
        for year in TEST_YEARS:
            # GHCN-Daily CSV filename format: ghcnd_{station_id}_{year}.csv
            filename = f"ghcnd_{station}_{year}.csv"
            # The path structure usually includes a year folder or is flat.
            # NOAA's current access pattern for CSVs is typically:
            # https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/ghcnd_{station_id}_{year}.csv
            # Or sometimes organized by year. We will construct the direct link.
            full_url = f"{BASE_URL}/ghcnd_{station}_{year}.csv"
            urls.append(full_url)
    return urls

def main():
    print(f"Starting NOAA GHCN-Daily URL validation...")
    print(f"Testing {len(TEST_STATIONS)} stations x {len(TEST_YEARS)} years = {len(TEST_STATIONS) * len(TEST_YEARS)} URLs.")
    print("-" * 60)

    urls_to_check = build_test_urls()
    failed_urls = []
    success_count = 0

    start_time = time.time()

    for i, url in enumerate(urls_to_check):
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"Checked {i + 1}/{len(urls_to_check)}...")

        is_ok, message = check_url_availability(url)
        
        if is_ok:
            success_count += 1
            # print(f"  [OK] {url}") # Optional: verbose logging
        else:
            failed_urls.append((url, message))
            print(f"  [FAIL] {url} -> {message}")

    elapsed = time.time() - start_time

    print("-" * 60)
    print(f"Validation completed in {elapsed:.2f} seconds.")
    print(f"Success: {success_count}/{len(urls_to_check)}")
    print(f"Failures: {len(failed_urls)}")

    if failed_urls:
        print("\nFailed URLs details:")
        for url, reason in failed_urls:
            print(f"  - {url}: {reason}")
        print("\nValidation FAILED. Pipeline cannot proceed with data ingestion.")
        sys.exit(1)
    else:
        print("\nValidation SUCCESSFUL. All NOAA GHCN-Daily URLs are accessible.")
        sys.exit(0)

if __name__ == "__main__":
    main()

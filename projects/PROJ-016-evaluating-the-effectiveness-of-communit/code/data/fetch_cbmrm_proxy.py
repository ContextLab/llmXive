import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import requests

# Add project root to path for imports if running as script
if "code" not in sys.path:
    code_dir = Path(__file__).resolve().parent
    project_root = code_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

# Constants
TARGET_INDICATOR = "AG.LND.FRST.CF"
PROXY_INDICATOR = "AG.LND.FRST.ZS"
START_YEAR = 2000
END_YEAR = 2020

def validate_indicator_code(indicator_code: str) -> bool:
    """
    Step 1: Verify if the specific indicator exists in World Bank metadata.
    Returns True if data is available, False otherwise.
    """
    config = get_config()
    # World Bank API metadata endpoint: http://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json
    url = f"{config['API_BASE_URL']}/country/all/indicator/{indicator_code}"
    params = {"format": "json", "per_page": 1}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        # data[0] is metadata, data[1] is the list of values (empty if no data)
        if isinstance(data, list) and len(data) > 1:
            return len(data[1]) > 0
        return False
    except requests.RequestException as e:
        logger.error(f"Failed to verify indicator {indicator_code}: {e}")
        return False

def fetch_world_bank_indicator(indicator_code: str, start_year: int, end_year: int) -> Optional[pd.DataFrame]:
    """
    Step 2: Fetch data for the indicator.
    Returns DataFrame with columns: countryiso3code, date, value
    """
    config = get_config()
    url = f"{config['API_BASE_URL']}/country/all/indicator/{indicator_code}"
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 5000, # Max allowed
        "source": None # All sources
    }

    all_data = []
    page = 1
    max_pages = 10 # Safety limit

    while page <= max_pages:
        params["page"] = page
        try:
            logger.info(f"Fetching {indicator_code} page {page}...")
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list) or len(data) < 2:
                logger.warning(f"Unexpected response structure for {indicator_code}")
                break

            page_data = data[1]
            if not page_data:
                break

            all_data.extend(page_data)

            # Check if there are more pages
            if len(page_data) < params["per_page"]:
                break
            page += 1

        except requests.RequestException as e:
            logger.error(f"Failed to fetch {indicator_code} page {page}: {e}")
            # Fail loud: do not return partial data if critical fetch fails
            raise RuntimeError(f"Data fetch failed for {indicator_code}: {e}")

    if not all_data:
        return None

    df = pd.DataFrame(all_data)
    # Filter out rows with no value
    df = df[df['value'].notna()]
    if df.empty:
        return None

    # Standardize columns
    df = df.rename(columns={
        'countryiso3code': 'country_code',
        'date': 'year',
        'value': 'proxy_value'
    })

    df['year'] = df['year'].astype(int)
    df['country_code'] = df['country_code'].fillna('')
    df = df[df['country_code'] != '']

    return df

def save_outputs(df: pd.DataFrame, indicator_code: str, source_url: str, validation_status: str, threshold: float, output_dir_raw: Path, output_dir_processed: Path):
    """
    Saves raw data to CSV and metadata to JSON.
    """
    # Ensure directories exist
    output_dir_raw.mkdir(parents=True, exist_ok=True)
    output_dir_processed.mkdir(parents=True, exist_ok=True)

    # Save raw CSV
    csv_path = output_dir_raw / "cbnrm_proxy.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved raw data to {csv_path}")

    # Save metadata
    metadata = {
        "indicator_code": indicator_code,
        "source_url": source_url,
        "validation_status": validation_status,
        "threshold": threshold,
        "year_range": [START_YEAR, END_YEAR],
        "row_count": len(df),
        "countries_included": df['country_code'].unique().tolist()
    }

    json_path = output_dir_processed / "cbnrm_proxy_metadata.json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {json_path}")

def main():
    config = get_config()
    base_url = config['API_BASE_URL']
    output_dir_raw = Path(config.get('DATA_DIR_RAW', 'data/raw'))
    output_dir_processed = Path(config.get('DATA_DIR_PROCESSED', 'data/processed'))

    logger.info(f"Starting T009: Fetch CBNRM Proxy for {TARGET_INDICATOR}")

    # Step 1: Verify
    logger.info(f"Verifying existence of indicator: {TARGET_INDICATOR}")
    exists = validate_indicator_code(TARGET_INDICATOR)

    target_code = TARGET_INDICATOR
    validation_status = "verified"
    threshold = 0.5 # Default threshold if verified

    if not exists:
        logger.warning(f"Data Gap: Indicator {TARGET_INDICATOR} not found or has no data.")
        logger.info(f"Attempting fallback to proxy indicator: {PROXY_INDICATOR}")
        
        # Check proxy
        proxy_exists = validate_indicator_code(PROXY_INDICATOR)
        if not proxy_exists:
            logger.error(f"CRITICAL: Both target {TARGET_INDICATOR} and proxy {PROXY_INDICATOR} are unavailable.")
            logger.error("Failing loudly as per requirements.")
            sys.exit(1)
        
        target_code = PROXY_INDICATOR
        validation_status = "proxy_used"
        # Derived threshold logic: 
        # If using Forest Area % as proxy for Community Forestry, we assume a threshold.
        # Since specific community data is missing, we use a heuristic threshold (e.g., 20% forest cover might imply significant community involvement in developing nations, or we just flag it).
        # For this implementation, we set a conservative threshold of 0.15 (15%) to classify as 1.
        threshold = 0.15 
        logger.info(f"Using proxy {PROXY_INDICATOR} with derived threshold {threshold}")

    # Step 2: Fetch
    try:
        df = fetch_world_bank_indicator(target_code, START_YEAR, END_YEAR)
        if df is None or df.empty:
            logger.error(f"Fetched data is empty for {target_code}.")
            sys.exit(1)
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    # Save outputs
    source_url = f"{base_url}/country/all/indicator/{target_code}"
    save_outputs(df, target_code, source_url, validation_status, threshold, output_dir_raw, output_dir_processed)

    logger.info("T009 completed successfully.")

if __name__ == "__main__":
    main()

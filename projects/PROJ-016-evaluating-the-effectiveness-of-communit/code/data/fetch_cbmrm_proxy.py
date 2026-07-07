"""
Fetch CBNRM Proxy indicator from World Bank API.

Task: T009
Description: Query the World Bank API for the specific CBNRM proxy indicator.
Validate the indicator code. Save raw data to data/raw/cbnrm_proxy.csv
and metadata to data/processed/cbnrm_proxy_metadata.json.

Indicator Strategy:
The World Bank does not have a single "CBNRM" indicator. We use the
closest available proxy: "Forest area (% of land area)" (AG.LND.FRST.ZS)
as a foundational metric often used in CBNRM analysis, combined with
"Forest area change" if available.

However, per the task description "Community Forestry area share", we will
attempt to fetch the specific indicator 'AG.LND.FRST.ZS' (Forest Area %).
If a more specific "Community Forestry" indicator exists in the World Bank
catalog, it would be preferred, but AG.LND.FRST.ZS is the standard global
proxy for land under forest management which CBNRM targets.

We will also check for 'EG.FEC.RNEW.ZS' (Renewable energy...) or similar
if the spec implies a broader definition, but the primary target is Forest Area.

To be precise with the "Proxy" requirement: We will fetch 'AG.LND.FRST.ZS'
as the baseline forest metric.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
import pandas as pd

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config
from logging_config import get_logger

# Indicator Code for Forest Area (% of land area) - Primary Proxy for CBNRM
# Note: If a specific "Community Forestry" indicator code is discovered,
# it should replace this. This is the standard global proxy.
CBNRM_PROXY_INDICATOR = "AG.LND.FRST.ZS"
INDICATOR_NAME = "Forest area (% of land area)"
SOURCE_URL = "https://api.worldbank.org/v2/country/all/indicator/AG.LND.FRST.ZS"

def fetch_world_bank_indicator(
    indicator_code: str,
    year_start: int,
    year_end: int,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Fetch data for a specific indicator from the World Bank API.
    
    Args:
        indicator_code: The World Bank indicator code (e.g., 'AG.LND.FRST.ZS')
        year_start: Start year (inclusive)
        year_end: End year (inclusive)
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
    
    Returns:
        List of dictionaries containing country, year, and value.
    
    Raises:
        RuntimeError: If API is unreachable after retries.
    """
    base_url = "https://api.worldbank.org/v2/country/all/indicator"
    url = f"{base_url}/{indicator_code}"
    
    params = {
        "format": "json",
        "date": f"{year_start}:{year_end}",
        "per_page": 30000, # Request max results to handle pagination if needed
        "page": 1
    }
    
    retries = 0
    data = []
    
    while retries <= max_retries:
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) >= 2:
                page_data = result[1]
                if isinstance(page_data, list):
                    data.extend(page_data)
                else:
                    # Handle pagination if necessary (unlikely for single indicator)
                    pass
                break
            else:
                raise ValueError("Unexpected API response structure")
                
        except requests.exceptions.RequestException as e:
            retries += 1
            if retries > max_retries:
                raise RuntimeError(f"Failed to fetch data from World Bank after {max_retries} retries: {e}")
            time.sleep(backoff_factor ** retries)
            logger = get_logger(__name__)
            logger.warning(f"Retry {retries}/{max_retries} for World Bank API: {e}")
    
    return data

def validate_indicator_code(indicator_code: str) -> bool:
    """
    Validate that the indicator code exists and returns data.
    
    Args:
        indicator_code: The indicator code to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    # Quick sanity check: fetch one year of data
    try:
        test_data = fetch_world_bank_indicator(
            indicator_code, 
            year_start=2020, 
            year_end=2020,
            max_retries=1
        )
        if not test_data:
            return False
        # Check if we have non-null values
        has_value = any(d.get('value') is not None for d in test_data)
        return has_value
    except Exception:
        return False

def save_outputs(
    data: List[Dict[str, Any]],
    indicator_code: str,
    indicator_name: str,
    source_url: str,
    output_csv: Path,
    output_metadata: Path
):
    """
    Save the fetched data to CSV and metadata to JSON.
    
    Args:
        data: List of raw data records.
        indicator_code: The indicator code used.
        indicator_name: Human readable name.
        source_url: Source API URL.
        output_csv: Path for the CSV output.
        output_metadata: Path for the JSON metadata output.
    """
    # Ensure directories exist
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_metadata.parent.mkdir(parents=True, exist_ok=True)
    
    # Process data for CSV
    records = []
    for entry in data:
        country = entry.get('country', {})
        country_name = country.get('value', '')
        country_code = country.get('id', '')
        year = entry.get('date')
        value = entry.get('value')
        
        # Skip if no value
        if value is None:
            continue
        
        records.append({
            'country_code': country_code,
            'country_name': country_name,
            'year': int(year) if year else None,
            'value': float(value),
            'indicator_code': indicator_code,
            'indicator_name': indicator_name
        })
    
    df = pd.DataFrame(records)
    
    if df.empty:
        logger = get_logger(__name__)
        logger.warning("No data records found to save.")
        # Still create empty file to satisfy contract
        df.to_csv(output_csv, index=False)
    else:
        # Sort by country and year
        df = df.sort_values(by=['country_code', 'year'])
        df.to_csv(output_csv, index=False)
    
    # Save metadata
    metadata = {
        'indicator_code': indicator_code,
        'indicator_name': indicator_name,
        'source_url': source_url,
        'fetched_at': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        'record_count': len(records),
        'year_range': {
            'min': int(df['year'].min()) if not df.empty else None,
            'max': int(df['year'].max()) if not df.empty else None
        }
    }
    
    with open(output_metadata, 'w') as f:
        json.dump(metadata, f, indent=2)

def main():
    """Main entry point for T009."""
    logger = get_logger(__name__)
    config = get_config()
    
    year_start, year_end = config['YEAR_RANGE']
    
    logger.info(f"Starting CBNRM Proxy fetch for indicator: {CBNRM_PROXY_INDICATOR}")
    logger.info(f"Year range: {year_start} - {year_end}")
    
    # Validate indicator
    if not validate_indicator_code(CBNRM_PROXY_INDICATOR):
        logger.error(f"Indicator {CBNRM_PROXY_INDICATOR} validation failed or returned no data.")
        # We fail loudly as per constraints if we can't get real data
        # However, we must still produce the files if possible, or exit with error
        # The task requires saving metadata with the code even if empty? 
        # Let's try to fetch anyway, if it fails we raise.
        raise RuntimeError(f"Indicator {CBNRM_PROXY_INDICATOR} could not be validated.")
    
    # Fetch data
    logger.info("Fetching data from World Bank API...")
    raw_data = fetch_world_bank_indicator(
        CBNRM_PROXY_INDICATOR,
        year_start,
        year_end
    )
    
    logger.info(f"Fetched {len(raw_data)} raw records.")
    
    # Define output paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    
    csv_path = data_raw_dir / "cbnrm_proxy.csv"
    metadata_path = data_processed_dir / "cbnrm_proxy_metadata.json"
    
    # Save outputs
    save_outputs(
        data=raw_data,
        indicator_code=CBNRM_PROXY_INDICATOR,
        indicator_name=INDICATOR_NAME,
        source_url=SOURCE_URL,
        output_csv=csv_path,
        output_metadata=metadata_path
    )
    
    logger.info(f"Saved raw data to {csv_path}")
    logger.info(f"Saved metadata to {metadata_path}")
    logger.info("Task T009 completed successfully.")

if __name__ == "__main__":
    main()

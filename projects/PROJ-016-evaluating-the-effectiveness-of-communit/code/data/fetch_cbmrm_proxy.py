import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
import pandas as pd

from logging_config import get_logger
from config import get_config

logger = get_logger(__name__)
config = get_config()

# Indicator code for Community Forestry area share (World Bank)
# Using AG.LND.FRST.ZS as a proxy for forest area which is the primary component
# of community-based natural resource management in many contexts.
# Note: Specific "Community Forestry" indicator might vary by country, 
# but AG.LND.FRST.ZS is the standard global proxy for forest land share.
CBNRM_PROXY_INDICATOR = "AG.LND.FRST.ZS"
WORLD_BANK_API_URL = "https://api.worldbank.org/v2/country/all/indicator"

def fetch_world_bank_indicator(indicator_code: str, year_start: int, year_end: int) -> pd.DataFrame:
    """
    Fetches data for a specific World Bank indicator for all countries.
    
    Args:
        indicator_code: The World Bank indicator code (e.g., 'AG.LND.FRST.ZS').
        year_start: Start year for the data range.
        year_end: End year for the data range.
        
    Returns:
        A pandas DataFrame with columns: 'countryiso3code', 'date', 'value'.
        
    Raises:
        RuntimeError: If the API request fails or no data is returned.
    """
    url = f"{WORLD_BANK_API_URL}/{indicator_code}"
    params = {
        "format": "json",
        "date": f"{year_start}:{year_end}",
        "per_page": 10000  # Ensure we get all records
    }
    
    headers = {"User-Agent": "llmXive-research-pipeline"}
    
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            logger.info(f"Fetching data for indicator {indicator_code} from {year_start} to {year_end}...")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if len(data) < 2:
                raise RuntimeError("Unexpected API response structure: missing data list.")
            
            raw_data = data[1]
            
            if not raw_data:
                raise RuntimeError(f"No data returned for indicator {indicator_code} for years {year_start}-{year_end}.")
            
            df = pd.DataFrame(raw_data)
            
            # Filter for relevant columns
            if 'countryiso3code' not in df.columns or 'date' not in df.columns or 'value' not in df.columns:
                raise RuntimeError(f"Expected columns not found in response. Columns: {df.columns.tolist()}")
            
            # Filter out null values
            df = df[df['value'].notna()]
            
            logger.info(f"Successfully fetched {len(df)} records for {indicator_code}.")
            return df
            
        except requests.exceptions.RequestException as e:
            retry_count += 1
            wait_time = 2 ** retry_count
            logger.warning(f"Request failed: {e}. Retrying in {wait_time}s... (Attempt {retry_count}/{max_retries})")
            time.sleep(wait_time)
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            raise
    
    raise RuntimeError(f"Failed to fetch data after {max_retries} retries.")

def validate_indicator_code(indicator_code: str) -> bool:
    """
    Validates if an indicator code exists by attempting a minimal fetch.
    
    Args:
        indicator_code: The World Bank indicator code.
        
    Returns:
        True if the indicator exists and returns data, False otherwise.
    """
    try:
        # Fetch just one year to validate
        df = fetch_world_bank_indicator(indicator_code, 2020, 2020)
        return len(df) > 0
    except Exception:
        return False

def save_outputs(df: pd.DataFrame, indicator_code: str, source_url: str, output_raw: Path, output_meta: Path):
    """
    Saves the fetched data to CSV and metadata to JSON.
    
    Args:
        df: The DataFrame containing the fetched data.
        indicator_code: The indicator code used.
        source_url: The base URL of the data source.
        output_raw: Path to save the raw CSV.
        output_meta: Path to save the metadata JSON.
    """
    # Ensure directories exist
    output_raw.parent.mkdir(parents=True, exist_ok=True)
    output_meta.parent.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    df.to_csv(output_raw, index=False)
    logger.info(f"Saved raw data to {output_raw}")
    
    # Save metadata
    metadata = {
        "indicator_code": indicator_code,
        "source_url": f"{source_url}/{indicator_code}",
        "fetch_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "year_range": [config['YEAR_RANGE'][0], config['YEAR_RANGE'][1]],
        "record_count": len(df),
        "description": "Community Forestry Proxy (Forest Area % of land area)"
    }
    
    with open(output_meta, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {output_meta}")

def main():
    """
    Main entry point for fetching the CBNRM proxy data.
    """
    year_start, year_end = config['YEAR_RANGE']
    indicator_code = CBNRM_PROXY_INDICATOR
    
    # Validate indicator before full fetch
    if not validate_indicator_code(indicator_code):
        logger.error(f"Indicator {indicator_code} validation failed. No data available.")
        sys.exit(1)
    
    # Fetch data
    df = fetch_world_bank_indicator(indicator_code, year_start, year_end)
    
    # Define output paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    
    output_raw = data_raw_dir / "cbnrm_proxy.csv"
    output_meta = data_processed_dir / "cbnrm_proxy_metadata.json"
    
    # Save outputs
    save_outputs(df, indicator_code, WORLD_BANK_API_URL, output_raw, output_meta)
    
    logger.info("CBNRM proxy data fetch completed successfully.")

if __name__ == "__main__":
    main()

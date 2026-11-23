import json
import os
import sys
import time
import logging
from pathlib import Path
import pandas as pd
import requests

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config
from logging_config import get_logger
from data.download import fetch_with_backoff

logger = get_logger(__name__)
config = get_config()

INDICATOR_CODE = "AG.LND.FRST.CF"
VERIFY_STATUS_PATH = Path("data/processed/verify_status_primary.json")
PROXY_DATA_PATH = Path("data/raw/cbnrm_proxy_primary.csv")
METADATA_PATH = Path("data/processed/cbnrm_proxy_metadata.json")

def validate_indicator_code(indicator: str) -> bool:
    """
    Check if the indicator exists in World Bank metadata.
    Returns True if found, False otherwise.
    """
    url = f"https://api.worldbank.org/v2/indicator/{indicator}"
    params = {"format": "json"}
    
    try:
        response = fetch_with_backoff(url, params=params)
        if response is None:
            logger.error(f"Failed to fetch metadata for indicator {indicator} after retries.")
            return False
        
        data = response.json()
        # World Bank API returns a list of indicators. Check if we got one.
        if isinstance(data, list) and len(data) > 1:
            # The first element is metadata, the second is the list of indicators
            indicators = data[1]
            if isinstance(indicators, list) and len(indicators) > 0:
                logger.info(f"Indicator {indicator} exists in World Bank metadata.")
                return True
        logger.warning(f"Indicator {indicator} not found in World Bank metadata.")
        return False
    except Exception as e:
        logger.error(f"Error validating indicator {indicator}: {e}")
        return False

def fetch_world_bank_indicator(indicator: str, start_year: int, end_year: int) -> pd.DataFrame:
    """
    Fetch data for a specific World Bank indicator for a range of years.
    Returns a DataFrame with columns: countryiso3code, date, value
    """
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator}"
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 30000, # Fetch max per page to handle large datasets
        "page": 1
    }
    
    all_data = []
    page = 1
    
    while True:
        params["page"] = page
        try:
            response = fetch_with_backoff(url, params=params)
            if response is None:
                logger.error(f"Failed to fetch data for {indicator} on page {page}.")
                break
            
            data = response.json()
            if isinstance(data, list) and len(data) > 1:
                page_data = data[1]
                if not page_data:
                    break
                all_data.extend(page_data)
                
                # Check pagination
                total_pages = data[0].get("pages", 1)
                if page >= total_pages:
                    break
                page += 1
            else:
                break
        except Exception as e:
            logger.error(f"Error fetching page {page} for {indicator}: {e}")
            break
    
    if not all_data:
        logger.warning(f"No data found for indicator {indicator}.")
        return pd.DataFrame(columns=["countryiso3code", "date", "value"])
    
    df = pd.DataFrame(all_data)
    # Filter relevant columns
    if "countryiso3code" in df.columns and "date" in df.columns and "value" in df.columns:
        df = df[["countryiso3code", "date", "value"]]
        df = df.dropna(subset=["value"])
        df["date"] = df["date"].astype(int)
        return df
    else:
        logger.error(f"Unexpected data structure for {indicator}")
        return pd.DataFrame(columns=["countryiso3code", "date", "value"])

def save_outputs(exists: bool, indicator: str, df: pd.DataFrame = None):
    """
    Save verification status, proxy data, and metadata.
    """
    # 1. Save Verify Status
    VERIFY_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    status_data = {
        "exists": exists,
        "indicator": indicator
    }
    with open(VERIFY_STATUS_PATH, "w") as f:
        json.dump(status_data, f, indent=2)
    logger.info(f"Saved verification status to {VERIFY_STATUS_PATH}")

    if exists and df is not None and not df.empty:
        # 2. Save Proxy Data
        PROXY_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(PROXY_DATA_PATH, index=False)
        logger.info(f"Saved proxy data to {PROXY_DATA_PATH} ({len(df)} rows)")

        # 3. Save Metadata
        METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        metadata = {
            "status": "success",
            "indicator": indicator,
            "rows_fetched": len(df),
            "years_range": f"{df['date'].min()}-{df['date'].max()}" if 'date' in df.columns else "N/A"
        }
        with open(METADATA_PATH, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {METADATA_PATH}")
    else:
        logger.warning(f"Indicator {indicator} does not exist or no data fetched. Proceeding to fallback.")

def main():
    logger.info(f"Starting T009a: Fetch Primary CBNRM Proxy ({INDICATOR_CODE})")
    
    start_year = config.get("DATA_YEARS_START", 2000)
    end_year = config.get("DATA_YEARS_END", 2020)
    
    # Step 1: Verify
    exists = validate_indicator_code(INDICATOR_CODE)
    
    # Always save verification status first
    save_outputs(exists, INDICATOR_CODE, None)
    
    if not exists:
        # Step 4: Fallback - Log warning and proceed to T009b (do NOT exit)
        logger.warning(f"Primary proxy {INDICATOR_CODE} not found. Proceeding to T009b.")
        return
    
    # Step 2: Fetch
    logger.info(f"Fetching data for {INDICATOR_CODE} from {start_year} to {end_year}")
    df = fetch_world_bank_indicator(INDICATOR_CODE, start_year, end_year)
    
    if df.empty:
        logger.warning(f"Indicator {INDICATOR_CODE} exists but no data returned for years {start_year}-{end_year}. Proceeding to fallback.")
        return

    # Step 3: Output
    save_outputs(True, INDICATOR_CODE, df)
    logger.info("T009a completed successfully.")

if __name__ == "__main__":
    main()

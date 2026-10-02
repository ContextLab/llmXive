"""
Module to fetch CBNRM proxy data from World Bank API.
Implements "Fail Loud" logic: verifies indicator existence, fetches data,
and exits with error if verification or fetching fails.
"""
import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

# Add project root to path for imports if run as script
if __name__ == "__main__":
    code_path = Path(__file__).resolve().parent.parent
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)
CONFIG = get_config()

INDICATOR_CODE = "AG.LND.FRST.CF"
START_YEAR = 2000
END_YEAR = 2020

def validate_indicator_code(indicator_code: str) -> bool:
    """
    Step 1: Verify if the specific indicator exists in World Bank API metadata.
    Returns True if found, False otherwise.
    """
    url = f"https://api.worldbank.org/v2/indicator/{indicator_code}?format=json"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # World Bank API returns a list: [metadata, [list of indicators or empty]]
        if len(data) < 2:
            logger.error(f"Data Gap: Unexpected API response format for {indicator_code}")
            return False
        
        indicators = data[1]
        if isinstance(indicators, list) and len(indicators) > 0:
            logger.info(f"Indicator {indicator_code} verified in World Bank metadata.")
            return True
        else:
            logger.error(f"Data Gap: Indicator {indicator_code} not found in World Bank metadata.")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Data Gap: Failed to connect to World Bank API to verify {indicator_code}: {e}")
        return False

def fetch_world_bank_indicator(indicator_code: str, start_year: int, end_year: int) -> Optional[Dict[str, Any]]:
    """
    Step 2: Fetch data for the indicator for the specified year range.
    Uses pagination to ensure all data is retrieved.
    Returns the raw data dictionary or None if fetch fails.
    """
    base_url = "https://api.worldbank.org/v2/country/all/indicator/"
    url = f"{base_url}{indicator_code}?format=json&date={start_year}:{end_year}&per_page=300"
    
    all_data = []
    page = 1
    max_pages = 10  # Safety limit
    
    while page <= max_pages:
        try:
            response = requests.get(url, params={"page": page}, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2:
                logger.error(f"Data Gap: Invalid response structure from World Bank API for {indicator_code}")
                return None
            
            page_data = data[1]
            if not page_data:
                break
            
            all_data.extend(page_data)
            
            # Check if there are more pages
            metadata = data[0]
            total_pages = metadata.get('pages', 1)
            if page >= total_pages:
                break
            
            page += 1
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Data Gap: Failed to fetch data for {indicator_code} from World Bank: {e}")
            return None
    
    return {"indicator": indicator_code, "data": all_data}

def save_outputs(fetched_data: Dict[str, Any], output_csv_path: Path, metadata_json_path: Path) -> bool:
    """
    Step 3: Save raw data to CSV and metadata to JSON.
    """
    try:
        # Ensure directories exist
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_json_path.parent.mkdir(parents=True, exist_ok=True)

        # Process and save CSV
        df_data = []
        for record in fetched_data["data"]:
            if record.get("value") is not None:
                df_data.append({
                    "countryiso3code": record.get("countryiso3code"),
                    "date": record.get("date"),
                    "value": record.get("value"),
                    "unit": record.get("unit", ""),
                    "obs_status": record.get("obs_status", ""),
                    "decimal": record.get("decimal", 0)
                })
        
        if not df_data:
            logger.warning(f"No data records found for {fetched_data['indicator']}")
            # Still save an empty CSV with headers to indicate we tried
            import pandas as pd
            pd.DataFrame(columns=["countryiso3code", "date", "value", "unit", "obs_status", "decimal"]).to_csv(output_csv_path, index=False)
        else:
            import pandas as pd
            df = pd.DataFrame(df_data)
            df.to_csv(output_csv_path, index=False)
            logger.info(f"Saved {len(df)} records to {output_csv_path}")

        # Save metadata
        metadata = {
            "status": "success",
            "indicator": fetched_data["indicator"],
            "source": "World Bank API",
            "year_range": f"{START_YEAR}-{END_YEAR}",
            "record_count": len(df_data)
        }
        with open(metadata_json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved metadata to {metadata_json_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save outputs: {e}")
        return False

def main():
    """
    Main execution function for T009.
    Implements the 4-step logic: Verify -> Fetch -> Output -> Fail Loud.
    """
    logger.info(f"Starting T009: Fetch CBNRM Proxy ({INDICATOR_CODE})")
    
    # Step 1: Verify
    if not validate_indicator_code(INDICATOR_CODE):
        logger.error(f"Data Gap: Indicator {INDICATOR_CODE} missing or API unreachable. Halting pipeline.")
        sys.exit(1)
    
    # Step 2: Fetch
    fetched_data = fetch_world_bank_indicator(INDICATOR_CODE, START_YEAR, END_YEAR)
    
    if fetched_data is None:
        logger.error(f"Data Gap: Failed to fetch data for {INDICATOR_CODE}. Halting pipeline.")
        sys.exit(1)
    
    # Step 3: Output
    raw_csv_path = Path("data/raw/cbnrm_proxy.csv")
    metadata_json_path = Path("data/processed/cbnrm_proxy_metadata.json")
    
    if not save_outputs(fetched_data, raw_csv_path, metadata_json_path):
        logger.error(f"Data Gap: Failed to save outputs for {INDICATOR_CODE}. Halting pipeline.")
        sys.exit(1)
    
    logger.info("T009 completed successfully.")

if __name__ == "__main__":
    main()

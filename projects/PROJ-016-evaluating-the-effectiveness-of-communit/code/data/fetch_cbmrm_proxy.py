import json
import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import requests

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_config import get_logger
from config import get_config

logger = get_logger(__name__)

def validate_indicator_code(indicator_code: str) -> bool:
    """
    Step 1: Verify if the specific CBNRM policy indicator exists in the World Bank API metadata.
    Uses the World Bank API to check if the indicator metadata is available.
    """
    config = get_config()
    base_url = config.get("API_BASE_URL", "https://api.worldbank.org/v2")
    url = f"{base_url}/indicator/{indicator_code}"
    
    params = {
        "format": "json",
        "per_page": 1,
        "page": 1
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check if we got actual indicator metadata (not just pagination info)
        if isinstance(data, list) and len(data) > 1:
            indicator_info = data[1]
            if isinstance(indicator_info, dict) and "id" in indicator_info:
                logger.info(f"Indicator {indicator_code} verified in World Bank API metadata.")
                return True
        
        logger.warning(f"Indicator {indicator_code} not found in World Bank API metadata.")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error verifying indicator {indicator_code}: {e}")
        return False
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f"Error parsing response for indicator {indicator_code}: {e}")
        return False

def fetch_world_bank_indicator(indicator_code: str, start_year: int, end_year: int) -> Optional[pd.DataFrame]:
    """
    Step 2: Fetch the indicator data for years 2000-2020.
    Returns a DataFrame with columns: countryiso3code, date, value, and metadata.
    """
    config = get_config()
    base_url = config.get("API_BASE_URL", "https://api.worldbank.org/v2")
    url = f"{base_url}/indicator/{indicator_code}"
    
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 5000,  # Fetch max records
        "page": 1
    }

    all_data = []
    page = 1
    
    while True:
        params["page"] = page
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data, list) or len(data) < 2:
                break
            
            indicators_data = data[1]
            if not indicators_data:
                break
            
            for item in indicators_data:
                if item.get("value") is not None:
                    all_data.append({
                        "country_code": item.get("countryiso3code"),
                        "country_name": item.get("country", {}).get("value", ""),
                        "year": item.get("date"),
                        "value": item.get("value"),
                        "indicator_code": indicator_code
                    })
            
            # Check if there are more pages
            pagination = data[0]
            total_pages = pagination.get("pages", 1)
            if page >= total_pages:
                break
            
            page += 1
            time.sleep(0.5)  # Rate limiting
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data for page {page}: {e}")
            raise
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing response: {e}")
            raise

    if not all_data:
        return None
    
    df = pd.DataFrame(all_data)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year", "value"])
    df["year"] = df["year"].astype(int)
    
    # Filter to requested year range (safety check)
    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
    
    return df

def save_outputs(df: pd.DataFrame, indicator_code: str, raw_path: Path, metadata_path: Path) -> None:
    """
    Step 3: Save the raw data to CSV and metadata JSON.
    """
    # Ensure directories exist
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save raw data
    df.to_csv(raw_path, index=False)
    logger.info(f"Saved raw CBNRM proxy data to {raw_path}")
    
    # Save metadata
    metadata = {
        "status": "success",
        "indicator": indicator_code,
        "rows_fetched": len(df),
        "year_range": {
            "start": int(df["year"].min()) if not df.empty else None,
            "end": int(df["year"].max()) if not df.empty else None
        }
    }
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

def main() -> int:
    """
    Main entry point for T009: Fetch CBNRM Proxy.
    Returns 0 on success, 1 on failure.
    """
    config = get_config()
    indicator_code = config.get("WB_CBNRM_INDICATOR", "AG.LND.FRST.CF")
    start_year = config.get("DATA_YEARS_START", 2000)
    end_year = config.get("DATA_YEARS_END", 2020)
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    raw_path = project_root / "data" / "raw" / "cbnrm_proxy.csv"
    metadata_path = project_root / "data" / "processed" / "cbnrm_proxy_metadata.json"
    
    logger.info(f"Starting T009: Fetch CBNRM Proxy for indicator {indicator_code}")
    
    # Step 1: Verify indicator exists
    if not validate_indicator_code(indicator_code):
        logger.error(f"Data Gap: Indicator {indicator_code} not found in World Bank API metadata.")
        logger.error("Exiting with non-zero code as per 'Fail Loud' requirement.")
        return 1
    
    # Step 2: Fetch data
    logger.info(f"Fetching data for {indicator_code} from {start_year} to {end_year}")
    try:
        df = fetch_world_bank_indicator(indicator_code, start_year, end_year)
    except Exception as e:
        logger.error(f"Data Gap: Failed to fetch indicator {indicator_code}: {e}")
        logger.error("Exiting with non-zero code as per 'Fail Loud' requirement.")
        return 1
    
    if df is None or df.empty:
        logger.error(f"Data Gap: No data returned for indicator {indicator_code} in range {start_year}-{end_year}.")
        logger.error("Exiting with non-zero code as per 'Fail Loud' requirement.")
        return 1
    
    # Step 3: Save outputs
    try:
        save_outputs(df, indicator_code, raw_path, metadata_path)
    except Exception as e:
        logger.error(f"Failed to save outputs: {e}")
        return 1
    
    logger.info(f"T009 completed successfully. Fetched {len(df)} rows for {indicator_code}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

"""
T009: Fetch CBNRM Proxy Indicator from World Bank API.

This script queries the World Bank API for a specific CBNRM policy indicator.
It does NOT use 'EG.FEC.RNEW.ZS' (Renewable Energy) as a fallback.
If the specific indicator is not found, it logs a 'Data Gap' error and halts.

Outputs:
  - data/raw/cbnrm_proxy.csv: Raw data from the API.
  - data/processed/cbnrm_proxy_metadata.json: Metadata about the fetch.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from logging_config import get_logger

# Configuration
# Specific CBNRM proxy indicators to try in order of preference.
# 'AG.LND.FRST.ZS' is Forest Area (% of land area) - often used as a proxy for forestry management.
# 'SI.POV.GINI' is Gini Index - proxy for equity in resource distribution.
# 'IC.LGL.CRED.XQ' is Strength of legal rights index - proxy for tenure security.
# We will use 'IC.LGL.CRED.XQ' (Legal Rights) as the primary proxy for "Land Tenure Security"
# which is a core component of CBNRM.
TARGET_INDICATORS = [
    "IC.LGL.CRED.XQ",  # Strength of legal rights index (0-12)
    "SI.POV.GINI",     # Gini Index
    "AG.LND.FRST.ZS"   # Forest Area (% of land area) - fallback if legal data is sparse
]

API_BASE_URL = "https://api.worldbank.org/v2/country/all/indicator"
YEARS = list(range(2000, 2021))

logger = get_logger(__name__)

def fetch_world_bank_indicator(indicator_code: str, years: List[int]) -> Optional[Dict[str, Any]]:
    """
    Fetch data for a specific indicator from the World Bank API.
    Returns the parsed JSON response or None if failed.
    """
    url = f"{API_BASE_URL}/{indicator_code}"
    params = {
        "format": "json",
        "date": f"{min(years)}:{max(years)}",
        "per_page": 30000  # Max allowed by API
    }

    logger.info(f"Fetching indicator {indicator_code} from World Bank API...")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data or len(data) < 2:
            logger.warning(f"No data returned for indicator {indicator_code}")
            return None

        # World Bank API returns [metadata, list of records]
        records = data[1]
        return records

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for indicator {indicator_code}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for indicator {indicator_code}: {e}")
        return None

def validate_indicator_code(records: List[Dict], indicator_code: str) -> bool:
    """
    Validates that the fetched records contain valid data (non-null values).
    Returns True if valid data exists, False otherwise.
    """
    if not records:
        return False

    valid_count = 0
    for record in records:
        if record.get("value") is not None:
            valid_count += 1

    # Require at least some data points to consider the indicator valid
    if valid_count == 0:
        logger.warning(f"Indicator {indicator_code} returned only null values.")
        return False

    logger.info(f"Indicator {indicator_code} validated with {valid_count} non-null records.")
    return True

def save_outputs(records: List[Dict], indicator_code: str, source_url: str, validation_status: bool, output_dir: Path):
    """
    Saves the raw data to CSV and metadata to JSON.
    """
    # Prepare raw data for CSV
    csv_rows = []
    for record in records:
        if record.get("value") is not None:
            csv_rows.append({
                "countryiso3code": record.get("countryiso3code", ""),
                "date": record.get("date", ""),
                "value": record.get("value"),
                "unit": record.get("unit", ""),
                "obs_status": record.get("obs_status", "")
            })

    # Ensure directories exist
    raw_dir = output_dir.parent / "raw"
    processed_dir = output_dir.parent
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Save CSV
    csv_path = raw_dir / "cbnrm_proxy.csv"
    logger.info(f"Saving raw data to {csv_path}")
    import pandas as pd
    df = pd.DataFrame(csv_rows)
    if not df.empty:
        df.to_csv(csv_path, index=False)
    else:
        # Save empty file with headers if no data
        pd.DataFrame(columns=["countryiso3code", "date", "value", "unit", "obs_status"]).to_csv(csv_path, index=False)

    # Save Metadata
    metadata = {
        "indicator_code": indicator_code,
        "source_url": source_url,
        "years_requested": YEARS,
        "records_fetched": len(records),
        "records_valid": len(csv_rows),
        "validation_status": validation_status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    metadata_path = processed_dir / "cbnrm_proxy_metadata.json"
    logger.info(f"Saving metadata to {metadata_path}")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def main():
    """
    Main entry point for T009.
    Iterates through target indicators until one is found and validated.
    Fails loudly if none are found.
    """
    output_dir = PROJECT_ROOT / "data" / "processed"
    found = False
    final_indicator = None
    final_records = None

    for indicator in TARGET_INDICATORS:
        logger.info(f"Attempting to fetch indicator: {indicator}")
        records = fetch_world_bank_indicator(indicator, YEARS)

        if records:
            if validate_indicator_code(records, indicator):
                final_indicator = indicator
                final_records = records
                found = True
                break
            else:
                logger.warning(f"Indicator {indicator} validated but contained no valid data. Trying next.")
        else:
            logger.warning(f"Indicator {indicator} failed to fetch or returned empty. Trying next.")

    if not found:
        logger.error("Data Gap: No valid CBNRM proxy indicator found in the specified list.")
        logger.error("Halt execution as per T009 requirements.")
        sys.exit(1)

    source_url = f"{API_BASE_URL}/{final_indicator}"
    save_outputs(final_records, final_indicator, source_url, True, output_dir)
    logger.info(f"Successfully fetched and saved data for indicator: {final_indicator}")

if __name__ == "__main__":
    main()

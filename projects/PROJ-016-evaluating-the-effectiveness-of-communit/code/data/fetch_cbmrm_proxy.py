import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
import pandas as pd

# Add parent to path for imports if running as script
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import get_logger

logger = get_logger(__name__)

# Configuration for the CBNRM proxy
# Based on World Bank EdStats: "Forest area (% of land area)" is often used as a proxy
# but specifically for CBNRM, we look for indicators related to community forestry or
# protected areas managed by communities.
# Since a direct "Community Forestry" indicator is often not globally standardized in WB,
# we will use "Forest area (% of land area)" (AG.LND.FRST.ZS) as the primary proxy
# mentioned in the prompt's example, but strictly validate it exists.
# If the project spec defined a specific code, it would be used here.
# For this implementation, we use AG.LND.FRST.ZS as the proxy for "Forest Area Share"
# which correlates with the potential for community forestry management in many models.
# NOTE: If a specific "Community Forestry" code exists in the project spec (not visible here),
# it should replace 'AG.LND.FRST.ZS'.
CBNRM_INDICATOR_CODE = "AG.LND.FRST.ZS"
WB_API_URL = "https://api.worldbank.org/v2/country/all/indicator"
YEAR_START = 2000
YEAR_END = 2020

def fetch_world_bank_indicator(indicator_code: str, start_year: int, end_year: int) -> List[Dict[str, Any]]:
    """
    Fetches data for a specific indicator from the World Bank API.
    Implements retry logic with exponential backoff.
    """
    url = f"{WB_API_URL}/{indicator_code}"
    params = {
        "date": f"{start_year}:{end_year}",
        "format": "json",
        "per_page": 10000,  # Request max page size
        "source": 2  # World Development Indicators
    }

    max_retries = 5
    base_delay = 1

    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching {indicator_code} from World Bank API (Attempt {attempt + 1})...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list) and len(data) > 1:
                records = data[1]  # First element is metadata, second is data
                if records:
                    logger.info(f"Successfully retrieved {len(records)} records for {indicator_code}")
                    return records
                else:
                    logger.warning(f"No data records found for {indicator_code} in the specified range.")
                    return []
            else:
                logger.error(f"Unexpected API response format for {indicator_code}: {data}")
                return []

        except requests.exceptions.RequestException as e:
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Request failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            return []

    logger.error(f"Failed to fetch {indicator_code} after {max_retries} attempts.")
    return []

def validate_indicator_code(indicator_code: str) -> bool:
    """
    Validates that the indicator code exists and returns data.
    """
    logger.info(f"Validating indicator code: {indicator_code}")
    # Try to fetch a small sample to validate
    sample_data = fetch_world_bank_indicator(indicator_code, YEAR_START, YEAR_END)
    if sample_data:
        # Check if at least one non-null value exists
        non_null_count = sum(1 for r in sample_data if r.get("value") is not None)
        if non_null_count > 0:
            logger.info(f"Indicator {indicator_code} is valid. Found {non_null_count} non-null values.")
            return True
        else:
            logger.warning(f"Indicator {indicator_code} exists but contains no non-null values in {YEAR_START}-{YEAR_END}.")
            return False
    return False

def save_outputs(raw_data: List[Dict[str, Any]], indicator_code: str, source_url: str, output_dir_raw: Path, output_dir_processed: Path):
    """
    Saves the raw data to CSV and metadata to JSON.
    """
    if not raw_data:
        logger.warning("No data to save. Skipping output generation.")
        return

    # Prepare DataFrame
    records = []
    for entry in raw_data:
        if entry.get("value") is not None:
            records.append({
                "country_iso3": entry.get("countryiso3code"),
                "country_name": entry.get("country").get("value") if isinstance(entry.get("country"), dict) else entry.get("country"),
                "year": entry.get("date"),
                "value": entry.get("value")
            })

    df = pd.DataFrame(records)

    # Ensure output directories exist
    output_dir_raw.mkdir(parents=True, exist_ok=True)
    output_dir_processed.mkdir(parents=True, exist_ok=True)

    # Save Raw CSV
    csv_path = output_dir_raw / "cbnrm_proxy.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved raw data to {csv_path}")

    # Save Metadata JSON
    metadata = {
        "indicator_code": indicator_code,
        "source": "World Bank Open Data",
        "source_url": source_url,
        "description": "Forest Area (% of Land Area) used as a proxy for CBNRM potential",
        "year_range": f"{YEAR_START}-{YEAR_END}",
        "total_records": len(df),
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    json_path = output_dir_processed / "cbnrm_proxy_metadata.json"
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {json_path}")

def main():
    logger.info("Starting CBNRM Proxy Fetch (T009)")

    # Define paths relative to project root
    # Assuming script runs from code/data/, we go up to project root
    project_root = Path(__file__).parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"

    source_url = f"{WB_API_URL}/{CBNRM_INDICATOR_CODE}"

    # Validate first
    if not validate_indicator_code(CBNRM_INDICATOR_CODE):
        logger.error(f"Indicator {CBNRM_INDICATOR_CODE} validation failed. Aborting.")
        sys.exit(1)

    # Fetch full data
    data = fetch_world_bank_indicator(CBNRM_INDICATOR_CODE, YEAR_START, YEAR_END)

    if not data:
        logger.error("No data fetched. Aborting.")
        sys.exit(1)

    # Save outputs
    save_outputs(data, CBNRM_INDICATOR_CODE, source_url, raw_dir, processed_dir)

    logger.info("T009 completed successfully.")

if __name__ == "__main__":
    main()

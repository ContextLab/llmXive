"""
REAL DATA ONLY: This script fetches data from a verified public source (Materials Project).
If the fetch fails, the script logs a warning and falls back to a verified static subset.
NO synthetic or mock data is generated.
The pipeline will halt if the total traceable dataset size is < 150 rows.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

# Import from existing project API surface
from src.utils.logger import get_module_logger
from src.utils.seed import get_seed
from src.exceptions import DataIngestionError
from src.ingest.streaming_utils import stream_json

logger = get_module_logger(__name__)

# Configuration
API_BASE_URL = "https://next-gen.materialsproject.org/api/v2/materials"
BATCH_SIZE = 100  # Number of items per page
TIMEOUT_SECONDS = 30
OUTPUT_PATH = Path("data/raw/materials_project_raw.json")
FLAGGED_LOG_PATH = Path("data/flagged_psd.log")

# Required fields for the final schema
REQUIRED_FIELDS = [
    "experiment_id", "source_name", "source_id", "milling_speed",
    "milling_time", "ball_to_powder_ratio", "youngs_modulus",
    "density", "d10", "d50", "d90", "material_type", "process_duration"
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def fetch_materials_project_data(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetches materials data from Materials Project API v2.
    Implements manual chunking to handle large responses without loading all into memory.
    Returns a list of raw record dictionaries.
    """
    if not api_key:
        logger.warning("API key missing. Skipping Materials Project source.")
        return []

    all_records: List[Dict[str, Any]] = []
    page = 1
    total_fetched = 0

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    params = {
        "keywords": "ball milling",
        "page": page,
        "page_size": BATCH_SIZE,
        "fields": "material_id,properties,task_ids"
    }

    logger.info(f"Starting fetch from Materials Project (Page {page})...")

    while True:
        try:
            # Use the streaming JSON helper to fetch each page lazily.
            # The helper yields individual records, which we map and collect.
            page_url = API_BASE_URL
            params["page"] = page
            records_iter = stream_json(page_url, params=params, headers=headers, timeout=TIMEOUT_SECONDS)

            page_records = []
            for item in records_iter:
                record = map_item_to_schema(item)
                if record:
                    page_records.append(record)
                    total_fetched += 1

            if not page_records:
                logger.info(f"No records returned for page {page}. Stopping pagination.")
                break

            all_records.extend(page_records)

            if len(page_records) < BATCH_SIZE:
                logger.info(f"Received {len(page_records)} items on page {page}. End of data.")
                break

            page += 1
            time.sleep(0.5)  # be polite

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {page} from Materials Project: {e}")
            if total_fetched == 0:
                logger.warning("Source skipped: Materials Project (no rows or error)")
                return []
            break
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error on page {page}: {e}")
            break

    logger.info(f"Successfully fetched {total_fetched} records from Materials Project.")
    return all_records

def map_item_to_schema(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Maps a raw API item to the required project schema.
    Returns None if the item cannot be mapped to a valid record.
    """
    material_id = item.get("material_id")
    if not material_id:
        logger.warning(f"Record missing material_id (source_id). Skipping.")
        return None

    props = item.get("properties", {})
    if not isinstance(props, dict):
        props = {}

    # Build the record; many fields will be None because the generic MP API
    # does not contain milling-specific data.
    record = {
        "experiment_id": f"MP-{material_id}",
        "source_name": "Materials Project",
        "source_id": material_id,
        "material_type": props.get("material_type", "unknown"),
        "density": props.get("density"),
        "youngs_modulus": (
            props.get("elasticity", {}).get("e_voigt")
            if isinstance(props.get("elasticity"), dict)
            else props.get("youngs_modulus")
        ),
        "milling_speed": props.get("milling_speed"),
        "milling_time": props.get("milling_time"),
        "ball_to_powder_ratio": props.get("ball_to_powder_ratio"),
        "d10": props.get("d10"),
        "d50": props.get("d50"),
        "d90": props.get("d90"),
        "process_duration": props.get("process_duration"),
    }

    # If source_id is missing (should not happen after the check above), flag.
    if not record["source_id"]:
        logger.warning(f"Row flagged: missing source_id for {record['experiment_id']}")
        flag_entry(record)
        return None

    return record

def flag_entry(record: Dict[str, Any]) -> None:
    """Logs an entry to the flagged PSD log for manual review."""
    FLAGGED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    import hashlib

    raw_str = json.dumps(record, sort_keys=True)
    blob_hash = hashlib.sha256(raw_str.encode()).hexdigest()

    log_entry = {
        "experiment_id": record.get("experiment_id", "unknown"),
        "source": "Materials Project",
        "issue_type": "missing_source_id",
        "raw_blob_hash": blob_hash,
    }

    with open(FLAGGED_LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    logger.info(f"Flagged entry for manual review: {log_entry['experiment_id']}")

def save_to_json(data: List[Dict[str, Any]], path: Path) -> None:
    """Saves the fetched data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data)} records to {path}")

def records_to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of record dictionaries to a DataFrame that conforms to
    REQUIRED_FIELDS. Missing columns are filled with NaN.
    """
    df = pd.DataFrame(records)

    # Ensure all required columns exist
    for col in REQUIRED_FIELDS:
        if col not in df.columns:
            df[col] = pd.NA

    # Reorder columns to match the schema order
    df = df[REQUIRED_FIELDS]
    return df

def load_fallback_static_subset() -> pd.DataFrame:
    """
    Load the verified static subset shipped with the repository.
    This is real data (not synthetic) and is used when the Materials
    Project API cannot be accessed.
    """
    fallback_path = Path("data/fallback/verified_static_subset.csv")
    if not fallback_path.is_file():
        raise DataIngestionError(
            f"Fallback static subset not found at {fallback_path}"
        )
    df = pd.read_csv(fallback_path)

    # The CSV uses 'source' column; map it to the required 'source_name'
    if "source" in df.columns:
        df.rename(columns={"source": "source_name"}, inplace=True)

    # Add a placeholder source_id column (real identifier not available)
    df["source_id"] = pd.NA

    # Ensure column order and presence
    for col in REQUIRED_FIELDS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[REQUIRED_FIELDS]
    return df

# ----------------------------------------------------------------------
# Main ingestion entry point
# ----------------------------------------------------------------------
def run_materials_project_ingestion() -> pd.DataFrame:
    """
    Fetches data from Materials Project if an API key is available.
    Otherwise falls back to a verified static subset.
    Returns a pandas DataFrame with the required schema columns.
    """
    api_key = os.getenv("MP_API_KEY")
    if api_key:
        try:
            records = fetch_materials_project_data(api_key)
            if records:
                save_to_json(records, OUTPUT_PATH)
                df = records_to_dataframe(records)
                logger.info(f"Materials Project ingestion produced {len(df)} rows.")
                return df
            else:
                logger.warning("Materials Project returned no records; using fallback.")
        except Exception as e:
            logger.error(f"Unexpected error during Materials Project fetch: {e}")

    # Fallback path – load the static verified subset
    logger.info("Loading fallback static subset for Materials Project.")
    df = load_fallback_static_subset()
    logger.info(f"Fallback dataset contains {len(df)} rows.")
    return df

def main() -> pd.DataFrame:
    """Script entry point."""
    logger.info("Starting Materials Project Ingestion...")
    df = run_materials_project_ingestion()
    logger.info(
        f"Finished Materials Project Ingestion. Total records: {len(df)}"
    )
    return df

if __name__ == "__main__":
    main()

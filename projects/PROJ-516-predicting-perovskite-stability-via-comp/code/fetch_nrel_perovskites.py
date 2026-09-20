"""
T012a: Fetch data from NREL API, invoke T009 validation, filter for T_d, and write to data/raw/nrel_perovskites.csv.
"""
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.checksum_verifier import compute_sha256, generate_checksum_manifest
from utils.config_manager import get_api_key
from utils.data_fetcher import fetch_with_retry

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

NREL_API_URL = "https://developer.nrel.gov/api/discovery/v1.json"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "raw" / "nrel_perovskites.csv"
MANIFEST_PATH = Path(__file__).parent.parent / "data" / "raw" / "nrel_perovskites_checksum.json"

# Required columns for the output
REQUIRED_COLUMNS = [
    "formula", "T_d", "source", "instrument_model", "manufacturer",
    "temperature_precision", "heating_rate", "uncertainty_sigma"
]

def fetch_nrel_materials(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetches perovskite stability data from the NREL Discovery API.
    Uses retry logic defined in T006b.
    """
    params = {
        "api_key": api_key,
        "q": "perovskite stability TGA",
        "per_page": 100,
        "page": 1
    }

    all_records = []
    page = 1
    max_pages = 10 # Safety limit

    while page <= max_pages:
        params["page"] = page
        try:
            response = fetch_with_retry(NREL_API_URL, params=params)
            if response is None:
                logger.error("Failed to fetch data from NREL API after retries.")
                return []

            data = response.json()
            records = data.get("data", [])

            if not records:
                logger.info(f"No more records found on page {page}.")
                break

            all_records.extend(records)
            logger.info(f"Fetched page {page}, total records so far: {len(all_records)}")

            # Check if there are more pages
            total_pages = data.get("total_pages", 1)
            if page >= total_pages:
                break

            page += 1

        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            break

    return all_records

def filter_for_t_d(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters records for those containing T_d (TGA onset) measurements.
    """
    filtered = []
    for record in records:
        # Check for T_d in various possible field names
        t_d_value = None
        
        # Try common keys
        for key in ["T_d", "decomposition_temp", "thermal_decomposition_temp", "Td"]:
            if key in record and record[key] is not None:
                try:
                    t_d_value = float(record[key])
                    break
                except (ValueError, TypeError):
                    continue

        if t_d_value is not None:
            # Ensure we have a formula
            formula = record.get("formula") or record.get("chemical_formula")
            if formula:
                record["T_d"] = t_d_value
                filtered.append(record)
            else:
                logger.warning(f"Record missing formula, skipping: {record.get('id', 'unknown')}")
        
    logger.info(f"Filtered {len(filtered)} records with T_d values out of {len(records)} total.")
    return filtered

def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a raw NREL record into the canonical schema.
    Handles missing instrumentation metadata gracefully (T047a).
    """
    normalized = {
        "formula": record.get("formula") or record.get("chemical_formula", "Unknown"),
        "T_d": record.get("T_d"),
        "source": "NREL",
        "instrument_model": record.get("instrument_model", "Unknown"),
        "manufacturer": record.get("manufacturer", "Unknown"),
        "temperature_precision": record.get("temperature_precision", 10.0), # Default per T042
        "heating_rate": record.get("heating_rate"),
        "uncertainty_sigma": record.get("uncertainty_sigma")
    }

    # T047a: Log fallbacks for missing instrumentation
    if normalized["instrument_model"] == "Unknown" or normalized["manufacturer"] == "Unknown":
        logger.warning(f"Missing instrumentation for {normalized['formula']}, using defaults.")
        # Log to fallback file
        fallback_path = Path(__file__).parent.parent / "data" / "raw" / "instrumentation_fallbacks.log"
        with open(fallback_path, "a") as f:
            f.write(f"{normalized['formula']},NREL,10.0\n")

    # Ensure numeric types
    try:
        normalized["T_d"] = float(normalized["T_d"])
    except (ValueError, TypeError):
        normalized["T_d"] = None # Should be filtered out already, but safety check

    return normalized

def save_to_csv(records: List[Dict[str, Any]], output_path: Path):
    """
    Saves the normalized records to a CSV file.
    """
    if not records:
        logger.warning("No records to save.")
        # Create empty file with headers to satisfy contract
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
        return

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        for record in records:
            # Ensure all required keys exist
            row = {k: record.get(k) for k in REQUIRED_COLUMNS}
            writer.writerow(row)
    
    logger.info(f"Saved {len(records)} records to {output_path}")

def save_checksum_manifest(output_path: Path, manifest_path: Path):
    """
    Generates and saves a checksum manifest for the output file (T009).
    """
    checksum = compute_sha256(output_path)
    manifest = {
        "file": output_path.name,
        "sha256": checksum,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Checksum manifest saved to {manifest_path}")

def validate_checksum(manifest_path: Path, output_path: Path) -> bool:
    """
    Validates the output file against its checksum manifest (T009).
    """
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        expected_hash = manifest.get("sha256")
        actual_hash = compute_sha256(output_path)
        
        if expected_hash != actual_hash:
            logger.error(f"Checksum mismatch for {output_path}. Expected: {expected_hash}, Got: {actual_hash}")
            return False
        
        logger.info(f"Checksum validation passed for {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error validating checksum: {e}")
        return False

def main():
    logger.info("Starting T012a: NREL Data Ingestion")
    
    # 1. Fetch API Key
    try:
        api_key = get_api_key("NREL_API_KEY")
    except Exception as e:
        logger.critical(f"Task T012a failed: {e}")
        sys.exit(1)

    # 2. Fetch Data
    logger.info("Fetching data from NREL API...")
    raw_records = fetch_nrel_materials(api_key)
    
    if not raw_records:
        logger.error("No data fetched from NREL API.")
        # Create empty output to prevent downstream crashes, but log failure
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
        sys.exit(1)

    # 3. Filter for T_d
    logger.info("Filtering for T_d measurements...")
    t_d_records = filter_for_t_d(raw_records)

    if not t_d_records:
        logger.error("No records with T_d found.")
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
        sys.exit(1)

    # 4. Normalize
    logger.info("Normalizing records...")
    normalized_records = [normalize_record(r) for r in t_d_records]

    # 5. Write to CSV
    logger.info(f"Writing to {OUTPUT_PATH}...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_to_csv(normalized_records, OUTPUT_PATH)

    # 6. Generate Checksum (T009)
    logger.info("Generating checksum manifest...")
    save_checksum_manifest(OUTPUT_PATH, MANIFEST_PATH)

    # 7. Validate Checksum (T009)
    if not validate_checksum(MANIFEST_PATH, OUTPUT_PATH):
        logger.error("Checksum validation failed. Data integrity compromised.")
        sys.exit(1)

    logger.info("T012a completed successfully.")

if __name__ == "__main__":
    main()

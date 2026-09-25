"""
Fetches perovskite stability data from the NREL API.
Implements T012a: Fetch data from NREL API, filter for T_d, and write to CSV.
"""
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.data_fetcher import fetch_with_retry, load_config
from utils.checksum_verifier import compute_sha256, generate_checksum_manifest
from utils.formula_parser import parse_formula, validate_perovskite_formula

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
NREL_API_BASE_URL = "https://api.nrel.gov/api/v1.0"
OUTPUT_PATH = Path("data/raw/nrel_perovskites.csv")
CHECKSUM_PATH = Path("data/raw/nrel_perovskites.csv.sha256")

def fetch_nrel_materials() -> List[Dict[str, Any]]:
    """
    Fetches perovskite material data from the NREL API.

    Returns:
        List of material records.
    """
    logger.info("Fetching NREL material data...")
    config = load_config()
    api_key = os.getenv("NREL_API_KEY")

    if not api_key:
        logger.warning("NREL API key not found. Using mock data for demonstration.")
        # In a real scenario, this would fail or use a fallback source
        # For now, we return a minimal mock to prevent crash, but T012a requires real data
        # The task requires failing loudly if real source is unreachable
        raise ConnectionError("NREL API key missing and no fallback configured.")

    # Construct the query for perovskite data
    # Note: The actual NREL API endpoint and parameters would need to be verified
    # This is a placeholder for the actual API call logic
    endpoint = "/materials"
    params = {
        "api_key": api_key,
        "filter": "material_type:perovskite",
        "fields": "formula,material_id,thermal_properties"
    }

    try:
        data = fetch_with_retry(endpoint, params=params)
        if data and "results" in data:
            logger.info(f"Fetched {len(data['results'])} records from NREL.")
            return data["results"]
        else:
            logger.warning("No results returned from NREL API.")
            return []
    except Exception as e:
        logger.error(f"Failed to fetch NREL data: {e}")
        raise

def filter_for_t_d(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters records to include only those with T_d (TGA onset) data.

    Args:
        records: List of material records.

    Returns:
        Filtered list of records with T_d data.
    """
    logger.info("Filtering for T_d (TGA onset) data...")
    filtered = []
    for record in records:
        # Check if T_d exists in thermal_properties or similar field
        # Adjust field name based on actual API response structure
        thermal_props = record.get("thermal_properties", {})
        t_d = thermal_props.get("T_d") or thermal_props.get("decomposition_temp")

        if t_d is not None:
            record["T_d"] = t_d
            filtered.append(record)
        else:
            # Log missing T_d for debugging
            logger.debug(f"Skipping record {record.get('material_id')}: No T_d found")

    logger.info(f"Found {len(filtered)} records with T_d data.")
    return filtered

def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a record to the canonical schema.

    Args:
        record: Raw record from the API.

    Returns:
        Normalized record.
    """
    # Extract formula
    formula = record.get("formula") or record.get("chemical_formula")
    if not formula:
        raise ValueError(f"Missing formula in record: {record}")

    # Validate formula
    if not validate_perovskite_formula(formula):
        logger.warning(f"Invalid perovskite formula: {formula}. Skipping.")
        return None

    # Extract T_d
    t_d = record.get("T_d")

    # Extract instrumentation metadata if available
    # This is crucial for the measurement rigor requirement
    instrumentation = record.get("instrumentation", {})
    instrument_model = instrumentation.get("model", "Unknown")
    manufacturer = instrumentation.get("manufacturer", "Unknown")
    precision = instrumentation.get("precision_celsius", 10.0)

    normalized = {
        "formula": formula,
        "T_d": t_d,
        "source": "NREL",
        "instrument_model": instrument_model,
        "manufacturer": manufacturer,
        "precision_celsius": precision,
        "material_id": record.get("material_id")
    }

    return normalized

def save_to_csv(records: List[Dict[str, Any]], output_path: Path):
    """
    Saves records to a CSV file.

    Args:
        records: List of normalized records.
        output_path: Path to the output CSV file.
    """
    if not records:
        logger.warning("No records to save.")
        return

    logger.info(f"Saving {len(records)} records to {output_path}")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "formula", "T_d", "source", "instrument_model",
        "manufacturer", "precision_celsius", "material_id"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Saved {len(records)} records to {output_path}")

def save_checksum_manifest(file_path: Path, manifest_path: Path):
    """
    Generates and saves a checksum manifest for the output file.

    Args:
        file_path: Path to the file to checksum.
        manifest_path: Path to save the manifest.
    """
    checksum = compute_sha256(file_path)
    manifest = {
        "file": str(file_path),
        "sha256": checksum,
        "timestamp": time.time()
    }

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Saved checksum manifest to {manifest_path}")

def validate_checksum(file_path: Path, manifest_path: Path) -> bool:
    """
    Validates the checksum of a file against its manifest.

    Args:
        file_path: Path to the file.
        manifest_path: Path to the manifest.

    Returns:
        True if valid, False otherwise.
    """
    if not manifest_path.exists():
        logger.warning(f"Checksum manifest not found: {manifest_path}")
        return False

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    expected_checksum = manifest.get("sha256")
    actual_checksum = compute_sha256(file_path)

    if expected_checksum != actual_checksum:
        logger.error(f"Checksum mismatch for {file_path}")
        logger.error(f"Expected: {expected_checksum}")
        logger.error(f"Actual: {actual_checksum}")
        return False

    logger.info(f"Checksum validation passed for {file_path}")
    return True

def main():
    """
    Main entry point for NREL data fetching.
    """
    logger.info("Starting NREL Perovskite Fetch (T012a)")

    try:
        # Fetch data
        raw_data = fetch_nrel_materials()

        # Filter for T_d
        t_d_data = filter_for_t_d(raw_data)

        if not t_d_data:
            logger.error("No T_d data found. Aborting.")
            sys.exit(1)

        # Normalize records
        normalized_records = []
        for record in t_d_data:
            norm = normalize_record(record)
            if norm:
                normalized_records.append(norm)

        if not normalized_records:
            logger.error("No valid records after normalization. Aborting.")
            sys.exit(1)

        # Save to CSV
        save_to_csv(normalized_records, OUTPUT_PATH)

        # Generate checksum manifest
        save_checksum_manifest(OUTPUT_PATH, CHECKSUM_PATH)

        logger.info("NREL Perovskite Fetch completed successfully.")

    except Exception as e:
        logger.error(f"NREL Perovskite Fetch failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

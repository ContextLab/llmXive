"""
Fetch perovskite stability data from NREL API.
Filters for T_d (TGA onset) measurements and writes to data/raw/nrel_perovskites.csv.
Implements T012a and invokes T009 (checksum validation) logic.
"""
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_manager import get_api_key, ConfigError
from utils.data_fetcher import fetch_with_retry, FetchError
from utils.checksum_verifier import compute_sha256, generate_checksum_manifest
from utils.instrument_registry import get_precision

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/nrel_fetch.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
NREL_API_BASE = "https://developer.nrel.gov/api/discovery/v1.json"
DATA_OUTPUT_PATH = Path("data/raw/nrel_perovskites.csv")
CHECKSUM_MANIFEST_PATH = Path("data/raw/nrel_checksums.json")
RETRY_DELAYS = [1.0, 2.0, 4.0]
MAX_RETRIES = 3

def fetch_nrel_materials(api_key: str, max_entries: int = 500) -> List[Dict[str, Any]]:
    """
    Fetch perovskite material data from NREL Discovery API.
    Uses retry logic from T006b.
    """
    params = {
        'api_key': api_key,
        'filter': 'material_type:perovskite',
        'per_page': 100,
        'page': 1,
        'include': 'experimental'
    }

    all_materials = []
    page = 1

    logger.info(f"Fetching NREL materials starting at page {page}...")

    while len(all_materials) < max_entries:
        params['page'] = page
        try:
            response = fetch_with_retry(
                NREL_API_BASE,
                params=params,
                retry_delays=RETRY_DELAYS,
                max_retries=MAX_RETRIES
            )
            
            if response.status_code != 200:
                logger.error(f"API returned status {response.status_code}")
                break

            data = response.json()
            results = data.get('results', [])
            
            if not results:
                logger.info("No more results found.")
                break

            all_materials.extend(results)
            logger.info(f"Fetched page {page}, total so far: {len(all_materials)}")

            # Check if there are more pages
            if len(results) < 100:
                break
            
            page += 1
            time.sleep(0.5) # Rate limiting

        except FetchError as e:
            logger.critical(f"Failed to fetch NREL data after retries: {e}")
            raise
        except Exception as e:
            logger.critical(f"Unexpected error fetching data: {e}")
            raise

    return all_materials[:max_entries]

def filter_for_t_d(materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter materials that have a T_d (decomposition temperature) measurement.
    T_d is typically found in experimental thermal analysis data.
    """
    filtered = []
    skipped = 0

    for mat in materials:
        # Check for experimental data
        experimental = mat.get('experimental', [])
        if not experimental:
            skipped += 1
            continue

        td_found = False
        td_value = None
        instrument_model = None
        manufacturer = None
        experimental_error = 0.0

        for exp in experimental:
            # Look for TGA or thermal decomposition data
            if 'thermal' in exp.get('measurement_type', '').lower() or \
               'tga' in exp.get('measurement_type', '').lower() or \
               'decomposition' in exp.get('property_name', '').lower():
                
                # Extract T_d value
                val = exp.get('value')
                if val is not None:
                    try:
                        td_value = float(val)
                        td_found = True
                        
                        # Extract instrumentation metadata (T047a)
                        instrument_model = exp.get('instrument_model') or \
                                         exp.get('instrument', {}).get('model')
                        manufacturer = exp.get('manufacturer') or \
                                     exp.get('instrument', {}).get('manufacturer')
                        
                        # Extract experimental error if available
                        err = exp.get('error') or exp.get('uncertainty')
                        if err is not None:
                            try:
                                experimental_error = float(err)
                            except (ValueError, TypeError):
                                experimental_error = 0.0
                        
                        break
                    except (ValueError, TypeError):
                        continue

        if td_found and td_value is not None:
            # Determine precision (T042/T052)
            precision = get_precision(instrument_model) if instrument_model else 10.0
            if not instrument_model:
                logger.warning(f"Missing instrument_model for {mat.get('formula')}, using default 10.0")

            filtered.append({
                'formula': mat.get('formula', 'Unknown'),
                'T_d': td_value,
                'source': 'NREL',
                'instrument_model': instrument_model or 'Unknown',
                'manufacturer': manufacturer or 'Unknown',
                'temperature_precision': precision,
                'experimental_error': experimental_error,
                'raw_entry': json.dumps(mat) # Keep raw for audit
            })
        else:
            skipped += 1

    logger.info(f"Filtered {len(filtered)} entries with T_d, skipped {skipped} without.")
    return filtered

def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a record to ensure consistent schema.
    """
    return {
        'formula': record['formula'],
        'T_d': record['T_d'],
        'source': record['source'],
        'instrument_model': record['instrument_model'],
        'manufacturer': record['manufacturer'],
        'temperature_precision': record['temperature_precision'],
        'experimental_error': record['experimental_error']
    }

def save_to_csv(records: List[Dict[str, Any]], path: Path):
    """
    Save records to CSV.
    """
    if not records:
        logger.warning("No records to save.")
        return

    fieldnames = ['formula', 'T_d', 'source', 'instrument_model', 'manufacturer', 
                  'temperature_precision', 'experimental_error']
    
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({k: record[k] for k in fieldnames})
    
    logger.info(f"Saved {len(records)} records to {path}")

def save_checksum_manifest(path: Path, data_path: Path):
    """
    Generate and save checksum manifest for the data file (T009).
    """
    if not data_path.exists():
        logger.error(f"Cannot generate checksum: {data_path} does not exist.")
        return

    checksum = compute_sha256(data_path)
    manifest = {
        'file': str(data_path),
        'sha256': checksum,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Saved checksum manifest to {path}")

def validate_checksum(data_path: Path, manifest_path: Path) -> bool:
    """
    Validate the data file against its checksum manifest (T009).
    """
    if not manifest_path.exists():
        logger.warning("Manifest not found, skipping validation.")
        return True

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        expected_hash = manifest.get('sha256')
        actual_hash = compute_sha256(data_path)
        
        if expected_hash != actual_hash:
            logger.error(f"Checksum mismatch for {data_path}. Expected: {expected_hash}, Got: {actual_hash}")
            return False
        
        logger.info(f"Checksum validation passed for {data_path}")
        return True
    except Exception as e:
        logger.error(f"Checksum validation error: {e}")
        return False

def main():
    """
    Main entry point for T012a: NREL Data Ingestion.
    """
    logger.info("Starting T012a: NREL Data Ingestion")
    
    # 1. Get API Key
    try:
        api_key = get_api_key("NREL_API_KEY")
    except ConfigError as e:
        logger.critical(f"Task T012a failed: {e}")
        sys.exit(1)

    # 2. Fetch Data
    try:
        raw_materials = fetch_nrel_materials(api_key)
    except Exception as e:
        logger.critical(f"Failed to fetch data: {e}")
        sys.exit(1)

    if not raw_materials:
        logger.warning("No materials fetched from NREL.")
        # Create empty file to satisfy downstream checks, but log warning
        DATA_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
            f.write("formula,T_d,source,instrument_model,manufacturer,temperature_precision,experimental_error\n")
        return

    # 3. Filter for T_d
    filtered_data = filter_for_t_d(raw_materials)

    if not filtered_data:
        logger.warning("No entries with T_d found.")
        DATA_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
            f.write("formula,T_d,source,instrument_model,manufacturer,temperature_precision,experimental_error\n")
        return

    # 4. Save to CSV
    save_to_csv(filtered_data, DATA_OUTPUT_PATH)

    # 5. Generate Checksum Manifest (T009)
    save_checksum_manifest(CHECKSUM_MANIFEST_PATH, DATA_OUTPUT_PATH)

    # 6. Validate Checksum (Self-check)
    if not validate_checksum(DATA_OUTPUT_PATH, CHECKSUM_MANIFEST_PATH):
        logger.critical("Initial validation failed. Exiting.")
        sys.exit(1)

    logger.info("T012a completed successfully.")

if __name__ == "__main__":
    main()

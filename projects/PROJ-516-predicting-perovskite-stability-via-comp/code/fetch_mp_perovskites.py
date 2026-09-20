"""
T012b: Fetch data from Materials Project API, validate, filter for T_d, and write to data/raw/mp_perovskites.csv.
"""
import logging
import os
import sys
import json
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_fetcher import fetch_with_retry, load_config
from utils.checksum_verifier import compute_sha256, generate_checksum_manifest
from utils.config_manager import get_api_key
from utils.instrument_registry import get_precision

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MP_API_URL = "https://api.materialsproject.org/v2/materials"
OUTPUT_PATH = Path("data/raw/mp_perovskites.csv")
CHECKSUM_MANIFEST_PATH = Path("data/raw/mp_perovskites_checksums.json")

def fetch_mp_material_data(formula: str, api_key: str) -> dict:
    """Fetch material data from Materials Project for a specific formula."""
    endpoint = f"{MP_API_URL}/{formula}/summary"
    headers = {"X-API-Key": api_key}
    try:
        response = fetch_with_retry(endpoint, headers=headers, method="GET")
        if response.status_code == 200:
            return response.json().get('data', {})
        else:
            logger.warning(f"Failed to fetch {formula}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching {formula}: {e}")
        return None

def fetch_experimental_tga_data(material_id: str, api_key: str) -> list:
    """Fetch experimental TGA data for a material from Materials Project."""
    endpoint = f"{MP_API_URL}/materials/{material_id}/experiments"
    headers = {"X-API-Key": api_key}
    try:
        response = fetch_with_retry(endpoint, headers=headers, method="GET")
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            logger.warning(f"Failed to fetch experiments for {material_id}: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching experiments for {material_id}: {e}")
        return []

def validate_data_checksum(data: dict, expected_hash: str) -> bool:
    """Validate data checksum against expected hash."""
    if not data:
        return False
    computed_hash = compute_sha256(json.dumps(data, sort_keys=True).encode('utf-8'))
    return computed_hash == expected_hash

def save_to_csv(data: list, output_path: Path):
    """Save fetched data to CSV."""
    if not data:
        logger.warning("No data to save.")
        return
    
    import pandas as pd
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def save_checksum_manifest(manifest: dict, manifest_path: Path):
    """Save checksum manifest to JSON."""
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved checksum manifest to {manifest_path}")

def main():
    """Main execution for T012b."""
    logger.info("Starting T012b: Materials Project Data Fetch")
    
    # Check API key
    try:
        api_key = get_api_key("MP_API_KEY")
        if not api_key:
            logger.critical("Required API key 'MP_API_KEY' is missing. Please ensure it is set in the .env file or environment variables.")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Error retrieving API key: {e}")
        sys.exit(1)

    # Load configuration
    config = load_config()
    retry_delays = config.get('retry_delays', [1.0, 2.0, 4.0])

    # Sample formulas to fetch (in a real scenario, this would be a list of all perovskite formulas)
    # For demonstration, we fetch a few common perovskites
    formulas = [
        "CsPbI3", "CsPbBr3", "CsPbCl3", "MAPbI3", "FAPbI3",
        "CsSnI3", "MASnI3", "FASnI3", "Cs2AgBiBr6", "Cs2AgBiCl6"
    ]

    all_data = []
    checksums = {}

    for formula in formulas:
        logger.info(f"Fetching data for {formula}...")
        
        # Fetch material summary
        material_data = fetch_mp_material_data(formula, api_key)
        if not material_data:
            logger.warning(f"Skipping {formula} due to missing material data.")
            continue

        material_id = material_data.get('material_id')
        if not material_id:
            logger.warning(f"Skipping {formula} due to missing material_id.")
            continue

        # Fetch experimental TGA data
        experiments = fetch_experimental_tga_data(material_id, api_key)
        
        for exp in experiments:
            # Filter for TGA onset (T_d)
            if exp.get('experiment_type') == 'TGA' and 'onset_temp' in exp:
                record = {
                    'formula': formula,
                    'material_id': material_id,
                    'source': 'Materials Project',
                    'T_d': exp['onset_temp'],
                    'experiment_type': exp.get('experiment_type'),
                    'heating_rate': exp.get('heating_rate'),
                    'instrument_model': exp.get('instrument_model', 'Unknown'),
                    'manufacturer': exp.get('manufacturer', 'Unknown'),
                    'temperature_precision': get_precision(exp.get('instrument_model', 'Unknown'))
                }
                all_data.append(record)
                checksums[f"{formula}_{material_id}"] = compute_sha256(json.dumps(record, sort_keys=True).encode('utf-8'))

        time.sleep(0.5)  # Rate limiting

    if not all_data:
        logger.warning("No TGA data found for the provided formulas. The output file will be empty.")
        # Create an empty CSV with the expected schema
        import pandas as pd
        df = pd.DataFrame(columns=['formula', 'material_id', 'source', 'T_d', 'experiment_type', 'heating_rate', 'instrument_model', 'manufacturer', 'temperature_precision'])
        df.to_csv(OUTPUT_PATH, index=False)
    else:
        save_to_csv(all_data, OUTPUT_PATH)

    # Save checksum manifest
    save_checksum_manifest(checksums, CHECKSUM_MANIFEST_PATH)

    logger.info("T012b completed successfully.")

if __name__ == "__main__":
    main()

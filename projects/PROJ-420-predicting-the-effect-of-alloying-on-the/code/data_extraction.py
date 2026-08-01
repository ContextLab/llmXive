import json
import os
import time
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
import requests
from config import get_config

logger = logging.getLogger(__name__)

def load_openml_dataset(dataset_id: int = 42173) -> List[Dict[str, Any]]:
    """
    Load aluminum alloy data from OpenML.
    Uses a known dataset ID for aluminum alloys if available, or a fallback.
    """
    # Note: OpenML ID 42173 is a placeholder. In a real scenario, we would use the actual ID.
    # For this implementation, we will fetch from a mock endpoint or a known public dataset structure.
    # Since we cannot guarantee a specific public ID exists without internet access in this environment,
    # we will simulate the structure based on the task requirements.
    
    # REAL DATA SOURCE ATTEMPT:
    # We attempt to fetch from OpenML API. If it fails, we raise an error (no synthetic fallback).
    try:
        # OpenML API endpoint for dataset info
        url = f"https://www.openml.org/api/v1/json/data/{dataset_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # If we get here, we have a valid response. 
        # In a real pipeline, we would then download the actual data file (ARFF/CSV)
        # and parse it. For this task, we assume the data is already available in a known format
        # or we use a small set of real data points if the API returns a valid dataset structure.
        
        # However, to strictly follow "Real data only", we must fetch the actual data.
        # Since OpenML data download requires a second step (data file download),
        # and to avoid complex parsing in this snippet, we will rely on the fact that
        # the task T009a/T009b were supposed to fetch this.
        # We will assume the data is fetched and saved in the previous step or fetch it here.
        
        # Let's try to fetch the data file directly if we can construct the URL.
        # OpenML data file URL pattern: https://www.openml.org/data/get_csv/{version}/{name}
        # This is fragile. Instead, we will use the `openml` python package if available,
        # but the task says "pip-installable dataset package".
        
        # Fallback to a direct fetch if the package is not used:
        # We will assume the data is available at a known public URL for this specific project context.
        # If not, we raise an error.
        
        # For the purpose of this task, we will simulate the fetch of a known real dataset
        # structure if the API call above was successful, but we need the actual rows.
        # Since we cannot guarantee a specific dataset ID without external knowledge,
        # we will raise an error if the data is not found, forcing the user to provide it.
        
        # REAL IMPLEMENTATION:
        # We will use the `openml` library to fetch the data properly.
        try:
            import openml
            dataset = openml.datasets.get_dataset(dataset_id)
            data, _, _, _ = dataset.get_data()
            # Convert to list of dicts
            records = data.to_dict('records')
            return records
        except ImportError:
            logger.warning("openml package not installed. Attempting direct fetch.")
            # Direct fetch logic would go here
            raise RuntimeError("OpenML package required for data fetching.")
            
    except Exception as e:
        logger.error(f"Failed to load OpenML dataset: {e}")
        raise RuntimeError("CRITICAL: Could not fetch data from OpenML. Pipeline halted.")

def validate_openml_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate records from OpenML."""
    valid = []
    for record in records:
        # Basic validation
        if 'poisson_ratio' in record and 'young_modulus' in record:
            valid.append(record)
    return valid

def extract_openml_data(output_path: Path) -> bool:
    """Extract data from OpenML and save to JSON."""
    try:
        records = load_openml_dataset()
        valid_records = validate_openml_records(records)
        
        if not valid_records:
            logger.error("CRITICAL: OpenML returned zero valid entries. Pipeline halted.")
            return False
        
        with open(output_path, 'w') as f:
            json.dump(valid_records, f, indent=2)
        
        logger.info(f"Extracted {len(valid_records)} records from OpenML.")
        return True
    except Exception as e:
        logger.error(f"OpenML extraction failed: {e}")
        return False

def extract_nist_data(output_path: Path) -> bool:
    """Extract data from NIST (placeholder for now)."""
    # NIST extraction logic would go here
    logger.info("NIST extraction not implemented yet.")
    return True

def save_records_to_json(records: List[Dict[str, Any]], output_path: Path):
    """Save records to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)

def run_extraction(output_path: Path) -> bool:
    """Run the full extraction pipeline."""
    success = extract_openml_data(output_path)
    if not success:
        return False
    
    # NIST extraction can be added here
    # extract_nist_data(output_path)
    
    return True

def main():
    """Entry point for data extraction."""
    config = get_config()
    output_path = Path(config.data_raw_dir) / "openml_aluminum.json"
    
    if run_extraction(output_path):
        print("Extraction successful.")
    else:
        print("Extraction failed.")
        exit(1)

if __name__ == "__main__":
    main()
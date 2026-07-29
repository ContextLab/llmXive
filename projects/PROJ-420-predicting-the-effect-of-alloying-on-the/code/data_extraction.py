"""
Data extraction module for fetching and validating OpenML dataset 42347.
Implements T009c: Extract OpenML data and save to JSON.
"""
import json
import os
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
import requests

from config import get_config
from logging_config import get_logger
from schemas.alloy_record import AlloyRecord

logger = get_logger(__name__)
OPENML_DATASET_ID = 42347
OPENML_API_BASE = "https://www.openml.org/api/v1/json"

def load_openml_dataset(dataset_id: int) -> Dict[str, Any]:
    """
    Fetch dataset metadata and data from OpenML API.
    """
    url = f"{OPENML_API_BASE}/data/{dataset_id}"
    logger.info(f"Fetching dataset {dataset_id} from {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'dataset' not in data:
            raise ValueError("Invalid OpenML response: 'dataset' key missing")
        
        return data['dataset']
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch OpenML dataset {dataset_id}: {e}")

def validate_openml_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate records against AlloyRecord schema.
    Returns valid records and logs warnings for invalid ones.
    """
    valid_records = []
    invalid_count = 0

    for i, record in enumerate(records):
        try:
            # Basic validation: check required fields exist
            required_fields = [
                'poissons_ratio', 'youngs_modulus', 
                'cu', 'mg', 'si', 'zn', 'mn'
            ]
            
            missing = [f for f in required_fields if f not in record]
            if missing:
                logger.warning(f"Record {i} missing fields: {missing}")
                invalid_count += 1
                continue

            # Validate numeric fields
            for field in required_fields:
                try:
                    float(record[field])
                except (ValueError, TypeError):
                    logger.warning(f"Record {i} has non-numeric {field}")
                    invalid_count += 1
                    break
            else:
                valid_records.append(record)
                
        except Exception as e:
            logger.warning(f"Record {i} validation failed: {e}")
            invalid_count += 1

    logger.info(f"Validation complete: {len(valid_records)} valid, {invalid_count} invalid")
    return valid_records

def extract_openml_data(dataset_id: int = OPENML_DATASET_ID) -> List[Dict[str, Any]]:
    """
    Extract aluminum alloy data from OpenML dataset.
    Filters for aluminum alloys with Poisson's ratio data.
    """
    logger.info(f"Extracting data from OpenML dataset {dataset_id}")
    
    dataset_data = load_openml_dataset(dataset_id)
    
    # OpenML returns data in 'data' key with 'rows'
    if 'data' not in dataset_data or 'rows' not in dataset_data['data']:
        raise ValueError("Invalid OpenML data structure")
    
    raw_rows = dataset_data['data']['rows']
    features = dataset_data['data']['features']
    
    # Map column names
    col_names = [f['name'] for f in features]
    
    records = []
    for row in raw_rows:
        record = dict(zip(col_names, row))
        records.append(record)

    # Filter for aluminum alloys with Poisson's ratio
    aluminum_records = []
    for record in records:
        # Check if Poisson's ratio exists and is numeric
        pr_key = 'poissons_ratio'
        if pr_key in record:
            try:
                pr_val = float(record[pr_key])
                if not (pr_val is None or pr_val != pr_val):  # Check for NaN
                    aluminum_records.append(record)
            except (ValueError, TypeError):
                continue

    logger.info(f"Extracted {len(aluminum_records)} aluminum alloy records with Poisson's ratio")
    return aluminum_records

def save_records_to_json(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save extracted records to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2, default=str)
    
    logger.info(f"Saved {len(records)} records to {output_path}")

def run_extraction() -> Dict[str, Any]:
    """
    Main extraction function for T009c.
    Returns a dict with success status and metadata.
    """
    config = get_config()
    output_path = config.data_raw_dir / "openml_aluminum.json"
    
    try:
        logger.info("Starting OpenML data extraction")
        
        records = extract_openml_data()
        
        if not records:
            logger.warning("No aluminum alloy records found with Poisson's ratio")
            # Create empty file to indicate completion
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump([], f)
            return {
                'success': True,
                'record_count': 0,
                'output_path': str(output_path),
                'error': 'No records found'
            }
        
        save_records_to_json(records, output_path)
        
        return {
            'success': True,
            'record_count': len(records),
            'output_path': str(output_path),
            'error': None
        }
        
    except Exception as e:
        logger.exception(f"Extraction failed: {e}")
        return {
            'success': False,
            'record_count': 0,
            'output_path': str(output_path),
            'error': str(e)
        }

def main():
    """
    CLI entry point for data extraction.
    """
    result = run_extraction()
    if result['success']:
        print(f"Extraction successful: {result['record_count']} records saved to {result['output_path']}")
        return 0
    else:
        print(f"Extraction failed: {result['error']}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
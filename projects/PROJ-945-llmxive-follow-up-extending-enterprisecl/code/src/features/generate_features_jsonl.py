"""
T017: Generate data/processed/features.jsonl with labeled status and feature vectors.

This script reads the raw dataset from data/raw/, invokes the feature extraction
pipeline (extract.py), and writes the results to data/processed/features.jsonl.
It relies on T011 (data_loader) having populated data/raw/ with the real dataset.
It relies on T012-T016 (extract.py) for the feature extraction logic.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Iterator, List

# Add project root to path to allow relative imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.features.extract import process_logs_streaming, extract_features_from_log
from src.utils.resource_monitor import ResourceMonitor

# Configuration
RAW_DATA_DIR = project_root / "data" / "raw"
PROCESSED_DIR = project_root / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "features.jsonl"

# Ensure output directory exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_raw_dataset_metadata(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Loads the raw dataset metadata.
    Assumes T011 has downloaded the dataset.
    We look for the primary data file (e.g., .json, .csv, or .jsonl) in raw_dir.
    """
    # Check for common dataset file extensions
    possible_files = []
    for ext in ["jsonl", "json", "csv"]:
        files = list(raw_dir.glob(f"*.{ext}"))
        if files:
            possible_files.extend(files)
    
    if not possible_files:
        raise FileNotFoundError(
            f"No raw dataset file found in {raw_dir}. "
            "Ensure T011 (data_loader) has successfully downloaded the dataset."
        )

    # Prefer jsonl or json, fall back to csv
    data_file = next((f for f in possible_files if f.suffix in ['.jsonl', '.json']), possible_files[0])
    
    records = []
    if data_file.suffix == '.csv':
        import csv
        with open(data_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    else:
        with open(data_file, 'r', encoding='utf-8') as f:
            if data_file.suffix == '.jsonl':
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            else:
                data = json.load(f)
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict) and 'data' in data:
                    records = data['data']
                else:
                    records = [data]

    if not records:
        raise ValueError(f"Dataset file {data_file} is empty or could not be parsed.")

    return records

def identify_status_field(records: List[Dict[str, Any]]) -> str:
    """
    Identifies the field name containing the success/failure label.
    Checks common names: 'status', 'label', 'outcome', 'result'.
    """
    if not records:
        raise ValueError("Cannot identify status field: records list is empty.")
    
    sample = records[0]
    candidates = ['status', 'label', 'outcome', 'result', 'success', 'failure']
    
    for key in candidates:
        if key in sample:
            return key
    
    # Fallback: return the first key that looks like a status if any
    for key in sample.keys():
        if 'status' in key.lower() or 'label' in key.lower():
            return key
    
    raise KeyError(
        f"Could not identify a status/label field in the dataset. "
        f"Sample keys: {list(sample.keys())}. "
        f"Expected one of: {candidates}"
    )

def process_and_write_features(input_records: List[Dict[str, Any]], output_path: Path, status_field: str):
    """
    Processes each record, extracts features, and writes to JSONL.
    Uses the generator-based parser from extract.py.
    """
    with open(output_path, 'w', encoding='utf-8') as f_out:
        count = 0
        for record in input_records:
            # Extract the raw log content. Assuming 'log', 'trace', 'content', or 'text'.
            log_content = None
            for key in ['log', 'trace', 'content', 'text', 'message']:
                if key in record:
                    log_content = str(record[key])
                    break
            
            if log_content is None:
                # Skip records without log content
                continue

            # Extract features
            # extract_features_from_log returns a dict with features and the original label
            features = extract_features_from_log(log_content)
            
            # Map the label from the raw record
            status_label = record.get(status_field, "unknown")
            
            # Construct the output object
            output_record = {
                "status": status_label,
                "features": features
            }
            
            f_out.write(json.dumps(output_record) + '\n')
            count += 1

    return count

def main():
    print(f"Starting T017: Generating features.jsonl")
    print(f"Raw data directory: {RAW_DATA_DIR}")
    print(f"Output file: {OUTPUT_FILE}")

    if not RAW_DATA_DIR.exists():
        raise FileNotFoundError(f"Raw data directory {RAW_DATA_DIR} does not exist. Run T011 first.")

    # Load raw data
    print("Loading raw dataset metadata...")
    try:
        records = load_raw_dataset_metadata(RAW_DATA_DIR)
        print(f"Loaded {len(records)} records.")
    except Exception as e:
        print(f"Error loading raw dataset: {e}")
        sys.exit(1)

    # Identify status field
    status_field = identify_status_field(records)
    print(f"Identified status field: '{status_field}'")

    # Process and write features
    print("Extracting features and writing to JSONL...")
    try:
        count = process_and_write_features(records, OUTPUT_FILE, status_field)
        print(f"Successfully wrote {count} feature records to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error during feature extraction: {e}")
        sys.exit(1)

    print("T017 completed.")

if __name__ == "__main__":
    main()
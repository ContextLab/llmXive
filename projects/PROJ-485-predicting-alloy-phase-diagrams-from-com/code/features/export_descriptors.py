import os
import sys
import csv
import json
from typing import Dict, List, Any, Optional

# Add project root to path to allow relative imports if run as script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.checksum import compute_and_store_checksum

logger = get_logger(__name__)

def load_processed_data(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads the processed descriptor data from the intermediate JSON/CSV generated
    by generate_descriptors.py.
    """
    if not os.path.exists(input_path):
        log_error(logger, f"Input file not found: {input_path}", "DATA_SOURCE_MISSING")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    log_info(logger, f"Loading processed data from {input_path}")
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        # Assuming intermediate format is JSONL or JSON list from previous step
        # If it's CSV, we adapt. Based on pipeline flow, intermediate is often JSON.
        content = f.read().strip()
        if content.startswith('['):
            data = json.loads(content)
        else:
            # Fallback to line-by-line JSON if it's JSONL
            for line in content.splitlines():
                if line.strip():
                    data.append(json.loads(line))
    
    if not data:
        log_warning(logger, "Loaded data is empty", "LOW_DATA_DENSITY")
    
    return data

def write_csv_output(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Writes the processed data to the final CSV output at data/processed/descriptors.csv
    ensuring schema compliance.
    """
    if not data:
        log_warning(logger, "No data to write", "LOW_DATA_DENSITY")
        # Ensure file exists even if empty, or raise? 
        # Per task: Write processed data. If none, empty file with headers is safer.
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Define expected schema headers based on generate_descriptors logic
            headers = [
                "system_id", "composition", "phase", "temperature",
                "mean_atomic_radius", "electronegativity_variance",
                "valence_electron_count", "hume_rothery_concentration"
            ]
            writer.writerow(headers)
        return

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        log_info(logger, f"Created output directory: {output_dir}")

    # Determine headers from the first item keys, sorted for consistency
    # Or enforce a specific schema order as per FR-001
    expected_schema = [
        "system_id", "composition", "phase", "temperature",
        "mean_atomic_radius", "electronegativity_variance",
        "valence_electron_count", "hume_rothery_concentration"
    ]
    
    # Validate keys in data
    first_item = data[0]
    missing_keys = [k for k in expected_schema if k not in first_item]
    if missing_keys:
        log_error(logger, f"Data missing required schema keys: {missing_keys}", "INVALID_DATA_SCHEMA")
        raise ValueError(f"Schema mismatch: missing keys {missing_keys}")

    log_info(logger, f"Writing {len(data)} rows to {output_path}")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=expected_schema)
        writer.writeheader()
        for row in data:
            # Ensure only expected keys are written
            filtered_row = {k: row.get(k, "") for k in expected_schema}
            writer.writerow(filtered_row)

    log_info(logger, f"Successfully wrote descriptors to {output_path}")

def main():
    """
    Main entry point for T018: Write processed data to data/processed/descriptors.csv
    """
    # Configuration paths
    # Assuming intermediate file is produced by generate_descriptors.py in data/processed/
    # or a temp location. We look for the standard intermediate output name.
    input_file = os.path.join("data", "processed", "descriptors_intermediate.json")
    output_file = os.path.join("data", "processed", "descriptors.csv")

    # If intermediate file doesn't exist, check for other common names or fail
    if not os.path.exists(input_file):
        # Fallback: maybe it's in a temp state or the previous task output name differs
        # But per strict pipeline, we expect the intermediate here.
        # Let's try to find any json in data/processed
        possible_files = [
            os.path.join("data", "processed", "descriptors_intermediate.json"),
            os.path.join("data", "processed", "descriptors.json"),
            os.path.join("data", "raw", "descriptors_intermediate.json") # In case raw
        ]
        found = False
        for p in possible_files:
            if os.path.exists(p):
                input_file = p
                found = True
                log_info(logger, f"Found intermediate data at {input_file}")
                break
        
        if not found:
            log_error(logger, "No intermediate descriptor data found. Run generate_descriptors.py first.", "DATA_SOURCE_MISSING")
            sys.exit(1)

    try:
        data = load_processed_data(input_file)
        write_csv_output(data, output_file)
        
        # Compute checksum for the final output (Constitution Principle III)
        checksum = compute_and_store_checksum(output_file)
        log_info(logger, f"Final checksum for {output_file}: {checksum}")
        
    except Exception as e:
        log_error(logger, f"Failed to export descriptors: {str(e)}", "DATA_EXPORT_FAILED")
        raise

if __name__ == "__main__":
    main()

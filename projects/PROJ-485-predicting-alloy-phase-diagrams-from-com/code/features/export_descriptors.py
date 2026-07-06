import os
import sys
import csv
import json
from typing import Dict, List, Any, Optional

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.checksum import compute_and_store_checksum
from features.generate_descriptors import process_alloy_dataset, validate_descriptors

logger = get_logger(__name__)

# Schema definition for FR-001 compliance
REQUIRED_COLUMNS = [
    'system_id',
    'element_a',
    'element_b',
    'element_c',
    'composition_a',
    'composition_b',
    'composition_c',
    'temperature_k',
    'phase',
    'mean_atomic_radius',
    'electronegativity_variance',
    'valence_electron_count',
    'hume_rothery_concentration'
]

def load_processed_data(input_path: str) -> List[Dict[str, Any]]:
    """
    Load the processed data dictionary produced by generate_descriptors.
    Expects a JSON file containing a list of alloy records with descriptors.
    """
    if not os.path.exists(input_path):
        log_error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        log_error(f"Expected list of records in {input_path}, got {type(data)}")
        raise ValueError("Input data must be a list of records")
    
    return data

def write_csv_output(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write the processed data to a CSV file at output_path.
    Ensures schema compliance with REQUIRED_COLUMNS.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        log_info(f"Created output directory: {output_dir}")

    # Determine fieldnames from the first record, ensuring REQUIRED_COLUMNS are present
    fieldnames = list(REQUIRED_COLUMNS)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for record in data:
            # Validate record against schema before writing
            if not validate_descriptors(record):
                log_warning(f"Skipping record with invalid descriptors: {record.get('system_id', 'unknown')}")
                continue
            
            # Ensure numeric fields are formatted correctly
            row = {}
            for col in fieldnames:
                val = record.get(col)
                if val is None:
                    row[col] = ''
                elif isinstance(val, float):
                    # Format floats to reasonable precision to avoid scientific notation issues
                    row[col] = f"{val:.6f}"
                else:
                    row[col] = val
            
            writer.writerow(row)
    
    log_info(f"Wrote {len(data)} records to {output_path}")

def main():
    """
    Main entry point for T018: Write processed data to data/processed/descriptors.csv.
    This script expects the output from generate_descriptors (usually a JSON intermediate)
    or processes the raw data pipeline if the intermediate step is skipped in this specific flow.
    
    For this implementation, we assume the pipeline produces a JSON intermediate at 
    data/processed/descriptors_raw.json (or similar) which we then convert to CSV.
    If the intermediate doesn't exist, we attempt to run the descriptor generation logic
    on the raw data if available, but strictly speaking, T018 is the export step.
    
    To ensure robustness, we will look for the raw processed data in data/processed/
    or run the generation if the input is missing but raw data exists.
    """
    input_json_path = os.path.join(project_root, 'data', 'processed', 'descriptors_raw.json')
    output_csv_path = os.path.join(project_root, 'data', 'processed', 'descriptors.csv')
    
    # Fallback: if raw JSON doesn't exist, check if we need to run generation first
    # However, T015/T016/T017 should have produced the data. 
    # If T017 produced a JSON, we load it. If it produced nothing, we might need to re-run the feature pipeline.
    
    if not os.path.exists(input_json_path):
        log_warning(f"Intermediate file {input_json_path} not found. Attempting to regenerate descriptors from raw data...")
        # Re-run the feature generation to get the data for T018
        # We need to find the raw data source. Usually data/raw/alloy_data.csv or similar.
        # Since T015/T016/T017 are marked complete, we assume the data exists somewhere or the pipeline is designed to run sequentially.
        # Let's try to run the process_alloy_dataset function directly if we can find the raw input.
        
        raw_data_path = os.path.join(project_root, 'data', 'raw', 'alloy_data.csv')
        if not os.path.exists(raw_data_path):
            # Try common alternative names
            alt_paths = [
                os.path.join(project_root, 'data', 'raw', 'phase_data.csv'),
                os.path.join(project_root, 'data', 'raw', 'input.csv')
            ]
            for p in alt_paths:
                if os.path.exists(p):
                    raw_data_path = p
                    break
        
        if not os.path.exists(raw_data_path):
            log_error("Raw data source not found. Cannot proceed with T018 without input data.")
            log_error("Please ensure data/raw contains the source alloy data.")
            sys.exit(1)
        
        log_info(f"Regenerating descriptors from {raw_data_path}")
        # We need to import the function that actually generates the descriptors from raw data
        # The API surface says process_alloy_dataset is available in generate_descriptors
        # We need to know the signature. Assuming it takes a path and returns a list of dicts.
        # Since the API surface is limited, we assume it handles the loading or we load it here.
        # Let's assume process_alloy_dataset expects a list of dicts or a path.
        # To be safe, let's load the CSV here and pass to the function if it expects a list.
        
        try:
            with open(raw_data_path, 'r') as f:
                reader = csv.DictReader(f)
                raw_records = list(reader)
            
            # Call the feature generation
            # Note: The API surface says process_alloy_dataset is a public name.
            # We assume it returns the list of enriched records.
            enriched_data = process_alloy_dataset(raw_records)
            
            # Save intermediate for consistency
            with open(input_json_path, 'w') as f:
                json.dump(enriched_data, f, indent=2)
        except Exception as e:
            log_error(f"Failed to generate descriptors: {e}")
            sys.exit(1)
    else:
        log_info(f"Loading intermediate data from {input_json_path}")
        enriched_data = load_processed_data(input_json_path)

    # Write to CSV
    write_csv_output(enriched_data, output_csv_path)

    # Compute checksum for the final output (Constitution Principle III)
    checksum_path = compute_and_store_checksum(output_csv_path)
    log_info(f"Checksum saved to {checksum_path}")
    log_info("T018 completed successfully.")

if __name__ == '__main__':
    main()

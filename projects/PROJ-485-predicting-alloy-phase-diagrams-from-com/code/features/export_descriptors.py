"""
Export processed descriptors to CSV with schema compliance.
This module implements T020: Write processed data to data/processed/descriptors.csv.
"""
import os
import sys
import csv
import json
from typing import Dict, List, Any, Optional
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

REQUIRED_COLUMNS = [
    "system_id",
    "element_a",
    "element_b",
    "composition",
    "temperature",
    "mean_atomic_radius",
    "electronegativity_variance",
    "valence_electron_count",
    "hume_rothery_concentration",
    "checksum"
]

def load_processed_data(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads processed descriptor data from a JSON or CSV intermediate file.
    Assumes the data has already been processed by generate_descriptors.py.
    """
    if not os.path.exists(input_path):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    log_info(f"Loading processed data from {input_path}")
    data = []
    
    # Try loading as JSON first (common intermediate format)
    if input_path.endswith('.json'):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif input_path.endswith('.csv'):
        with open(input_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    else:
        log_error(ErrorCode.INVALID_DATA_SCHEMA, "Unsupported input format. Expected .json or .csv")
        raise ValueError("Unsupported input format")

    return data

def validate_row_schema(row: Dict[str, Any]) -> bool:
    """
    Validates that a single row contains all required columns and valid data types.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in row]
    if missing:
        log_warning(f"Row missing columns: {missing}")
        return False

    # Validate numeric types
    numeric_cols = ['composition', 'temperature', 'mean_atomic_radius', 
                    'electronegativity_variance', 'valence_electron_count', 
                    'hume_rothery_concentration']
    
    for col in numeric_cols:
        try:
            float(row[col])
        except (ValueError, TypeError):
            log_warning(f"Row has invalid numeric value for {col}: {row[col]}")
            return False
    
    return True

def write_csv_output(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Writes the processed data to a CSV file with the required schema.
    """
    if not data:
        log_warning("No data to write.")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    log_info(f"Writing {len(data)} rows to {output_path}")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS, extrasaction='ignore')
        writer.writeheader()
        
        valid_count = 0
        for row in data:
            if validate_row_schema(row):
                writer.writerow(row)
                valid_count += 1
            else:
                log_warning(f"Skipping invalid row: {row}")
        
        log_info(f"Successfully wrote {valid_count} valid rows to {output_path}")

def main():
    """
    Main entry point for exporting descriptors.
    Expects an intermediate processed file (e.g., from generate_descriptors)
    and writes the final schema-compliant CSV.
    """
    # Default paths
    input_file = "data/processed/descriptors_intermediate.json"
    output_file = "data/processed/descriptors.csv"

    # Check if input exists, if not, try to generate it or fail
    if not os.path.exists(input_file):
        # Check if we have raw data to process
        raw_data_path = "data/processed/raw_filtered.csv"
        if os.path.exists(raw_data_path):
            log_info(f"Intermediate file not found, attempting to generate from {raw_data_path}")
            # In a real pipeline, this would call generate_descriptors logic
            # For now, we assume the pipeline runner has already done this step
            # or we simulate the call to generate_descriptors.main() if needed
            # To strictly follow T020, we assume the data is ready.
            # If the file is missing, we must fail loudly as per instructions.
            log_error(ErrorCode.DATA_SOURCE_MISSING, f"Processed data source missing: {input_file}")
            sys.exit(1)
        else:
            log_error(ErrorCode.DATA_SOURCE_MISSING, f"No input data found at {input_file} or {raw_data_path}")
            sys.exit(1)

    try:
        data = load_processed_data(input_file)
        write_csv_output(data, output_file)
        
        # Verify output exists
        if os.path.exists(output_file):
            log_info(f"SUCCESS: Descriptors exported to {output_file}")
            sys.exit(0)
        else:
            log_error(ErrorCode.RESOURCE_LIMIT_EXCEEDED, "Failed to create output file")
            sys.exit(1)
    except Exception as e:
        log_error(ErrorCode.RESOURCE_LIMIT_EXCEEDED, f"Export failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

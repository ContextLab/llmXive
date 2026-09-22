"""
Export processed descriptors to CSV with schema compliance.
Implements T018: Write processed data to data/processed/descriptors.csv with schema compliance (FR-001).
"""
import os
import sys
import csv
import json
from typing import Dict, List, Any, Optional

from utils.logging import get_logger, log_info, log_error, log_warning

# Define the expected schema for the output CSV based on FR-001 and T009b
# Required columns: temperature, composition, element_a, element_b
# Derived columns (from T015): mean_atomic_radius, electronegativity_variance, valence_electron_count, hume_rothery_concentration
REQUIRED_COLUMNS = [
    "temperature",
    "composition",
    "element_a",
    "element_b",
    "mean_atomic_radius",
    "electronegativity_variance",
    "valence_electron_count",
    "hume_rothery_concentration"
]

logger = get_logger(__name__)

def load_processed_data(input_path: str) -> List[Dict[str, Any]]:
    """Load processed data from a JSON or CSV intermediate file."""
    if not os.path.exists(input_path):
        log_error(logger, f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    log_info(logger, f"Loading processed data from {input_path}")

    if input_path.endswith('.json'):
        with open(input_path, 'r') as f:
            data = json.load(f)
    elif input_path.endswith('.csv'):
        data = []
        with open(input_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric strings to float/int where appropriate
                processed_row = {}
                for k, v in row.items():
                    if k in ["temperature", "composition", "mean_atomic_radius", "electronegativity_variance", "valence_electron_count", "hume_rothery_concentration"]:
                        try:
                            processed_row[k] = float(v)
                        except ValueError:
                            processed_row[k] = v
                    else:
                        processed_row[k] = v
                data.append(processed_row)
    else:
        log_error(logger, f"Unsupported input format: {input_path}")
        raise ValueError(f"Unsupported input format: {input_path}")

    log_info(logger, f"Loaded {len(data)} rows")
    return data

def validate_row_schema(row: Dict[str, Any]) -> bool:
    """Validate that a row contains all required columns and valid data types."""
    # Check for required columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in row]
    if missing_columns:
        log_warning(logger, f"Row missing required columns: {missing_columns}")
        return False

    # Validate numeric types for specific columns
    numeric_columns = ["temperature", "composition", "mean_atomic_radius", "electronegativity_variance", "valence_electron_count", "hume_rothery_concentration"]
    for col in numeric_columns:
        if col in row:
            if not isinstance(row[col], (int, float)):
                log_warning(logger, f"Row has non-numeric value for {col}: {row[col]}")
                return False
            # Check for reasonable ranges (basic sanity check)
            if col == "temperature" and (row[col] < 0 or row[col] > 10000):
                log_warning(logger, f"Temperature out of expected range: {row[col]}")
                return False
            if col == "composition" and (row[col] < 0 or row[col] > 100):
                log_warning(logger, f"Composition out of expected range: {row[col]}")
                return False

    return True

def write_csv_output(data: List[Dict[str, Any]], output_path: str) -> None:
    """Write validated data to a CSV file with schema compliance."""
    if not data:
        log_warning(logger, "No data to write")
        return

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        log_info(logger, f"Created output directory: {output_dir}")

    log_info(logger, f"Writing {len(data)} rows to {output_path}")

    valid_rows = []
    for i, row in enumerate(data):
        if validate_row_schema(row):
            valid_rows.append(row)
        else:
            log_warning(logger, f"Skipping invalid row {i}")

    if not valid_rows:
        log_error(logger, "No valid rows to write. Aborting.")
        raise ValueError("No valid rows to write. Aborting.")

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(valid_rows)

    log_info(logger, f"Successfully wrote {len(valid_rows)} rows to {output_path}")

def main():
    """Main entry point for exporting descriptors."""
    # Default paths - can be overridden by command line args if needed
    input_path = "data/processed/descriptors_raw.json"  # Assumed intermediate output from T015
    output_path = "data/processed/descriptors.csv"

    # Check for command line arguments
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    try:
        data = load_processed_data(input_path)
        write_csv_output(data, output_path)
        log_info(logger, "Export completed successfully")
    except Exception as e:
        log_error(logger, f"Export failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
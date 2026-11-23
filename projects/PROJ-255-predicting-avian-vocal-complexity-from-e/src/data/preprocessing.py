import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yaml

from src.utils.config import get_project_root, get_interim_data_dir, get_processed_data_dir
from src.utils.logging import setup_logger

logger = setup_logger(__name__)

def load_csv(file_path: Path) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_csv(data: List[Dict[str, str]], file_path: Path) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        logger.warning(f"No data to save to {file_path}")
        # Create empty file with headers if we know them, otherwise just create empty
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            pass
        return

    fieldnames = list(data[0].keys())
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def validate_against_schema(data: List[Dict[str, str]], schema_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate data against a YAML schema definition.
    Returns (is_valid, list_of_errors).
    """
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return False, [f"Schema file not found: {schema_path}"]

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    errors = []
    
    # Check required columns
    required_columns = schema.get('required_columns', [])
    if data:
        actual_columns = set(data[0].keys())
        missing_columns = set(required_columns) - actual_columns
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
    
    # Check data types if defined
    column_types = schema.get('column_types', {})
    if data and column_types:
        for row_idx, row in enumerate(data):
            for col, expected_type in column_types.items():
                if col in row:
                    val = row[col]
                    if expected_type == 'int':
                        try:
                            int(val)
                        except ValueError:
                            errors.append(f"Row {row_idx}: Column '{col}' expected int, got '{val}'")
                    elif expected_type == 'float':
                        try:
                            float(val)
                        except ValueError:
                            errors.append(f"Row {row_idx}: Column '{col}' expected float, got '{val}'")
                    # Add more type checks as needed

    return len(errors) == 0, errors

def combine_filtered_data_and_metrics(
    filtered_data_path: Path,
    metrics_path: Path,
    output_path: Path
) -> List[Dict[str, str]]:
    """
    Combine filtered SNR data with extracted vocal metrics.
    Assumes both files share a common key 'recording_id'.
    """
    if not filtered_data_path.exists():
        raise FileNotFoundError(f"Filtered data file not found: {filtered_data_path}")
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    filtered_data = load_csv(filtered_data_path)
    metrics_data = load_csv(metrics_path)

    # Index metrics by recording_id
    metrics_index = {row['recording_id']: row for row in metrics_data}

    combined = []
    for row in filtered_data:
        rec_id = row.get('recording_id')
        if rec_id and rec_id in metrics_index:
            metrics_row = metrics_index[rec_id]
            # Merge, keeping filtered_data keys first, then adding metrics
            merged = {**row, **metrics_row}
            combined.append(merged)
        else:
            logger.warning(f"Recording ID {rec_id} in filtered data not found in metrics. Skipping.")

    logger.info(f"Combined {len(combined)} records from filtered data and metrics.")
    save_csv(combined, output_path)
    return combined

def main():
    """
    Main entry point for T020:
    1. Load filtered SNR data (from T017b)
    2. Load extracted metrics (from T019)
    3. Combine them into final_dataset.csv
    4. Validate against dataset.schema.yaml
    """
    root = get_project_root()
    interim_dir = get_interim_data_dir()
    processed_dir = get_processed_data_dir()

    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Input paths
    filtered_snr_path = interim_dir / "filtered_snr.csv"
    metrics_path = interim_dir / "vocal_metrics.csv"
    schema_path = root / "contracts" / "dataset.schema.yaml"
    output_path = processed_dir / "final_dataset.csv"

    logger.info(f"Starting T020: Combining filtered data and metrics.")
    logger.info(f"  Filtered SNR: {filtered_snr_path}")
    logger.info(f"  Metrics: {metrics_path}")
    logger.info(f"  Schema: {schema_path}")
    logger.info(f"  Output: {output_path}")

    try:
        # Combine data
        combined_data = combine_filtered_data_and_metrics(
            filtered_snr_path,
            metrics_path,
            output_path
        )

        if not combined_data:
            logger.error("Combined data is empty. Cannot validate or proceed.")
            return 1

        # Validate against schema
        is_valid, errors = validate_against_schema(combined_data, schema_path)

        if is_valid:
            logger.info("Validation PASSED. Final dataset created successfully.")
            logger.info(f"Total records: {len(combined_data)}")
            logger.info(f"Columns: {list(combined_data[0].keys())}")
            return 0
        else:
            logger.error("Validation FAILED.")
            for err in errors:
                logger.error(f"  - {err}")
            # Still save the file, but return error code
            logger.warning(f"Saved invalid dataset to {output_path} for inspection.")
            return 1

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during T020: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

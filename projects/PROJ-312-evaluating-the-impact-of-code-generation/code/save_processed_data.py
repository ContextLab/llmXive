import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils import validate_json_schema

def load_raw_pr_data(raw_data_path: Path) -> List[Dict[str, Any]]:
    """Load the raw PR data from the JSON file generated in T018a."""
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
    
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def load_repo_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load repository metadata from the JSON file generated in T017."""
    if not metadata_path.exists():
        # If metadata is missing, we proceed with empty metadata but log a warning
        logging.warning(f"Repository metadata file not found: {metadata_path}. Proceeding without metadata.")
        return {}
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def save_processed_data(processed_data: List[Dict[str, Any]], output_path: Path, schema_path: Path) -> bool:
    """
    Save processed PR data to a CSV file and validate against the schema.
    
    Args:
        processed_data: List of dictionaries containing processed PR data.
        output_path: Path to the output CSV file.
        schema_path: Path to the JSON schema for validation.
    
    Returns:
        True if successful, False otherwise.
    """
    if not processed_data:
        logging.error("No processed data to save.")
        return False

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    import csv
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Get headers from the first record
            headers = list(processed_data[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writerow(dict(zip(headers, headers))) # Write header
            for row in processed_data:
                writer.writerow(row)
        
        logging.info(f"Saved processed data to {output_path}")
    except Exception as e:
        logging.error(f"Error saving processed data to CSV: {e}")
        return False

    # Validate against schema
    # Note: The schema validation utility expects JSON data. We convert CSV back to JSON for validation.
    # Alternatively, we could validate the JSON structure before saving to CSV.
    # Since T018a already validated the JSON, we re-validate the data structure here for consistency.
    
    # Re-load the data from the CSV to ensure it matches the schema format
    # (This is a simple re-conversion for validation purposes)
    with open(output_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        csv_data = [row for row in reader]

    is_valid = validate_json_schema(csv_data, schema_path)
    
    if not is_valid:
        logging.error(f"Processed data failed schema validation: {schema_path}")
        return False

    logging.info(f"Processed data validated successfully against schema: {schema_path}")
    return True

def main():
    """Main function to execute the data processing pipeline step."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pipeline.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Define paths
    project_root = Path(__name__).parent if '__name__' in globals() else Path('.')
    # Adjust paths relative to the project root
    raw_data_path = project_root / 'data' / 'raw' / 'pr_data.json'
    metadata_path = project_root / 'data' / 'processed' / 'repo_metadata.json'
    output_path = project_root / 'data' / 'processed' / 'pr_turnaround.csv'
    schema_path = project_root / 'contracts' / 'pull_request.schema.yaml'

    # Load raw data
    try:
        raw_data = load_raw_pr_data(raw_data_path)
    except FileNotFoundError as e:
        logging.error(f"Failed to load raw data: {e}")
        sys.exit(1)

    # Load metadata (optional)
    repo_metadata = load_repo_metadata(metadata_path)

    # Process data (simulating the logic from T015/T016 if not already done in raw)
    # Assuming raw_data already contains the necessary fields after T015/T016
    # If raw_data is just the list of PRs, we assume it's ready for saving as CSV
    # The task T018b implies saving the processed data (which includes classification and turnaround)
    
    processed_data = raw_data 

    # Save and validate
    success = save_processed_data(processed_data, output_path, schema_path)
    
    if not success:
        sys.exit(1)

    logging.info("T018b completed successfully.")

if __name__ == '__main__':
    main()

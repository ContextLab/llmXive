import json
import os
import re
import logging
import hashlib
import csv
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Helper Functions (from existing API surface) ---

def load_json_file(filepath: str) -> Any:
    """Load and return JSON data from a file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Any) -> None:
    """Save data as JSON to a file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def calculate_checksum(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(checksums_file: str, filepath: str, checksum: str) -> None:
    """Update the checksums file with a new entry."""
    os.makedirs(os.path.dirname(checksums_file), exist_ok=True)
    checksums = {}
    if os.path.exists(checksums_file):
        with open(checksums_file, 'r', encoding='utf-8') as f:
            try:
                checksums = json.load(f)
            except json.JSONDecodeError:
                checksums = {}
    
    checksums[os.path.basename(filepath)] = checksum
    
    with open(checksums_file, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)

def remove_pii_from_string(text: str) -> str:
    """Remove common PII patterns from a string."""
    if not isinstance(text, str):
        return text
    
    # Email pattern
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED_EMAIL]', text)
    # Phone pattern (US)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]', text)
    # IP address
    text = re.sub(r'\b\d{1,3}(?:\.\d{1,3}){3}\b', '[REDACTED_IP]', text)
    # Social Security Number
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', text)
    
    return text

def remove_pii_from_list(data_list: List[Any]) -> List[Any]:
    """Remove PII from a list of items."""
    return [remove_pii_from_string(item) if isinstance(item, str) else item for item in data_list]

def remove_pii_from_dict(data_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Remove PII from a dictionary."""
    cleaned = {}
    for key, value in data_dict.items():
        if isinstance(value, str):
            cleaned[key] = remove_pii_from_string(value)
        elif isinstance(value, list):
            cleaned[key] = remove_pii_from_list(value)
        elif isinstance(value, dict):
            cleaned[key] = remove_pii_from_dict(value)
        else:
            cleaned[key] = value
    return cleaned

def remove_pii(data: Any) -> Any:
    """Recursively remove PII from data structures."""
    if isinstance(data, str):
        return remove_pii_from_string(data)
    elif isinstance(data, list):
        return remove_pii_from_list(data)
    elif isinstance(data, dict):
        return remove_pii_from_dict(data)
    return data

def validate_input_data(validation_report_path: str) -> bool:
    """
    Validate that the input data has passed schema validation.
    Reads T033's output (validation_report.json) to ensure validation passed.
    """
    if not os.path.exists(validation_report_path):
        logger.error(f"Validation report not found: {validation_report_path}")
        return False
    
    try:
        report = load_json_file(validation_report_path)
        # Expecting a structure like {"status": "passed", ...}
        if report.get("status") != "passed":
            logger.error(f"Data validation failed. Report: {report}")
            return False
        
        logger.info("Schema validation passed. Proceeding with cleaning.")
        return True
    except Exception as e:
        logger.error(f"Error reading validation report: {e}")
        return False

def handle_incomplete_records(records: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Handle incomplete/abandoned records.
    Flags them for exclusion from time analysis but retains for dropout reporting.
    
    Returns:
        tuple: (cleaned_records, dropout_records)
    """
    cleaned = []
    dropouts = []
    
    for record in records:
        # Determine if record is incomplete/abandoned
        # Criteria: missing critical fields like 'session_end_time', 'final_time', or explicit 'abandoned' flag
        is_incomplete = (
            record.get('abandoned', False) or
            record.get('status') == 'incomplete' or
            not record.get('session_end_time') or
            not record.get('final_time')
        )
        
        if is_incomplete:
            # Flag for exclusion from time analysis
            record['exclude_from_time_analysis'] = True
            record['dropout_reason'] = record.get('dropout_reason', 'unknown')
            dropouts.append(record)
        else:
            cleaned.append(record)
    
    logger.info(f"Identified {len(dropouts)} incomplete/abandoned records.")
    return cleaned, dropouts

def save_dropouts(dropouts: List[Dict[str, Any]], output_path: str) -> None:
    """Save dropout records to a JSON file for reporting."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_json_file(output_path, dropouts)
    logger.info(f"Saved {len(dropouts)} dropout records to {output_path}")

def save_cleaned_dataset_csv(records: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save cleaned records to a CSV file.
    Flattens nested structures where necessary for CSV format.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if not records:
        logger.warning("No records to save to CSV.")
        # Create empty CSV with headers if possible, or just exit
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write("")
        return

    # Determine all keys from all records to form headers
    all_keys = set()
    for record in records:
        all_keys.update(record.keys())
    
    headers = sorted(list(all_keys))
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        
        for record in records:
            # Flatten nested dicts/lists for CSV compatibility
            flat_record = {}
            for key, value in record.items():
                if isinstance(value, (dict, list)):
                    flat_record[key] = json.dumps(value)
                else:
                    flat_record[key] = value
            writer.writerow(flat_record)
    
    logger.info(f"Saved {len(records)} cleaned records to {output_path}")

def main():
    """
    Main entry point for T032: Aggregate cleaning steps.
    1. Check validation status from T033.
    2. Load raw participant logs.
    3. Remove PII.
    4. Handle incomplete records.
    5. Save cleaned dataset as CSV.
    6. Save dropout records.
    7. Generate checksums.
    """
    # Paths
    validation_report_path = "data/processed/validation_report.json"
    raw_data_path = "data/raw/participant_logs.json"
    cleaned_output_path = "data/processed/cleaned_dataset.csv"
    dropouts_output_path = "data/processed/dropout_records.json"
    checksums_file = "data/checksums.txt"
    
    # Step 1: Validate input data (Gate from T033)
    if not validate_input_data(validation_report_path):
        logger.error("Validation failed. Aborting cleaning process.")
        raise RuntimeError("Data validation failed. Aborting cleaning process.")
    
    # Step 2: Load raw data
    if not os.path.exists(raw_data_path):
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
    
    raw_data = load_json_file(raw_data_path)
    
    # Ensure raw_data is a list of records
    if isinstance(raw_data, dict):
        # Assume it might be wrapped in a 'records' key or similar
        records = raw_data.get('records', [raw_data])
    elif isinstance(raw_data, list):
        records = raw_data
    else:
        records = [raw_data]
    
    logger.info(f"Loaded {len(records)} raw records.")
    
    # Step 3: Remove PII
    cleaned_records = [remove_pii(record) for record in records]
    logger.info("PII removal completed.")
    
    # Step 4: Handle incomplete records
    final_cleaned_records, dropouts = handle_incomplete_records(cleaned_records)
    
    # Step 5: Save cleaned dataset to CSV
    save_cleaned_dataset_csv(final_cleaned_records, cleaned_output_path)
    
    # Step 6: Save dropout records
    save_dropouts(dropouts, dropouts_output_path)
    
    # Step 7: Generate checksums
    if os.path.exists(cleaned_output_path):
        checksum = calculate_checksum(cleaned_output_path)
        update_checksums(checksums_file, cleaned_output_path, checksum)
        logger.info(f"Checksum for cleaned dataset: {checksum}")
    
    if os.path.exists(dropouts_output_path):
        dropout_checksum = calculate_checksum(dropouts_output_path)
        update_checksums(checksums_file, dropouts_output_path, dropout_checksum)
        logger.info(f"Checksum for dropout records: {dropout_checksum}")
    
    logger.info("Data cleaning pipeline completed successfully.")

if __name__ == "__main__":
    main()
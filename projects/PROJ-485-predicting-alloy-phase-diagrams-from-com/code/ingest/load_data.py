import os
import sys
import time
import json
import hashlib
import csv
from typing import Dict, List, Any, Optional, Tuple

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode
from utils.config import get_config

logger = get_logger(__name__)

def check_data_source_availability() -> bool:
    """
    Check if data sources are available in config.
    Returns True if at least one valid source is configured.
    """
    config = get_config()
    nist_url = config.get('nist_janaf_url', '')
    sgte_url = config.get('sgte_url', '')
    local_path = config.get('local_fallback_path', '')

    if nist_url:
        return True
    if sgte_url:
        return True
    if local_path and os.path.exists(local_path):
        return True

    log_error(ErrorCode.DATA_SOURCE_MISSING, "No valid data source configured")
    return False

def load_data_from_url(url: str, max_retries: int = 3) -> List[Dict[str, Any]]:
    """
    Load data from a URL with exponential backoff.
    Note: This is a placeholder for actual HTTP implementation.
    In a real scenario, this would use requests library.
    """
    # Simulating a fetch attempt that would fail if no real URL provided
    if not url:
        raise ValueError("URL is empty")
    
    # Placeholder logic - in real implementation, this would fetch data
    # For now, we assume the data is provided via local fallback or injected
    raise NotImplementedError("URL fetching requires real endpoint")

def load_data_from_local_fallback() -> List[Dict[str, Any]]:
    """
    Load data from local CSV fallback file.
    Raises DATA_SOURCE_MISSING if file doesn't exist or path is empty.
    """
    config = get_config()
    local_path = config.get('local_fallback_path', '')

    if not local_path:
        log_error(ErrorCode.DATA_SOURCE_MISSING, "Local fallback path is empty")
        raise ValueError(ErrorCode.DATA_SOURCE_MISSING.value)

    if not os.path.exists(local_path):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Local file not found: {local_path}")
        raise ValueError(ErrorCode.DATA_SOURCE_MISSING.value)

    data = []
    try:
        with open(local_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        log_info(None, f"Loaded {len(data)} rows from local fallback: {local_path}")
        return data
    except Exception as e:
        log_error(ErrorCode.INVALID_DATA_SCHEMA, f"Failed to read local file: {str(e)}")
        raise

def filter_missing_temperature(data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter out entries with missing temperature values.
    Returns (filtered_data, skipped_rows).
    """
    filtered = []
    skipped = []

    for row in data:
        temp = row.get('temperature')
        if temp is None or temp == '':
            # Check if it's a ternary system
            # Assuming ternary systems have 3 element columns or specific marker
            is_ternary = len([k for k in row.keys() if k.startswith('element_')]) >= 3
            
            if is_ternary:
                log_warning(
                    ErrorCode.MISSING_TEMP_COORDS,
                    f"Row excluded: ternary system missing temperature-composition coordinates"
                )
                skipped.append(row)
            else:
                skipped.append(row)
        else:
            filtered.append(row)

    return filtered, skipped

def compute_row_checksum(row: Dict[str, Any]) -> str:
    """
    Compute SHA-256 checksum for a single row.
    Used for data integrity verification (Constitution Principle III).
    """
    # Create a deterministic string representation of the row
    sorted_items = sorted(row.items())
    row_str = json.dumps(sorted_items, sort_keys=True)
    return hashlib.sha256(row_str.encode('utf-8')).hexdigest()

def compute_dataset_checksum(data: List[Dict[str, Any]]) -> str:
    """
    Compute overall checksum for the entire dataset.
    """
    combined_str = ""
    for row in data:
        combined_str += compute_row_checksum(row)
    
    return hashlib.sha256(combined_str.encode('utf-8')).hexdigest()

def update_state_with_checksum(checksum: str, data_source: str):
    """
    Update the project state file with the data checksum.
    Implements Constitution Principle V (State Management).
    """
    from main import load_state, save_state, ensure_state_directory

    ensure_state_directory()
    state = load_state()

    if 'ingest' not in state:
        state['ingest'] = {}

    state['ingest']['last_data_checksum'] = checksum
    state['ingest']['last_data_source'] = data_source
    state['ingest']['timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    state['ingest']['status'] = 'checksummed'

    save_state(state)
    log_info(None, f"State updated with checksum: {checksum[:16]}...")

def load_data() -> List[Dict[str, Any]]:
    """
    Main data loading function that:
    1. Checks source availability
    2. Loads from URL or local fallback
    3. Filters missing temperatures
    4. Computes and stores checksum
    5. Updates state
    """
    if not check_data_source_availability():
        raise ValueError(ErrorCode.DATA_SOURCE_MISSING.value)

    config = get_config()
    data = []

    # Try URL first if configured
    nist_url = config.get('nist_janaf_url', '')
    sgte_url = config.get('sgte_url', '')

    if nist_url or sgte_url:
        # In real implementation, try to fetch from URL
        # For this task, we assume local fallback is used for testing
        log_info(None, "URL sources configured but using local fallback for checksum demo")

    # Fall back to local file
    data = load_data_from_local_fallback()

    if not data:
        log_error(ErrorCode.INVALID_DATA_SCHEMA, "No data loaded from any source")
        raise ValueError("No data loaded")

    # Filter missing temperatures
    filtered_data, skipped = filter_missing_temperature(data)
    
    if len(skipped) > 0:
        log_warning(None, f"Skipped {len(skipped)} rows due to missing temperature")

    # Compute checksum for integrity verification
    checksum = compute_dataset_checksum(filtered_data)
    log_info(None, f"Computed dataset checksum: {checksum}")

    # Update state with checksum (Constitution Principle V)
    update_state_with_checksum(checksum, "local_fallback")

    return filtered_data

def main():
    """
    Entry point for data loading with checksumming.
    """
    try:
        data = load_data()
        log_info(None, f"Successfully loaded and checksummed {len(data)} rows")
        
        # Save a sample of the checksummed data for verification
        output_path = 'data/processed/ingested_data_checksummed.csv'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if data:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = list(data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            log_info(None, f"Saved processed data to {output_path}")
        
        return 0
    except Exception as e:
        log_error(None, f"Data loading failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
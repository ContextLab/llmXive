import os
import sys
import time
import json
import hashlib
import csv
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# Local imports from project structure
from utils.logging import get_logger, log_error, log_info, log_warning
from utils.error_codes import ErrorCode
from utils.checksum import compute_file_sha256

logger = get_logger(__name__)

def check_data_source_availability(url: str) -> bool:
    """Check if the primary data source URL is accessible."""
    # In a real implementation, this would perform a HEAD request
    # For now, we assume the URL is valid if not empty
    if not url or url.strip() == "":
        return False
    return True

def load_data_from_url(url: str) -> List[Dict[str, Any]]:
    """Load data from a remote URL (NIST-JANAF/SGTE)."""
    log_info(logger, f"Attempting to load data from URL: {url}")
    # Placeholder for actual HTTP request logic
    # This would typically use requests.get()
    raise NotImplementedError("URL loading not implemented in this context")

def load_data_from_local_fallback(path: str) -> List[Dict[str, Any]]:
    """Load data from a local CSV fallback file."""
    log_info(logger, f"Loading data from local fallback: {path}")
    if not os.path.exists(path):
        log_error(logger, f"Local fallback file not found: {path}")
        raise FileNotFoundError(f"Local fallback file not found: {path}")
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def filter_missing_temperature(data: List[Dict[str, Any]], log_path: str) -> List[Dict[str, Any]]:
    """
    Filter out entries with missing temperature values OR ternary systems 
    lacking temperature-composition coordinates.
    
    Logs MISSING_TEMP_COORDS errors to the specified log file in JSON format.
    """
    if not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path))
    
    filtered_data = []
    
    with open(log_path, 'a', encoding='utf-8') as log_file:
        for idx, row in enumerate(data):
            try:
                # Check for missing temperature
                temp_val = row.get('temperature')
                if temp_val is None or temp_val == '' or temp_val == 'NA':
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "level": "ERROR",
                        "code": ErrorCode.MISSING_TEMP_COORDS.value,
                        "message": f"Row {idx} excluded: missing temperature/coordinates"
                    }
                    log_file.write(json.dumps(log_entry) + "\n")
                    log_error(logger, f"Row {idx} excluded: missing temperature/coordinates")
                    continue
                
                # Check for ternary systems lacking composition coordinates
                # Assuming ternary systems have 'element_c' defined but missing 'composition_c'
                if 'element_c' in row and row['element_c']:
                    comp_a = row.get('composition_a')
                    comp_b = row.get('composition_b')
                    comp_c = row.get('composition_c')
                    
                    if comp_a is None or comp_a == '' or comp_b is None or comp_b == '' or comp_c is None or comp_c == '':
                        log_entry = {
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "level": "ERROR",
                            "code": ErrorCode.MISSING_TEMP_COORDS.value,
                            "message": f"Row {idx} excluded: missing temperature/coordinates for ternary system"
                        }
                        log_file.write(json.dumps(log_entry) + "\n")
                        log_error(logger, f"Row {idx} excluded: missing temperature/coordinates for ternary system")
                        continue
                
                # If we get here, the row is valid
                filtered_data.append(row)
                
            except Exception as e:
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": "ERROR",
                    "code": ErrorCode.INVALID_DATA_SCHEMA.value,
                    "message": f"Row {idx} excluded due to parsing error: {str(e)}"
                }
                log_file.write(json.dumps(log_entry) + "\n")
                log_error(logger, f"Row {idx} excluded due to parsing error: {str(e)}")
                continue
    
    return filtered_data

def load_data(config: Dict[str, Any], output_path: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Main entry point for loading data with filtering and checksumming.
    
    Args:
        config: Configuration dictionary containing data source URLs and paths
        output_path: Path to save the processed data CSV
    
    Returns:
        Tuple of (loaded_data, checksum)
    """
    nist_url = config.get('nist_janaf_url', '')
    sgte_url = config.get('sgte_url', '')
    local_path = config.get('local_fallback_path', '')
    log_path = os.path.join(os.path.dirname(output_path), '..', 'logs', 'pipeline.log')
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    data = None
    
    # Try primary sources first
    if check_data_source_availability(nist_url):
        try:
            data = load_data_from_url(nist_url)
        except Exception as e:
            log_warning(logger, f"Failed to load from NIST-JANAF: {e}")
    
    if data is None and check_data_source_availability(sgte_url):
        try:
            data = load_data_from_url(sgte_url)
        except Exception as e:
            log_warning(logger, f"Failed to load from SGTE: {e}")
    
    # Fallback to local file
    if data is None:
        if local_path and os.path.exists(local_path):
            try:
                data = load_data_from_local_fallback(local_path)
            except Exception as e:
                log_error(logger, f"Failed to load from local fallback: {e}")
                raise
        else:
            raise FileNotFoundError("No valid data source available")
    
    # Filter missing temperatures and invalid coordinates
    log_info(logger, f"Filtering {len(data)} records for missing temperature/coordinates")
    filtered_data = filter_missing_temperature(data, log_path)
    log_info(logger, f"Filtered data: {len(filtered_data)} records remaining")
    
    # Write output
    if filtered_data:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = list(filtered_data[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_data)
        
        # Compute checksum
        checksum = compute_file_sha256(output_path)
        log_info(logger, f"Data written to {output_path} with checksum {checksum}")
        return filtered_data, checksum
    
    raise ValueError("No valid data remaining after filtering")

def main():
    """Main execution entry point."""
    # Load configuration
    config_path = 'code/config.yaml'
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    output_path = config.get('local_fallback_path', 'data/processed/raw_data.csv')
    
    try:
        data, checksum = load_data(config, output_path)
        print(f"Successfully loaded and filtered data. Checksum: {checksum}")
    except Exception as e:
        log_error(logger, f"Data loading failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
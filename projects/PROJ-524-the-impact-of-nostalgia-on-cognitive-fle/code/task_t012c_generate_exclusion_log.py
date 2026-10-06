"""
Task T012c: Generate Exclusion Log
Reads exclusion counts from data/processed/exclusion_counts.json and writes
data/processed/exclusion_log.json with standardized keys.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from config import get_config

# Setup logging
logger = setup_logging(__name__)

def get_config_paths() -> Dict[str, Path]:
    """Retrieve configured paths from config."""
    config = get_config()
    paths = config.get('paths', {})
    return {
        'root': Path(paths.get('root', '.')),
        'processed': Path(paths.get('processed', 'data/processed')),
    }

def load_exclusion_counts(paths: Dict[str, Path]) -> Dict[str, Any]:
    """
    Load exclusion counts from data/processed/exclusion_counts.json.
    Returns an empty dict if file is missing, to allow graceful handling.
    """
    filepath = paths['processed'] / 'exclusion_counts.json'
    if not filepath.exists():
        log_warning(f"Exclusion counts file not found: {filepath}. Initializing empty counts.")
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        log_info(f"Loaded exclusion counts from {filepath}")
        return data
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in exclusion counts file {filepath}: {e}")
        return {}

def check_simulation_fallback(paths: Dict[str, Path]) -> bool:
    """
    Check if simulation fallback was used by inspecting data/raw/metadata.json.
    """
    metadata_path = paths['root'] / 'data' / 'raw' / 'metadata.json'
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            if metadata.get('simulation_mode', False):
                log_info("Simulation fallback detected in metadata.")
                return True
        except (json.JSONDecodeError, IOError) as e:
            log_warning(f"Could not read metadata to check simulation mode: {e}")
    return False

def generate_exclusion_log(counts: Dict[str, Any], is_simulation: bool) -> Dict[str, Any]:
    """
    Construct the exclusion log dictionary with standardized keys.
    """
    log_data = {
        'timestamp': get_timestamp(),
        'source_file': 'exclusion_counts.json',
        'simulation_fallback': is_simulation,
        'exclusion_counts': {
            'ERR_MISSING_AGE_FIELD': counts.get('ERR_MISSING_AGE_FIELD', 0),
            'ERR_MISSING_SCORE': counts.get('ERR_MISSING_SCORE', 0),
            'ERR_MMSE_IMPAIRED': counts.get('ERR_MMSE_IMPAIRED', 0),
        }
    }
    return log_data

def save_exclusion_log(log_data: Dict[str, Any], paths: Dict[str, Path]) -> Path:
    """
    Write the exclusion log to data/processed/exclusion_log.json.
    """
    output_path = paths['processed'] / 'exclusion_log.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2)
    
    log_info(f"Exclusion log written to {output_path}")
    return output_path

def main() -> int:
    """
    Main entry point for Task T012c.
    """
    try:
        paths = get_config_paths()
        
        # Load existing counts
        counts = load_exclusion_counts(paths)
        
        # Check for simulation fallback
        is_simulation = check_simulation_fallback(paths)
        
        # Generate log structure
        log_data = generate_exclusion_log(counts, is_simulation)
        
        # Write output
        save_exclusion_log(log_data, paths)
        
        log_info("Task T012c completed successfully.")
        return 0
        
    except Exception as e:
        log_error(f"Task T012c failed with exception: {e}")
        raise

if __name__ == '__main__':
    exit(main())
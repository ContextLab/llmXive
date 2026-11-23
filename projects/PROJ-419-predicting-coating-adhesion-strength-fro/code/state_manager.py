import os
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional

from utils import ensure_state_dir, setup_logging

logger = setup_logging()

def calculate_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate checksum for a single file."""
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise

def scan_raw_data_directory(raw_data_dir: str = "data/raw") -> List[str]:
    """Scan directory for data files."""
    if not os.path.exists(raw_data_dir):
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return []
    
    data_files = []
    for root, _, files in os.walk(raw_data_dir):
        for file in files:
            if file.endswith(('.csv', '.json', '.parquet', '.xlsx')):
                data_files.append(os.path.join(root, file))
    return data_files

def generate_state_checksums(raw_data_dir: str = "data/raw", 
                             state_dir: str = "state", 
                             algorithm: str = "sha256") -> Dict[str, str]:
    """Generate checksums for all raw data files."""
    data_files = scan_raw_data_directory(raw_data_dir)
    checksums = {}
    
    for file_path in data_files:
        try:
            checksum = calculate_file_checksum(file_path, algorithm)
            relative_path = os.path.relpath(file_path, start="data")
            checksums[relative_path] = checksum
            logger.info(f"Checksum generated for {relative_path}: {checksum[:16]}...")
        except FileNotFoundError:
            logger.warning(f"Skipping missing file: {file_path}")
        except Exception as e:
            logger.error(f"Error calculating checksum for {file_path}: {str(e)}")
    
    return checksums

def write_state_file(checksums: Dict[str, str], 
                    state_dir: str = "state", 
                    filename: str = "state_checksums.yaml") -> str:
    """Write checksums to a YAML state file."""
    ensure_state_dir(state_dir)
    state_file_path = os.path.join(state_dir, filename)
    
    state_data = {
        "generated_at": __import__('datetime').datetime.now().isoformat(),
        "algorithm": "sha256",
        "files": checksums
    }
    
    with open(state_file_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    logger.info(f"State file written to {state_file_path}")
    return state_file_path

def verify_state_checksums(state_file: str, 
                          raw_data_dir: str = "data/raw") -> bool:
    """Verify checksums against current files."""
    try:
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f)
        
        expected_checksums = state_data.get("files", {})
        algorithm = state_data.get("algorithm", "sha256")
        
        all_valid = True
        for relative_path, expected_checksum in expected_checksums.items():
            full_path = os.path.join(raw_data_dir, relative_path)
            
            if not os.path.exists(full_path):
                logger.error(f"File missing during verification: {full_path}")
                all_valid = False
                continue
            
            actual_checksum = calculate_file_checksum(full_path, algorithm)
            
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {relative_path}")
                logger.error(f"  Expected: {expected_checksum}")
                logger.error(f"  Actual:   {actual_checksum}")
                all_valid = False
            else:
                logger.info(f"Checksum verified for {relative_path}")
        
        return all_valid
        
    except FileNotFoundError:
        logger.error(f"State file not found: {state_file}")
        return False
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in state file: {str(e)}")
        return False

def main():
    """Main entry point for state_manager module."""
    logger = setup_logging()
    logger.info("State manager module loaded")
    
    # Example usage
    raw_data_dir = "data/raw"
    state_dir = "state"
    
    if os.path.exists(raw_data_dir):
        logger.info(f"Scanning {raw_data_dir} for data files...")
        checksums = generate_state_checksums(raw_data_dir, state_dir)
        
        if checksums:
            state_file = write_state_file(checksums, state_dir)
            logger.info(f"Verification status: {verify_state_checksums(state_file, raw_data_dir)}")
        else:
            logger.warning("No data files found to checksum")
    else:
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")

if __name__ == "__main__":
    main()

"""
State Registry Module.
Handles initialization, scanning, and verification of file checksums for data provenance.
"""
import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from logging_config import get_logger, log_provenance, log_warning

logger = get_logger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculates the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal digest string.
    """
    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        raise

def scan_raw_data_directory(raw_dir: Path) -> Dict[str, str]:
    """
    Scans the raw data directory and calculates checksums for all files found.
    
    Args:
        raw_dir: Path to the raw data directory.
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    checksums = {}
    if not raw_dir.exists():
        logger.warning(f"Raw data directory {raw_dir} does not exist.")
        return checksums
    
    for root, _, files in os.walk(raw_dir):
        for file in files:
            full_path = Path(root) / file
            relative_path = full_path.relative_to(raw_dir)
            checksums[str(relative_path)] = calculate_file_checksum(full_path)
            
    return checksums

def initialize_state_registry(state_path: Path, raw_dir: Path) -> None:
    """
    Initializes or updates the state registry with current file checksums.
    
    Args:
        state_path: Path to the state registry YAML file.
        raw_dir: Path to the raw data directory to scan.
    """
    checksums = scan_raw_data_directory(raw_dir)
    
    registry = {
        "project_id": "PROJ-077-investigating-the-correlation-between-gu",
        "created_at": None, # Timestamp could be added here
        "artifact_hashes": checksums
    }
    
    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w') as f:
        yaml.dump(registry, f, default_flow_style=False)
        
    log_provenance("State Registry Initialized", {
        "path": str(state_path),
        "files_recorded": len(checksums)
    })
    logger.info(f"State registry initialized at {state_path} with {len(checksums)} files.")

def load_state_registry(state_path: Path) -> Optional[Dict[str, Any]]:
    """
    Loads the state registry from a YAML file.
    
    Args:
        state_path: Path to the state registry YAML file.
        
    Returns:
        Dictionary containing the registry data, or None if file not found.
    """
    if not state_path.exists():
        return None
        
    try:
        with open(state_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load state registry: {e}")
        return None

def verify_file_checksums(file_paths: List[Path]) -> Dict[str, str]:
    """
    Verifies checksums for a list of file paths.
    
    Args:
        file_paths: List of file paths to verify.
        
    Returns:
        Dictionary mapping file paths (as strings) to their calculated checksums.
    """
    return {str(p): calculate_file_checksum(p) for p in file_paths}

def main():
    """
    CLI entry point for state registry operations.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage project state registry.")
    parser.add_argument("command", choices=["init", "verify"], help="Command to execute.")
    parser.add_argument("--state", type=str, default="state/projects/PROJ-077-investigating-the-correlation-between-gu.yaml", help="Path to state registry file.")
    parser.add_argument("--raw", type=str, default="data/raw", help="Path to raw data directory.")
    
    args = parser.parse_args()
    
    state_path = Path(args.state)
    raw_path = Path(args.raw)
    
    if args.command == "init":
        initialize_state_registry(state_path, raw_path)
    elif args.command == "verify":
        registry = load_state_registry(state_path)
        if not registry:
            logger.error("State registry not found.")
            sys.exit(1)
        
        expected_hashes = registry.get('artifact_hashes', {})
        if not expected_hashes:
            logger.warning("Registry is empty.")
            sys.exit(0)
            
        for rel_path, expected_hash in expected_hashes.items():
            full_path = raw_path / rel_path
            if not full_path.exists():
                logger.error(f"Missing file: {rel_path}")
                sys.exit(1)
            
            actual_hash = calculate_file_checksum(full_path)
            if actual_hash != expected_hash:
                logger.error(f"Checksum mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
                sys.exit(1)
            
        logger.info("All checksums verified successfully.")

if __name__ == "__main__":
    import sys
    main()

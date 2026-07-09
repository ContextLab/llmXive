"""
State Manager Module for llmXive Coating Adhesion Project.

Implements Constitution Principle III: Data integrity verification via checksums.
Provides logic to generate/update state YAML files with checksums for raw data files.
"""
import os
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Constants
STATE_DIR = "state"
STATE_FILE = "state/raw_data_checksums.yaml"
RAW_DATA_DIR = "data/raw"
ALGORITHM = "sha256"

def calculate_file_checksum(file_path: str, algorithm: str = ALGORITHM) -> str:
    """
    Calculate the cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal digest string of the file checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise

def scan_raw_data_directory(directory: str = RAW_DATA_DIR) -> List[Dict[str, str]]:
    """
    Scan the raw data directory for all files and their metadata.
    
    Args:
        directory: Path to the raw data directory.
        
    Returns:
        List of dictionaries containing file path, relative path, and size.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Raw data directory not found: {directory}")
    
    files = []
    for root, _, filenames in os.walk(dir_path):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, directory)
            size = os.path.getsize(full_path)
            files.append({
                "path": rel_path,
                "full_path": full_path,
                "size_bytes": size
            })
    
    logger.info(f"Scanned {len(files)} files in {directory}")
    return files

def generate_state_checksums(files: Optional[List[Dict[str, str]]] = None) -> Dict:
    """
    Generate checksums for a list of files.
    
    Args:
        files: List of file metadata dictionaries from scan_raw_data_directory.
               If None, scans the default raw data directory.
               
    Returns:
        Dictionary containing metadata and checksums for all files.
    """
    if files is None:
        files = scan_raw_data_directory()
    
    checksums = []
    for file_info in files:
        try:
            checksum = calculate_file_checksum(file_info["full_path"])
            checksums.append({
                "path": file_info["path"],
                "size_bytes": file_info["size_bytes"],
                "checksum": checksum,
                "algorithm": ALGORITHM
            })
            logger.debug(f"Checksum for {file_info['path']}: {checksum[:16]}...")
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_info['path']}: {e}")
            # Continue processing other files even if one fails
            continue
    
    state_data = {
        "generated_at": os.popen("date -Iseconds 2>/dev/null || date").read().strip(),
        "raw_data_directory": RAW_DATA_DIR,
        "algorithm": ALGORITHM,
        "total_files": len(checksums),
        "files": checksums
    }
    
    return state_data

def write_state_file(state_data: Dict, output_path: Optional[str] = None) -> str:
    """
    Write the state checksums to a YAML file.
    
    Args:
        state_data: Dictionary containing state information.
        output_path: Optional path for the output file. Defaults to STATE_FILE.
        
    Returns:
        Path to the written file.
    """
    if output_path is None:
        output_path = STATE_FILE
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        with open(output_path, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State file written to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to write state file to {output_path}: {e}")
        raise

def verify_state_checksums(state_path: Optional[str] = None) -> bool:
    """
    Verify current file checksums against a stored state file.
    
    Args:
        state_path: Path to the state YAML file. Defaults to STATE_FILE.
        
    Returns:
        True if all checksums match, False otherwise.
    """
    if state_path is None:
        state_path = STATE_FILE
    
    if not os.path.exists(state_path):
        logger.warning(f"State file not found: {state_path}")
        return False
    
    try:
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        return False
    
    if "files" not in state_data:
        logger.error("Invalid state file format: missing 'files' key")
        return False
    
    all_match = True
    for file_entry in state_data["files"]:
        file_path = os.path.join(state_data.get("raw_data_directory", RAW_DATA_DIR), file_entry["path"])
        
        if not os.path.exists(file_path):
            logger.warning(f"File missing during verification: {file_path}")
            all_match = False
            continue
        
        try:
            current_checksum = calculate_file_checksum(file_path)
            if current_checksum != file_entry["checksum"]:
                logger.error(f"Checksum mismatch for {file_entry['path']}")
                logger.error(f"  Expected: {file_entry['checksum']}")
                logger.error(f"  Found:    {current_checksum}")
                all_match = False
            else:
                logger.debug(f"Checksum verified: {file_entry['path']}")
        except Exception as e:
            logger.error(f"Error verifying checksum for {file_entry['path']}: {e}")
            all_match = False
    
    return all_match

def main():
    """
    Main entry point for the state manager script.
    Generates or updates the checksums file for raw data.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        logger.info("Starting state manager: generating checksums for raw data files.")
        
        # Scan raw data directory
        files = scan_raw_data_directory()
        
        if not files:
            logger.warning("No files found in raw data directory. Creating empty state.")
            state_data = {
                "generated_at": os.popen("date -Iseconds 2>/dev/null || date").read().strip(),
                "raw_data_directory": RAW_DATA_DIR,
                "algorithm": ALGORITHM,
                "total_files": 0,
                "files": []
            }
        else:
            # Generate checksums
            state_data = generate_state_checksums(files)
        
        # Write state file
        write_state_file(state_data)
        
        logger.info("State manager completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"State manager failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

import os
import hashlib
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file to ensure data integrity.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal checksum string
    """
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum calculation: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise

def scan_raw_data_directory(raw_data_dir: str) -> list:
    """
    Scan the raw data directory for files and return their paths.
    
    Args:
        raw_data_dir: Path to the raw data directory
        
    Returns:
        List of file paths
    """
    raw_path = Path(raw_data_dir)
    if not raw_path.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return []
    
    files = []
    for file_path in raw_path.rglob("*"):
        if file_path.is_file():
            files.append(str(file_path))
    
    return files

def generate_state_checksums(state_dir: str, raw_data_dir: str) -> dict:
    """
    Generate or update the state YAML file with checksums for all raw data files.
    
    This implements Constitution Principle III: Data integrity tracking.
    
    Args:
        state_dir: Directory where the state file will be written
        raw_data_dir: Directory containing raw data files
        
    Returns:
        Dictionary containing the state information
    """
    # Ensure state directory exists
    os.makedirs(state_dir, exist_ok=True)
    
    # Scan for raw data files
    data_files = scan_raw_data_directory(raw_data_dir)
    
    if not data_files:
        logger.warning("No raw data files found to checksum.")
        state = {
            "version": "1.0",
            "description": "Data integrity state file",
            "last_updated": None,
            "files": {}
        }
    else:
        logger.info(f"Calculating checksums for {len(data_files)} raw data files...")
        files_state = {}
        for file_path in data_files:
            try:
                checksum = calculate_file_checksum(file_path)
                relative_path = os.path.relpath(file_path, raw_data_dir)
                files_state[relative_path] = {
                    "checksum": checksum,
                    "algorithm": "sha256"
                }
                logger.debug(f"Checksum for {relative_path}: {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to checksum {file_path}: {e}")
                # Continue with other files even if one fails
        
        state = {
            "version": "1.0",
            "description": "Data integrity state file",
            "last_updated": None,  # Should be set by caller or main
            "files": files_state
        }
    
    return state

def write_state_file(state: dict, state_dir: str, filename: str = "data_state.yaml") -> str:
    """
    Write the state dictionary to a YAML file.
    
    Args:
        state: State dictionary to write
        state_dir: Directory to write the file to
        filename: Name of the state file
        
    Returns:
        Path to the written file
    """
    os.makedirs(state_dir, exist_ok=True)
    state_path = os.path.join(state_dir, filename)
    
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"State file written to: {state_path}")
    return state_path

def verify_state_checksums(state_dir: str, raw_data_dir: str, state_filename: str = "data_state.yaml") -> bool:
    """
    Verify that current file checksums match the stored state.
    
    Args:
        state_dir: Directory containing the state file
        raw_data_dir: Directory containing raw data files
        state_filename: Name of the state file
        
    Returns:
        True if all checksums match, False otherwise
    """
    state_path = os.path.join(state_dir, state_filename)
    if not os.path.exists(state_path):
        logger.error(f"State file not found: {state_path}")
        return False
    
    with open(state_path, "r") as f:
        state = yaml.safe_load(f)
    
    stored_files = state.get("files", {})
    if not stored_files:
        logger.warning("No files recorded in state file to verify.")
        return True
    
    all_match = True
    for relative_path, file_info in stored_files.items():
        full_path = os.path.join(raw_data_dir, relative_path)
        if not os.path.exists(full_path):
            logger.error(f"File missing during verification: {full_path}")
            all_match = False
            continue
        
        current_checksum = calculate_file_checksum(full_path)
        stored_checksum = file_info.get("checksum")
        stored_algorithm = file_info.get("algorithm", "sha256")
        
        if current_checksum != stored_checksum:
            logger.error(f"Checksum mismatch for {relative_path}: "
                       f"expected {stored_checksum[:16]}..., got {current_checksum[:16]}...")
            all_match = False
        else:
            logger.debug(f"Checksum verified for {relative_path}")
    
    return all_match

def main():
    """
    Main entry point for generating/updating the state file with raw data checksums.
    """
    import argparse
    import datetime

    parser = argparse.ArgumentParser(description="Generate/update state file with raw data checksums")
    parser.add_argument("--state-dir", default="state", help="Directory for state file")
    parser.add_argument("--raw-data-dir", default="data/raw", help="Directory containing raw data files")
    parser.add_argument("--filename", default="data_state.yaml", help="Name of the state file")
    parser.add_argument("--verify", action="store_true", help="Verify checksums instead of generating")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if args.verify:
        logger.info("Verifying data checksums...")
        if verify_state_checksums(args.state_dir, args.raw_data_dir, args.filename):
            logger.info("All checksums verified successfully.")
            return 0
        else:
            logger.error("Checksum verification failed. Data integrity compromised.")
            return 1
    else:
        logger.info("Generating data state checksums...")
        state = generate_state_checksums(args.state_dir, args.raw_data_dir)
        state["last_updated"] = datetime.datetime.now().isoformat()
        state_path = write_state_file(state, args.state_dir, args.filename)
        logger.info(f"State file generated successfully at {state_path}")
        return 0

if __name__ == "__main__":
    exit(main())

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directories(base_path: Optional[Path] = None) -> Path:
    """
    Create the standard data directory structure for the project.
    
    Args:
        base_path: Optional base path. Defaults to the project root 'data/'.
        
    Returns:
        Path to the created data directory.
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent / "data"
    
    subdirs = [
        "generated",
        "models",
        "simulation",
        "analysis"
    ]
    
    logger.info(f"Creating data directories under: {base_path}")
    base_path.mkdir(parents=True, exist_ok=True)
    
    for subdir in subdirs:
        subdir_path = base_path / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"  Created: {subdir_path}")
    
    return base_path

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hex digest string of the checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def record_checksums(data_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Scan the data directory and record checksums for all files.
    
    Args:
        data_root: Optional root path. Defaults to 'data/'.
        
    Returns:
        Dictionary mapping relative file paths to their checksums and metadata.
    """
    if data_root is None:
        data_root = Path(__file__).parent.parent / "data"
    
    if not data_root.exists():
        logger.warning(f"Data root does not exist: {data_root}. Creating it first.")
        create_directories(data_root)
    
    checksums: Dict[str, Any] = {
        "root": str(data_root),
        "files": {}
    }
    
    for root, _, files in os.walk(data_root):
        for filename in files:
            # Skip the checksum file itself to avoid circular dependency
            if filename == "checksums.json":
                continue
            
            file_path = Path(root) / filename
            rel_path = file_path.relative_to(data_root)
            
            try:
                checksum = compute_file_checksum(file_path)
                file_stat = file_path.stat()
                
                checksums["files"][str(rel_path)] = {
                    "checksum": checksum,
                    "size_bytes": file_stat.st_size,
                    "modified_time": file_stat.st_mtime
                }
                logger.debug(f"Checksummed: {rel_path} -> {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to checksum {file_path}: {e}")
    
    return checksums

def save_checksums(checksums: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the checksum record to a JSON file.
    
    Args:
        checksums: The checksum dictionary.
        output_path: Optional output path. Defaults to 'data/checksums.json'.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        data_root = Path(__file__).parent.parent / "data"
        output_path = data_root / "checksums.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
    
    logger.info(f"Saved checksums to: {output_path}")
    return output_path

def load_checksums(input_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the checksum record from a JSON file.
    
    Args:
        input_path: Optional input path. Defaults to 'data/checksums.json'.
        
    Returns:
        The loaded checksum dictionary.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        input_path = Path(__file__).parent.parent / "data" / "checksums.json"
    
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_integrity(data_root: Optional[Path] = None, 
                     checksum_path: Optional[Path] = None) -> bool:
    """
    Verify the integrity of all files in the data directory against stored checksums.
    
    Args:
        data_root: Optional root path. Defaults to 'data/'.
        checksum_path: Optional path to checksums.json. Defaults to 'data/checksums.json'.
        
    Returns:
        True if all files match, False otherwise.
    """
    if data_root is None:
        data_root = Path(__file__).parent.parent / "data"
    
    if checksum_path is None:
        checksum_path = data_root / "checksums.json"
    
    if not checksum_path.exists():
        logger.error(f"Checksum file not found: {checksum_path}")
        return False
    
    if not data_root.exists():
        logger.error(f"Data root not found: {data_root}")
        return False
    
    try:
        stored_checksums = load_checksums(checksum_path)
    except Exception as e:
        logger.error(f"Failed to load checksums: {e}")
        return False
    
    all_valid = True
    recorded_files = stored_checksums.get("files", {})
    
    # Check files that are recorded
    for rel_path_str, record in recorded_files.items():
        file_path = data_root / rel_path_str
        
        if not file_path.exists():
            logger.warning(f"Missing file: {rel_path_str}")
            all_valid = False
            continue
        
        try:
            current_checksum = compute_file_checksum(file_path)
            if current_checksum != record["checksum"]:
                logger.error(f"Checksum mismatch: {rel_path_str}")
                logger.error(f"  Expected: {record['checksum']}")
                logger.error(f"  Got:      {current_checksum}")
                all_valid = False
            else:
                logger.debug(f"Verified: {rel_path_str}")
        except Exception as e:
            logger.error(f"Error verifying {rel_path_str}: {e}")
            all_valid = False
    
    # Check for new files not in the record (optional strict mode could flag this)
    current_files = set()
    for root, _, files in os.walk(data_root):
        for filename in files:
            if filename == "checksums.json":
                continue
            file_path = Path(root) / filename
            rel_path = str(file_path.relative_to(data_root))
            current_files.add(rel_path)
    
    recorded_files_set = set(recorded_files.keys())
    new_files = current_files - recorded_files_set
    
    if new_files:
        logger.warning(f"New files found since last checksum (not verified): {new_files}")
        # Depending on policy, this might be an error. For now, just warn.
    
    if all_valid:
        logger.info("Integrity check PASSED.")
    else:
        logger.error("Integrity check FAILED.")
    
    return all_valid

def main() -> None:
    """
    Main entry point for the script.
    
    Usage:
        python setup_data_directories.py [--create] [--checksum] [--verify]
    
    If no arguments provided, it performs create -> checksum -> verify.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup and manage data directory checksums.")
    parser.add_argument("--create", action="store_true", help="Create directories.")
    parser.add_argument("--checksum", action="store_true", help="Compute and save checksums.")
    parser.add_argument("--verify", action="store_true", help="Verify integrity against checksums.")
    
    args = parser.parse_args()
    
    # Default behavior if no flags are set: do everything
    if not (args.create or args.checksum or args.verify):
        args.create = True
        args.checksum = True
        args.verify = True
    
    data_root = Path(__file__).parent.parent / "data"
    
    if args.create:
        logger.info("Step 1: Creating directories...")
        create_directories(data_root)
    
    if args.checksum:
        logger.info("Step 2: Recording checksums...")
        # Ensure directories exist first if we didn't create them
        if not data_root.exists():
            create_directories(data_root)
        
        checksums = record_checksums(data_root)
        save_checksums(checksums, data_root / "checksums.json")
    
    if args.verify:
        logger.info("Step 3: Verifying integrity...")
        if not data_root.exists():
            logger.error("Data root does not exist. Cannot verify.")
            return
        
        if not (data_root / "checksums.json").exists():
            logger.error("Checksum file does not exist. Run with --checksum first.")
            return
        
        success = verify_integrity(data_root)
        if not success:
            logger.error("Verification failed. Exiting with error code 1.")
            exit(1)
    
    logger.info("Data directory setup and checksum management completed successfully.")

if __name__ == "__main__":
    main()
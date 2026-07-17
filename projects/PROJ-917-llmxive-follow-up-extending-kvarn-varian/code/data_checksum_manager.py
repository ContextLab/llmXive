import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the data directory structure to be created
DATA_STRUCTURE = [
    "data/generated",
    "data/models",
    "data/simulation",
    "data/analysis",
    "data/raw"  # For immutable raw data if needed
]

def create_directories(root_dir: Optional[str] = None) -> Path:
    """
    Creates the required data directory structure.
    
    Args:
        root_dir: Optional root directory. Defaults to current working directory.
        
    Returns:
        Path to the root data directory.
    """
    if root_dir is None:
        root_dir = Path.cwd()
    
    root_path = Path(root_dir)
    data_path = root_path / "data"
    
    # Ensure root data directory exists
    data_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    for subdir in DATA_STRUCTURE:
        dir_path = data_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
        
    # Create .gitkeep files to ensure directories are tracked in git
    for subdir in DATA_STRUCTURE:
        keep_file = data_path / subdir / ".gitkeep"
        if not keep_file.exists():
            keep_file.write_text("# Keep this directory in git\n")
            
    logger.info(f"Data directory structure created at: {data_path}")
    return data_path

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Computes the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hex digest of the file checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def record_checksums(data_dir: Path, relative_paths: Optional[List[Path]] = None) -> List[Dict[str, Any]]:
    """
    Records checksums for files in the data directory.
    
    Args:
        data_dir: Path to the data directory.
        relative_paths: Optional list of relative paths to checksum. 
                       If None, checksums all files recursively.
                       
    Returns:
        List of dictionaries containing file path, checksum, and metadata.
    """
    checksums = []
    
    if relative_paths:
        files_to_process = [data_dir / p for p in relative_paths]
    else:
        # Get all files recursively, excluding .gitkeep
        files_to_process = [
            f for f in data_dir.rglob('*') 
            if f.is_file() and f.name != '.gitkeep'
        ]
    
    for file_path in files_to_process:
        try:
            checksum = compute_file_checksum(file_path)
            relative_path = file_path.relative_to(data_dir)
            checksums.append({
                "path": str(relative_path),
                "checksum": checksum,
                "algorithm": "sha256",
                "size_bytes": file_path.stat().st_size,
                "recorded_at": os.popen('date -Iseconds').read().strip()
            })
            logger.debug(f"Recorded checksum for: {relative_path}")
        except Exception as e:
            logger.warning(f"Skipping file {file_path}: {e}")
            
    return checksums

def save_checksums(checksums: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves checksums to a JSON file.
    
    Args:
        checksums: List of checksum dictionaries.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "version": "1.0",
        "created_at": os.popen('date -Iseconds').read().strip(),
        "checksums": checksums
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    logger.info(f"Saved {len(checksums)} checksums to {output_path}")

def load_checksums(checksum_path: Path) -> List[Dict[str, Any]]:
    """
    Loads checksums from a JSON file.
    
    Args:
        checksum_path: Path to the checksum JSON file.
        
    Returns:
        List of checksum dictionaries.
        
    Raises:
        FileNotFoundError: If the checksum file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")
        
    with open(checksum_path, 'r') as f:
        data = json.load(f)
        
    return data.get("checksums", [])

def verify_integrity(data_dir: Path, checksum_path: Path) -> Dict[str, Any]:
    """
    Verifies the integrity of data files against recorded checksums.
    
    Args:
        data_dir: Path to the data directory.
        checksum_path: Path to the checksum JSON file.
        
    Returns:
        Dictionary with verification results.
    """
    if not checksum_path.exists():
        return {
            "status": "error",
            "message": f"Checksum file not found: {checksum_path}"
        }
        
    recorded_checksums = load_checksums(checksum_path)
    results = {
        "status": "success",
        "verified": 0,
        "failed": 0,
        "missing": 0,
        "details": []
    }
    
    for record in recorded_checksums:
        file_path = data_dir / record["path"]
        
        if not file_path.exists():
            results["missing"] += 1
            results["details"].append({
                "path": record["path"],
                "status": "missing"
            })
            logger.warning(f"Missing file: {file_path}")
            continue
            
        try:
            current_checksum = compute_file_checksum(file_path, record["algorithm"])
            
            if current_checksum == record["checksum"]:
                results["verified"] += 1
                results["details"].append({
                    "path": record["path"],
                    "status": "verified"
                })
            else:
                results["failed"] += 1
                results["details"].append({
                    "path": record["path"],
                    "status": "mismatch",
                    "expected": record["checksum"],
                    "actual": current_checksum
                })
                logger.error(f"Checksum mismatch for {file_path}")
        except Exception as e:
            results["failed"] += 1
            results["details"].append({
                "path": record["path"],
                "status": "error",
                "error": str(e)
            })
            
    if results["failed"] > 0 or results["missing"] > 0:
        results["status"] = "failed"
        
    return results

def main():
    """
    Main function to demonstrate checksum management.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Checksum Manager")
    parser.add_argument(
        "command", 
        choices=["create", "record", "verify"],
        help="Command to execute"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Root directory for data (default: current directory)"
    )
    parser.add_argument(
        "--checksum-file",
        type=str,
        default="data/checksums.json",
        help="Path to checksum file (default: data/checksums.json)"
    )
    
    args = parser.parse_args()
    data_root = Path(args.data_dir) if args.data_dir else Path.cwd()
    data_dir = data_root / "data"
    
    if args.command == "create":
        logger.info("Creating data directory structure...")
        create_directories(str(data_root))
        logger.info("Directory structure created successfully.")
        
    elif args.command == "record":
        if not data_dir.exists():
            logger.error(f"Data directory not found: {data_dir}")
            return 1
            
        logger.info(f"Recording checksums for {data_dir}...")
        checksums = record_checksums(data_dir)
        output_path = data_root / args.checksum_file
        save_checksums(checksums, output_path)
        logger.info(f"Checksums recorded to {output_path}")
        
    elif args.command == "verify":
        output_path = data_root / args.checksum_file
        if not output_path.exists():
            logger.error(f"Checksum file not found: {output_path}")
            return 1
            
        logger.info(f"Verifying integrity against {output_path}...")
        results = verify_integrity(data_dir, output_path)
        
        if results["status"] == "success":
            logger.info(f"Verification successful: {results['verified']} files verified")
        else:
            logger.error(f"Verification failed: {results['failed']} failed, {results['missing']} missing")
            
        return 0 if results["status"] == "success" else 1
        
    return 0

if __name__ == "__main__":
    exit(main())

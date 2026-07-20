import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the data directory structure to create
DATA_DIRS = [
    "generated",
    "models",
    "simulation",
    "analysis"
]
DATA_ROOT = Path("data")

def create_directories(base_path: Optional[Path] = None) -> List[Path]:
    """
    Creates the required data directory structure.
    
    Args:
        base_path: Optional base path. Defaults to project root.
        
    Returns:
        List of created directory paths.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    root_dir = base_path / DATA_ROOT
    created_dirs = []
    
    # Create root data directory if it doesn't exist
    root_dir.mkdir(parents=True, exist_ok=True)
    created_dirs.append(root_dir)
    
    # Create subdirectories
    for subdir in DATA_DIRS:
        dir_path = root_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(dir_path)
        logger.info(f"Created directory: {dir_path}")
        
    return created_dirs

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Computes the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal string of the checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is a directory.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise ValueError(f"Cannot compute checksum for directory: {file_path}")
        
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
            
    return hasher.hexdigest()

def record_checksums(data_root: Optional[Path] = None, recursive: bool = True) -> Dict[str, Any]:
    """
    Scans the data directory and records checksums for all files.
    
    Args:
        data_root: Optional base path. Defaults to project root/data.
        recursive: Whether to scan subdirectories recursively.
        
    Returns:
        Dictionary containing checksum records and metadata.
    """
    if data_root is None:
        data_root = Path.cwd() / DATA_ROOT
        
    if not data_root.exists():
        raise FileNotFoundError(f"Data root directory not found: {data_root}")
        
    checksums = []
    total_files = 0
    
    if recursive:
        file_iterator = data_root.rglob('*')
    else:
        file_iterator = data_root.glob('*')
        
    for file_path in file_iterator:
        if file_path.is_file():
            try:
                relative_path = file_path.relative_to(data_root)
                checksum = compute_file_checksum(file_path)
                file_size = file_path.stat().st_size
                file_mtime = file_path.stat().st_mtime
                
                record = {
                    "path": str(relative_path),
                    "checksum": checksum,
                    "size_bytes": file_size,
                    "modified_at": file_mtime
                }
                checksums.append(record)
                total_files += 1
                logger.debug(f"Recorded checksum for: {relative_path}")
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                
    result = {
        "root": str(data_root),
        "recursive": recursive,
        "total_files": total_files,
        "files": checksums
    }
    
    logger.info(f"Recorded checksums for {total_files} files in {data_root}")
    return result

def save_checksums(checksum_data: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Saves checksum data to a JSON file.
    
    Args:
        checksum_data: Dictionary containing checksum records.
        output_path: Optional output path. Defaults to data/checksums.json.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = Path.cwd() / DATA_ROOT / "checksums.json"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksum_data, f, indent=2)
        
    logger.info(f"Checksums saved to: {output_path}")
    return output_path

def load_checksums(input_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads checksum data from a JSON file.
    
    Args:
        input_path: Optional input path. Defaults to data/checksums.json.
        
    Returns:
        Dictionary containing checksum records.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        input_path = Path.cwd() / DATA_ROOT / "checksums.json"
        
    if not input_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {input_path}")
        
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_integrity(data_root: Optional[Path] = None, checksums_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Verifies the integrity of files in the data directory against stored checksums.
    
    Args:
        data_root: Optional base path. Defaults to project root/data.
        checksums_path: Optional path to checksums file. Defaults to data/checksums.json.
        
    Returns:
        Dictionary containing verification results.
    """
    if data_root is None:
        data_root = Path.cwd() / DATA_ROOT
    if checksums_path is None:
        checksums_path = data_root / "checksums.json"
        
    if not data_root.exists():
        return {"status": "error", "message": f"Data root not found: {data_root}"}
        
    try:
        stored_data = load_checksums(checksums_path)
    except FileNotFoundError:
        return {"status": "error", "message": f"Checksum file not found: {checksums_path}"}
    except json.JSONDecodeError:
        return {"status": "error", "message": f"Invalid JSON in checksum file: {checksums_path}"}
        
    results = {
        "status": "success",
        "verified": 0,
        "failed": 0,
        "missing": 0,
        "new_files": 0,
        "details": []
    }
    
    # Create a map of stored checksums for quick lookup
    stored_map = {item["path"]: item["checksum"] for item in stored_data.get("files", [])}
    current_files = set()
    
    for file_path in data_root.rglob('*'):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(data_root))
            current_files.add(relative_path)
            
            if relative_path in stored_map:
                try:
                    current_checksum = compute_file_checksum(file_path)
                    if current_checksum == stored_map[relative_path]:
                        results["verified"] += 1
                        results["details"].append({"path": relative_path, "status": "valid"})
                    else:
                        results["failed"] += 1
                        results["details"].append({
                            "path": relative_path,
                            "status": "mismatch",
                            "expected": stored_map[relative_path],
                            "actual": current_checksum
                        })
                        logger.warning(f"Checksum mismatch for {relative_path}")
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({"path": relative_path, "status": "error", "error": str(e)})
                    logger.error(f"Error verifying {relative_path}: {e}")
            else:
                results["new_files"] += 1
                results["details"].append({"path": relative_path, "status": "new"})
                
    # Check for missing files
    for stored_path in stored_map:
        if stored_path not in current_files:
            results["missing"] += 1
            results["details"].append({"path": stored_path, "status": "missing"})
            logger.warning(f"Missing file: {stored_path}")
            
    if results["failed"] > 0 or results["missing"] > 0:
        results["status"] = "warning"
        
    logger.info(f"Integrity verification complete: {results['verified']} valid, {results['failed']} failed, {results['missing']} missing, {results['new_files']} new")
    return results

def main():
    """
    Main entry point for the checksum manager script.
    
    This function:
    1. Creates the data directory structure if it doesn't exist.
    2. Records checksums for all files in the data directory.
    3. Saves the checksums to a JSON file.
    4. Verifies the integrity of the data directory.
    """
    logger.info("Starting Data Checksum Manager")
    
    # Step 1: Create directories
    logger.info("Creating data directory structure...")
    created_dirs = create_directories()
    logger.info(f"Created {len(created_dirs)} directories")
    
    # Step 2: Record checksums
    logger.info("Recording checksums...")
    try:
        checksum_data = record_checksums()
        
        # Step 3: Save checksums
        logger.info("Saving checksums...")
        saved_path = save_checksums(checksum_data)
        logger.info(f"Checksums saved to: {saved_path}")
        
        # Step 4: Verify integrity
        logger.info("Verifying integrity...")
        verification_result = verify_integrity()
        
        if verification_result["status"] == "success":
            logger.info("Integrity verification passed")
        else:
            logger.warning(f"Integrity verification result: {verification_result['status']}")
            logger.warning(f"Verified: {verification_result['verified']}, Failed: {verification_result['failed']}, Missing: {verification_result['missing']}, New: {verification_result['new_files']}")
            
        # Print summary
        print("\n=== Data Checksum Summary ===")
        print(f"Total files processed: {checksum_data['total_files']}")
        print(f"Checksums saved to: {saved_path}")
        print(f"Verification status: {verification_result['status']}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 1
        
    logger.info("Data Checksum Manager completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())

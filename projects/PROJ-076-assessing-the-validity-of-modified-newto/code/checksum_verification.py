import os
import logging
import hashlib
import yaml
from pathlib import Path
from datetime import datetime

from utils import get_logger, log_stage

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_sparc_data_integrity(data_dir: Path, expected_checksums: dict = None) -> dict:
    """
    Verify integrity of downloaded SPARC data files.
    
    Args:
        data_dir: Path to directory containing downloaded SPARC data
        expected_checksums: Optional dict of filename -> expected checksum
        
    Returns:
        dict with verification results including checksums and status
    """
    logger = get_logger(__name__)
    results = {
        "verified_at": datetime.utcnow().isoformat(),
        "files": {},
        "all_passed": True
    }
    
    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        results["all_passed"] = False
        return results
    
    # Find all data files (zip, txt, etc.)
    data_files = list(data_dir.glob("*"))
    
    if not data_files:
        logger.warning(f"No files found in {data_dir}")
        results["all_passed"] = False
        return results
    
    for file_path in data_files:
        if file_path.is_file():
            try:
                checksum = calculate_sha256(file_path)
                status = "verified"
                
                if expected_checksums and file_path.name in expected_checksums:
                    if checksum != expected_checksums[file_path.name]:
                        status = "mismatch"
                        results["all_passed"] = False
                        logger.error(f"Checksum mismatch for {file_path.name}")
                
                results["files"][file_path.name] = {
                    "checksum": checksum,
                    "size_bytes": file_path.stat().st_size,
                    "status": status
                }
                
                logger.info(f"Verified {file_path.name}: {checksum[:16]}...")
                
            except Exception as e:
                logger.error(f"Failed to verify {file_path.name}: {e}")
                results["files"][file_path.name] = {
                    "error": str(e),
                    "status": "failed"
                }
                results["all_passed"] = False
    
    return results

def update_metadata_with_verification(metadata_path: Path, verification_results: dict) -> None:
    """Update metadata.yaml with verification results."""
    logger = get_logger(__name__)
    
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        return
    
    with open(metadata_path, "r") as f:
        metadata = yaml.safe_load(f)
    
    # Update data section with verification info
    if "data" not in metadata:
        metadata["data"] = {}
    
    metadata["data"]["verification"] = {
        "verified_at": verification_results["verified_at"],
        "all_passed": verification_results["all_passed"],
        "files": verification_results["files"]
    }
    
    # Update timestamp
    metadata["data"]["last_verified"] = datetime.utcnow().isoformat()
    
    # Write back
    with open(metadata_path, "w") as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated metadata at {metadata_path}")

def main():
    """Main entry point for checksum verification."""
    logger = get_logger(__name__)
    log_stage(logger, "T016: Checksum Verification")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "raw"
    metadata_path = project_root / "data" / "metadata.yaml"
    
    logger.info(f"Scanning data directory: {data_dir}")
    
    # Verify data integrity
    verification_results = verify_sparc_data_integrity(data_dir)
    
    # Update metadata
    update_metadata_with_verification(metadata_path, verification_results)
    
    if verification_results["all_passed"]:
        logger.info("All data files verified successfully.")
        return 0
    else:
        logger.error("Data verification failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    exit(main())

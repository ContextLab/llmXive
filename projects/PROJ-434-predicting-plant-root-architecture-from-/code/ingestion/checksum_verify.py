import os
import sys
import hashlib
import logging
from pathlib import Path
from datetime import datetime

# Ensure ingestion is in path if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_checksum(csv_path: Path, checksum_path: Path) -> bool:
    """
    Verify that the current file hash matches the stored checksum.
    
    Returns True if verification passes, False otherwise.
    Raises FileNotFoundError if either file is missing.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")
    
    # Read stored checksum (first 64 characters, ignoring whitespace)
    with open(checksum_path, "r", encoding="utf-8") as f:
        stored_hash = f.read().strip().split()[0] if f.read().strip() else ""
    
    # Recompute hash
    current_hash = compute_sha256(csv_path)
    
    return current_hash == stored_hash

def main():
    """
    Main entry point for checksum verification task T012b.
    Reads data/processed/soil_extracted.csv.sha256 and verifies against
    data/processed/soil_extracted.csv. Logs result to data/logs/checksum_verification.log.
    """
    # Setup logging
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "checksum_verification.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    csv_path = base_dir / "data" / "processed" / "soil_extracted.csv"
    checksum_path = base_dir / "data" / "processed" / "soil_extracted.csv.sha256"
    
    logger.info("Starting checksum verification for T012b")
    logger.info(f"Target file: {csv_path}")
    logger.info(f"Checksum file: {checksum_path}")
    
    try:
        # Check if files exist
        if not csv_path.exists():
            logger.error(f"Target CSV file not found: {csv_path}")
            sys.exit(1)
        
        if not checksum_path.exists():
            logger.error(f"Checksum file not found: {checksum_path}")
            sys.exit(1)
        
        # Perform verification
        is_valid = verify_checksum(csv_path, checksum_path)
        
        timestamp = datetime.now().isoformat()
        
        if is_valid:
            logger.info("CHECKSUM VERIFICATION PASSED")
            logger.info(f"  Timestamp: {timestamp}")
            logger.info(f"  File: {csv_path.name}")
            logger.info(f"  Status: MATCH")
            logger.info("  The current file hash matches the stored checksum.")
            sys.exit(0)
        else:
            logger.error("CHECKSUM VERIFICATION FAILED")
            logger.error(f"  Timestamp: {timestamp}")
            logger.error(f"  File: {csv_path.name}")
            logger.error("  Status: MISMATCH")
            logger.error("  The current file hash does NOT match the stored checksum.")
            logger.error("  Data integrity compromised. Aborting.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

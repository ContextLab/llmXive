import os
import sys
import hashlib
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Main entry point for saving raw data with checksum verification.
    
    This script expects the raw dataset to already exist at 
    data/raw/raw_dataset.csv (produced by T010 ingest.py).
    
    It performs:
    1. Verification that the input file exists
    2. Computation of SHA256 checksum
    3. Writing the checksum to a .sha256 file
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "raw" / "raw_dataset.csv"
    checksum_path = project_root / "data" / "raw" / "raw_dataset.csv.sha256"
    
    # Ensure input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("T010 (Data Fetch) must complete successfully before T014 can run.")
        sys.exit(1)
    
    logger.info(f"Processing file: {input_path}")
    
    try:
        # Load the dataset to verify it's valid
        df = pd.read_csv(input_path)
        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
        
        # Compute SHA256 checksum
        checksum = compute_sha256(str(input_path))
        logger.info(f"Computed SHA256 checksum: {checksum}")
        
        # Write checksum to file
        # Format: "<checksum>  <filename>" (standard sha256sum format)
        with open(checksum_path, 'w') as f:
            f.write(f"{checksum}  raw_dataset.csv\n")
        
        logger.info(f"Checksum saved to: {checksum_path}")
        logger.info("T014 Raw Data Save completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing raw data: {e}")
        # Clean up partial checksum file if it exists
        if checksum_path.exists():
            checksum_path.unlink()
        sys.exit(1)

if __name__ == "__main__":
    main()

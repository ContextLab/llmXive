import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Import from the checksum manager module
from data_checksum_manager import (
    create_directories, 
    compute_file_checksum, 
    record_checksums, 
    save_checksums, 
    load_checksums, 
    verify_integrity
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for setting up data directories with checksumming.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup data directories with checksumming for immutable raw data"
    )
    parser.add_argument(
        "--root-dir",
        type=str,
        default=None,
        help="Root directory for the project (default: current directory)"
    )
    parser.add_argument(
        "--record",
        action="store_true",
        help="Record checksums after creating directories"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify integrity of existing data"
    )
    
    args = parser.parse_args()
    root_dir = Path(args.root_dir) if args.root_dir else Path.cwd()
    
    logger.info(f"Setting up data directories at: {root_dir}")
    
    # Create the directory structure
    data_path = create_directories(str(root_dir))
    
    if args.verify:
        checksum_file = root_dir / "data" / "checksums.json"
        if checksum_file.exists():
            logger.info("Verifying data integrity...")
            results = verify_integrity(data_path, checksum_file)
            if results["status"] == "success":
                logger.info("Data integrity verified successfully.")
                return 0
            else:
                logger.error("Data integrity check failed.")
                return 1
        else:
            logger.warning("No checksum file found for verification.")
    elif args.record:
        logger.info("Recording checksums...")
        checksums = record_checksums(data_path)
        checksum_file = root_dir / "data" / "checksums.json"
        save_checksums(checksums, checksum_file)
        logger.info(f"Checksums saved to {checksum_file}")
        
    logger.info("Setup completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())

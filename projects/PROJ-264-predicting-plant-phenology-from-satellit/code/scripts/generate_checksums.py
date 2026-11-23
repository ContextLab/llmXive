"""
Script to generate and verify checksums for data directories.

Usage:
    python scripts/generate_checksums.py generate
    python scripts/generate_checksums.py verify
"""
import sys
from pathlib import Path
from src.data.checksums import generate_checksums_for_directories, verify_all_checksums
from src.lib.utils import setup_logging

logger = setup_logging(__name__)

def main() -> int:
    """
    Main entry point for the checksum script.
    
    Returns:
        0 on success, 1 on failure
    """
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_checksums.py <generate|verify>")
        return 1
    
    command = sys.argv[1]
    project_root = Path(__file__).parent.parent
    
    # Define data directories to process
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed"
    ]
    
    # Filter to only existing directories
    existing_dirs = [d for d in data_dirs if d.exists()]
    
    if not existing_dirs:
        logger.warning("No data directories found. Ensure data/raw and data/processed exist.")
        return 1
    
    if command == "generate":
        logger.info(f"Generating checksums for {len(existing_dirs)} directories")
        generate_checksums_for_directories(existing_dirs)
        logger.info("Checksum generation complete")
        return 0
        
    elif command == "verify":
        logger.info(f"Verifying checksums for {len(existing_dirs)} directories")
        success = verify_all_checksums(existing_dirs)
        if success:
            logger.info("All checksums verified successfully")
        else:
            logger.error("Checksum verification failed")
        return 0 if success else 1
        
    else:
        print(f"Unknown command: {command}")
        print("Usage: python scripts/generate_checksums.py <generate|verify>")
        return 1

if __name__ == "__main__":
    sys.exit(main())

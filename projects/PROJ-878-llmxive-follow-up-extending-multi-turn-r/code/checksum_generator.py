"""
Checksum generation for generated dataset.

This script generates SHA-256 checksums for the logical puzzles dataset
and records them in the checksums file.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_utils import configure_logging, generate_checksum, write_checksum_file

def main():
    """Generate checksums for the logical puzzles dataset."""
    # Configure logging
    logger = configure_logging(level=logging.INFO)
    
    # Define paths
    puzzles_file = project_root / "data" / "raw" / "logical_puzzles.jsonl"
    checksums_file = project_root / "data" / "checksums.txt"
    
    # Verify input file exists
    if not puzzles_file.exists():
        logger.error(f"Input file not found: {puzzles_file}")
        logger.error("Please run T016 (write_puzzles.py) first to generate the dataset.")
        sys.exit(1)
    
    logger.info(f"Generating checksum for: {puzzles_file}")
    
    # Generate checksum
    checksum = generate_checksum(puzzles_file)
    
    if checksum is None:
        logger.error("Failed to generate checksum.")
        sys.exit(1)
    
    logger.info(f"Checksum generated: {checksum}")
    
    # Write checksum to file
    write_checksum_file(checksums_file, "logical_puzzles.jsonl", checksum)
    
    logger.info(f"Checksum recorded in: {checksums_file}")
    logger.info("Checksum generation complete.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

import os
import sys
import logging
from pathlib import Path
from utils.logging_utils import configure_logging, generate_checksum, write_checksum_file

def main():
    """
    Generate checksums for the generated logical puzzles dataset.
    
    This script reads data/raw/logical_puzzles.jsonl, calculates its checksum,
    and writes the result to data/checksums.txt.
    """
    # Configure logging
    logger = configure_logging("checksum_generator")
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    checksum_file = data_dir / "checksums.txt"
    input_file = raw_dir / "logical_puzzles.jsonl"
    
    # Verify input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T016 (generate puzzles) has been completed first.")
        sys.exit(1)
    
    logger.info(f"Generating checksum for: {input_file}")
    
    try:
        # Generate checksum
        checksum = generate_checksum(input_file)
        
        # Write checksum to file
        write_checksum_file(checksum_file, input_file.name, checksum)
        
        logger.info(f"Checksum generated successfully: {checksum}")
        logger.info(f"Results written to: {checksum_file}")
        
    except Exception as e:
        logger.error(f"Failed to generate checksum: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

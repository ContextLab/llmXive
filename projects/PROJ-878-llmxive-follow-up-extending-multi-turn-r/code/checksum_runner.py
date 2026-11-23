"""
Checksum generation runner for T017.

Generates SHA-256 checksums for data/raw/logical_puzzles.jsonl
and records them in data/checksums.txt.

Usage:
    python code/checksum_runner.py
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_utils import generate_checksum, write_checksum_file

def main():
    """Generate checksums for the logical puzzles dataset."""
    # Configure logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)

    # Define paths relative to project root
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    checksums_file = data_dir / "checksums.txt"
    puzzles_file = raw_dir / "logical_puzzles.jsonl"

    # Verify input file exists
    if not puzzles_file.exists():
        logger.error(f"Input file not found: {puzzles_file}")
        logger.error("T016 must be completed to generate data/raw/logical_puzzles.jsonl first.")
        sys.exit(1)

    logger.info(f"Generating checksum for: {puzzles_file}")

    # Generate checksum
    checksum = generate_checksum(puzzles_file)
    
    if checksum is None:
        logger.error(f"Failed to generate checksum for: {puzzles_file}")
        sys.exit(1)

    logger.info(f"Checksum generated: {checksum}")

    # Write checksum file
    checksums_file.parent.mkdir(parents=True, exist_ok=True)
    write_checksum_file(checksums_file, [puzzles_file], {str(puzzles_file): checksum})

    logger.info(f"Checksum written to: {checksums_file}")
    logger.info("T017 completed successfully.")

if __name__ == "__main__":
    main()
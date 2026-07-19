"""
Task T028: Save cleaned full pool to data/processed/full_pool_final.csv with SHA-256 checksum generation.
Reads the final processed CSV, ensures it exists, computes its SHA-256 hash,
and writes the hash to a .sha256 sidecar file.
"""
import sys
from pathlib import Path

from utils.logging import get_logger
from utils.checksum_utils import generate_and_save_checksum


def main():
    logger = get_logger("checksum_pool")
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    input_file = project_root / "data" / "processed" / "full_pool_final.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run data_ingestion.py (T027) first to generate the full pool.")
        sys.exit(1)

    logger.info(f"Generating checksum for: {input_file}")
    
    # Generate and save checksum
    # generate_and_save_checksum expects a Path object for the file and the output path
    checksum_file = input_file.with_suffix(input_file.suffix + ".sha256")
    
    try:
        generate_and_save_checksum(input_file, checksum_file)
        logger.info(f"Checksum successfully written to: {checksum_file}")
    except Exception as e:
        logger.error(f"Failed to generate checksum: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

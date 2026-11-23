"""
Task T029: Generate checksums for execution logs.

Generates SHA-256 checksums for:
- data/processed/execution_log.csv
- data/processed/extended_budget_log.csv

Writes results to data/checksums.txt (appending to existing checksums).
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports from code/utils
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_utils import generate_checksum, write_checksum_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Generate checksums for execution log files."""
    data_dir = project_root / "data" / "processed"
    checksum_file = project_root / "data" / "checksums.txt"

    # Files to checksum
    files_to_checksum = [
        "execution_log.csv",
        "extended_budget_log.csv"
    ]

    # Verify files exist
    missing_files = []
    for filename in files_to_checksum:
        filepath = data_dir / filename
        if not filepath.exists():
            missing_files.append(str(filepath))

    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        sys.exit(1)

    # Generate checksums
    checksums = []
    for filename in files_to_checksum:
        filepath = data_dir / filename
        try:
            checksum = generate_checksum(filepath)
            relative_path = filepath.relative_to(project_root)
            checksums.append({
                "file": str(relative_path),
                "checksum": checksum
            })
            logger.info(f"Generated checksum for {relative_path}: {checksum}")
        except Exception as e:
            logger.error(f"Failed to generate checksum for {filepath}: {e}")
            sys.exit(1)

    # Write checksums to file
    if checksums:
        write_checksum_file(checksum_file, checksums, append=True)
        logger.info(f"Checksums written to {checksum_file}")
    else:
        logger.warning("No checksums generated")

    logger.info("T029 completed successfully")

if __name__ == "__main__":
    main()

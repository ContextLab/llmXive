"""
Script to generate checksums for all files in the data/ directory.
This script is the entry point for Task T006 to create artifacts/checksums.txt.
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path to import checksum_utils
sys.path.insert(0, str(Path(__file__).parent))

from checksum_utils import generate_checksums, logger

def main():
    """
    Main entry point to generate checksums for the data directory.
    """
    project_root = Path(__file__).parent.parent
    data_root = project_root / 'data'
    output_path = project_root / 'artifacts' / 'checksums.txt'

    # Ensure artifacts directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure data directory exists (if not, we might just generate empty or fail)
    if not data_root.exists():
        logger.warning(f"Data directory {data_root} does not exist. Generating empty checksum file.")
        output_path.write_text("")
        return

    try:
        generate_checksums(data_root, output_path)
        logging.info(f"Checksum generation complete. Output: {output_path}")
    except Exception as e:
        logging.error(f"Failed to generate checksums: {e}")
        sys.exit(1)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()

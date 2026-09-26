import logging
import sys
from pathlib import Path
from checksum_utils import generate_checksums, logger

def main():
    """
    CLI wrapper to generate checksums for the data directory.
    Ensures artifacts directory exists and writes checksums.txt.
    """
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    output_path = project_root / 'artifacts' / 'checksums.txt'

    # Ensure artifacts directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting checksum generation for {data_dir}")
    
    try:
        generate_checksums(data_dir, output_path)
        logger.info(f"Checksums successfully written to {output_path}")
    except FileNotFoundError as e:
        logger.error(f"Data directory not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during checksum generation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

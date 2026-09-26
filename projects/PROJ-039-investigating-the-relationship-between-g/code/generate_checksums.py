import logging
import sys
from pathlib import Path
from checksum_utils import generate_checksums, logger

def main():
    """
    Generate checksums for all files in the data directory.
    This script is the entry point for T006.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    checksum_file = project_root / 'artifacts' / 'checksums.txt'
    
    # Ensure artifacts directory exists
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting checksum generation for {data_dir}")
    logger.info(f"Output will be written to {checksum_file}")
    
    try:
        generate_checksums(str(data_dir), str(checksum_file))
        logger.info("Checksum generation completed successfully.")
    except Exception as e:
        logger.error(f"Checksum generation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

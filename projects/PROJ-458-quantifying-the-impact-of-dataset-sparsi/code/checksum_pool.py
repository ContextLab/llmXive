import sys
from pathlib import Path
from utils.logging import get_logger
from utils.checksum_utils import generate_and_save_checksum

def main():
    """
    T028: Save cleaned full pool to data/processed/full_pool_final.csv with SHA-256 checksum.
    
    This script expects `data/processed/full_pool_final.csv` to exist (produced by T027).
    It generates a SHA-256 checksum and writes it to `data/processed/full_pool_final.csv.sha256`.
    """
    logger = get_logger(__name__)
    
    input_path = Path("data/processed/full_pool_final.csv")
    checksum_path = Path("data/processed/full_pool_final.csv.sha256")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Task T027 (imputation) must be completed before T028.")
        sys.exit(1)
    
    logger.info(f"Generating SHA-256 checksum for {input_path}")
    generate_and_save_checksum(input_path, checksum_path)
    logger.info(f"Checksum saved to {checksum_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

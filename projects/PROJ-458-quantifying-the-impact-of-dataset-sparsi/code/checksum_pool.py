"""
T028: Save cleaned full pool to data/processed/full_pool_final.csv with SHA-256 checksum.

This script reads the final processed pool from data/processed/full_pool_final.csv,
computes its SHA-256 checksum, and writes the checksum to 
data/processed/full_pool_final.csv.sha256.

This implements Constitution III (Data Integrity via Checksums).
"""
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.checksum_utils import generate_and_save_checksum

logger = get_logger(__name__)


def main():
    """Main entry point for T028 checksum generation."""
    # Define paths relative to project root
    input_file = project_root / "data" / "processed" / "full_pool_final.csv"
    
    # Check if input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T027 (imputation logic) has completed successfully.")
        sys.exit(1)
    
    logger.info(f"Generating checksum for: {input_file}")
    logger.info(f"File size: {input_file.stat().st_size / (1024*1024):.2f} MB")
    
    try:
        checksum = generate_and_save_checksum(input_file)
        
        checksum_file = input_file.with_suffix(input_file.suffix + ".sha256")
        logger.info(f"SUCCESS: Checksum generated and saved to {checksum_file}")
        logger.info(f"Checksum value: {checksum}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

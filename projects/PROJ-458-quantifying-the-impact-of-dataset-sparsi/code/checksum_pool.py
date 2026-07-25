import sys
from pathlib import Path
from utils.logging import get_logger
from utils.checksum_utils import generate_and_save_checksum

def main():
    """
    T028 Implementation: Save cleaned full pool to data/processed/full_pool_final.csv
    with SHA-256 checksum generation (write to data/processed/full_pool_final.csv.sha256).
    
    This task assumes T027 has already produced the final CSV file.
    It verifies the file exists, computes its checksum, and writes the checksum file.
    """
    logger = get_logger(__name__)
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "full_pool_final.csv"
    checksum_file = project_root / "data" / "processed" / "full_pool_final.csv.sha256"
    
    # Verify input file exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("T027 (imputation) must be completed before running T028.")
        sys.exit(1)
    
    logger.info(f"Found input file: {input_file} ({input_file.stat().st_size} bytes)")
    
    # Generate and save checksum
    try:
        generate_and_save_checksum(input_file, checksum_file)
        logger.info(f"Checksum generated and saved to: {checksum_file}")
        
        # Read and log the checksum for verification
        with open(checksum_file, 'r') as f:
            checksum_content = f.read().strip()
        logger.info(f"SHA-256: {checksum_content}")
        
        return 0
    except Exception as e:
        logger.error(f"Failed to generate checksum: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

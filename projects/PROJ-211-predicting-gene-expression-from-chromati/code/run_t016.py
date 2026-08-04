import os
import sys
import logging
import subprocess
from utils import checksum_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/run_t016.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Execute T016: Define housekeeping and cell-type-specific genes.
    
    This script:
    1. Runs preprocess.py to generate housekeeping_genes.csv and cell_type_specific_genes.csv
    2. Computes checksums for the output files
    3. Logs the checksums
    """
    logger.info("Starting T016 execution script")
    
    # Define paths
    input_file = "data/processed/imputed_expression.csv"
    output_housekeeping = "data/processed/housekeeping_genes.csv"
    output_cell_type = "data/processed/cell_type_specific_genes.csv"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T014 has been completed and imputed_expression.csv exists.")
        sys.exit(1)
    
    # Run preprocess.py to generate housekeeping and cell-type-specific genes
    cmd = [
        "python", "code/preprocess.py",
        "--input", input_file,
        "--output-housekeeping", output_housekeeping,
        "--output-cell-type", output_cell_type,
        "--cv-threshold-hk", "0.2",
        "--cv-threshold-ct", "0.5"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Preprocessing failed with return code {result.returncode}")
        logger.error(f"STDOUT: {result.stdout}")
        logger.error(f"STDERR: {result.stderr}")
        sys.exit(1)
    
    logger.info("Preprocessing completed successfully")
    
    # Verify output files exist
    if not os.path.exists(output_housekeeping):
        logger.error(f"Output file not created: {output_housekeeping}")
        sys.exit(1)
    
    if not os.path.exists(output_cell_type):
        logger.error(f"Output file not created: {output_cell_type}")
        sys.exit(1)
    
    # Compute checksums
    logger.info("Computing checksums for output files")
    checksum_hk = checksum_file(output_housekeeping)
    checksum_ct = checksum_file(output_cell_type)
    
    logger.info(f"Housekeeping genes checksum: {checksum_hk}")
    logger.info(f"Cell-type-specific genes checksum: {checksum_ct}")
    
    # Log checksums to file
    checksum_log_path = "logs/checksums.txt"
    os.makedirs(os.path.dirname(checksum_log_path), exist_ok=True)
    
    with open(checksum_log_path, 'a') as f:
        f.write(f"T016_housekeeping_genes.csv: {checksum_hk}\n")
        f.write(f"T016_cell_type_specific_genes.csv: {checksum_ct}\n")
    
    logger.info(f"Checksums logged to {checksum_log_path}")
    logger.info("T016 execution completed successfully")

if __name__ == "__main__":
    main()

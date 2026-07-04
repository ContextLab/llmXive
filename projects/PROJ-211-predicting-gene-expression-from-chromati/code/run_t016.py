"""
Script to execute Task T016: Define housekeeping genes.

This script runs the housekeeping gene definition pipeline and generates checksums.
"""
import os
import sys
import logging
import subprocess
from utils import checksum_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/t016.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Execute T016 pipeline."""
    input_file = "data/processed/imputed_expression.csv"
    output_file = "data/processed/housekeeping_genes.csv"
    checksum_file_path = "logs/checksums.txt"
    
    # Ensure directories exist
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Check if input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run T014 first to generate imputed_expression.csv")
        sys.exit(1)
    
    logger.info(f"Starting T016: Define housekeeping genes")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    
    # Run the preprocessing script
    cmd = [
        sys.executable, "code/preprocess.py",
        "--input", input_file,
        "--output", output_file,
        "--n-genes", "500",
        "--cv-threshold", "0.2",
        "--gene-col", "gene_id"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("T016 preprocessing completed successfully")
        logger.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running preprocessing script: {e}")
        logger.error(f"stderr: {e.stderr}")
        sys.exit(1)
    
    # Generate checksum
    if os.path.exists(output_file):
        checksum = checksum_file(output_file)
        logger.info(f"Checksum for {output_file}: {checksum}")
        
        # Append to checksums log
        with open(checksum_file_path, "a") as f:
            f.write(f"{output_file}: {checksum}\n")
        logger.info(f"Checksum recorded in {checksum_file_path}")
    else:
        logger.error(f"Output file not created: {output_file}")
        sys.exit(1)
    
    logger.info("T016 completed successfully")

if __name__ == "__main__":
    main()

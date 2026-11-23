"""
Script to execute Task T016: Define housekeeping genes.

This script invokes the preprocess.py module to identify housekeeping genes
based on the coefficient of variation (CV) of gene expression across samples.

Input: data/processed/imputed_expression.csv
Output: data/processed/housekeeping_genes.csv
"""
import os
import sys
import logging
import subprocess
from utils import checksum_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    input_file = "data/processed/imputed_expression.csv"
    output_file = "data/processed/housekeeping_genes.csv"
    
    logger.info(f"Starting Task T016: Identifying housekeeping genes from {input_file}")
    
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} not found. Task T016 cannot proceed.")
        sys.exit(1)
    
    # Check for blocked marker
    blocked_marker = f"{input_file}.blocked"
    if os.path.exists(blocked_marker):
        logger.error(f"Input file {input_file} is blocked (marker exists). Task T016 cannot proceed.")
        sys.exit(1)

    try:
        # Run the preprocess module with the 'housekeeping' command
        cmd = [
            sys.executable, "code/preprocess.py", 
            "housekeeping",
            "--input", input_file,
            "--output", output_file
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr) # Warnings are okay, but log them

        if os.path.exists(output_file):
            checksum = checksum_file(output_file)
            logger.info(f"Task T016 completed successfully. Output: {output_file}, Checksum: {checksum}")
            
            # Optional: Record checksum in logs if needed, though task says record in state/...yaml
            # For now, we just log it. The main pipeline might handle state updates.
        else:
            logger.error(f"Output file {output_file} was not created despite successful exit code.")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        logger.error(f"Task T016 failed during execution: {e}")
        logger.error(f"stderr: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in T016 runner: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

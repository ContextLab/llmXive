"""
Wrapper script to execute the R-based preprocessing pipeline (preprocess.R).

This script handles:
1. Argument parsing for input raw data paths and output directory.
2. Validation of the R environment and dependencies.
3. Execution of preprocess.R via subprocess.
4. Verification of output .h5ad files.
5. Logging of success/failure.

Usage:
    python code/preprocess.py --input data/raw/ --output data/processed/
"""
import argparse
import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/preprocess.log')
    ]
)
logger = logging.getLogger(__name__)

def check_r_environment():
    """Verify that R and required packages are available."""
    logger.info("Checking R environment...")
    
    # Check if R is installed
    try:
        result = subprocess.run(
            ['R', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.error("R is not installed or not in PATH.")
            return False
        logger.info(f"R version found: {result.stdout.split(chr(10))[0]}")
    except FileNotFoundError:
        logger.error("R executable not found. Please install R.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("R version check timed out.")
        return False

    # Check for Seurat (via Rscript)
    try:
        result = subprocess.run(
            ['Rscript', '-e', 'if (!requireNamespace("Seurat", quietly = TRUE)) quit(status=1)'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            logger.error("Seurat package is not installed in R.")
            logger.error("stderr: " + result.stderr)
            return False
        logger.info("Seurat package found.")
    except FileNotFoundError:
        logger.error("Rscript executable not found.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Seurat check timed out.")
        return False

    # Check for reticulate (needed for Python-Anndata interop if used in R)
    try:
        result = subprocess.run(
            ['Rscript', '-e', 'if (!requireNamespace("reticulate", quietly = TRUE)) quit(status=1)'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            logger.warning("reticulate package not found. This may be required for some Anndata operations.")
            # Not strictly failing here as preprocess.R might not use it, but good to know
        else:
            logger.info("reticulate package found.")
    except FileNotFoundError:
        logger.error("Rscript executable not found.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("reticulate check timed out.")
        return False

    return True

def run_r_preprocessing(input_dir, output_dir, r_script_path):
    """Execute the R preprocessing script."""
    logger.info(f"Starting R preprocessing: Input={input_dir}, Output={output_dir}")
    
    # Validate paths
    if not os.path.isdir(input_dir):
        logger.error(f"Input directory does not exist: {input_dir}")
        return False

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Check if R script exists
    if not os.path.isfile(r_script_path):
        logger.error(f"R script not found: {r_script_path}")
        return False

    # Construct command
    cmd = [
        'Rscript',
        r_script_path,
        '--input', input_dir,
        '--output', output_dir
    ]

    logger.info(f"Executing command: {' '.join(cmd)}")

    try:
        # Run the R script
        process = subprocess.run(
            cmd,
            capture_output=False,  # Stream output to see progress
            text=True,
            timeout=3600  # 1 hour timeout for preprocessing
        )

        if process.returncode != 0:
            logger.error(f"R preprocessing script failed with return code {process.returncode}")
            return False

        logger.info("R preprocessing script completed successfully.")
        return True

    except subprocess.TimeoutExpired:
        logger.error("R preprocessing script timed out after 1 hour.")
        return False
    except Exception as e:
        logger.error(f"Error executing R script: {str(e)}")
        return False

def verify_outputs(output_dir, expected_extensions=['.h5ad']):
    """Verify that output files were created."""
    logger.info(f"Verifying outputs in {output_dir}...")
    
    output_files = list(Path(output_dir).rglob('*'))
    h5ad_files = [f for f in output_files if f.suffix in expected_extensions]
    
    if not h5ad_files:
        logger.error(f"No {expected_extensions} files found in {output_dir}")
        return False

    logger.info(f"Found {len(h5ad_files)} output files:")
    for f in h5ad_files:
        logger.info(f"  - {f}")
        if f.stat().st_size == 0:
            logger.error(f"Output file is empty: {f}")
            return False

    return True

def main():
    parser = argparse.ArgumentParser(description='Wrapper for R-based single-cell preprocessing')
    parser.add_argument('--input', type=str, required=True, help='Path to input directory containing raw data')
    parser.add_argument('--output', type=str, required=True, help='Path to output directory for processed .h5ad files')
    parser.add_argument('--script', type=str, default='code/preprocess.R', help='Path to the R preprocessing script')
    
    args = parser.parse_args()

    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)

    logger.info("=" * 60)
    logger.info("Starting Preprocessing Pipeline Wrapper")
    logger.info("=" * 60)

    # Step 1: Check R environment
    if not check_r_environment():
        logger.error("R environment check failed. Aborting.")
        sys.exit(1)

    # Step 2: Run R preprocessing
    if not run_r_preprocessing(args.input, args.output, args.script):
        logger.error("R preprocessing failed. Aborting.")
        sys.exit(1)

    # Step 3: Verify outputs
    if not verify_outputs(args.output):
        logger.error("Output verification failed. Aborting.")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Preprocessing Pipeline Completed Successfully")
    logger.info("=" * 60)

if __name__ == '__main__':
    main()

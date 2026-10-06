"""
Wrapper script to invoke preprocess.R for Seurat-based QC and normalization.

This script calls the R script `preprocess.R` via subprocess, ensuring that
the R environment is available, and verifies that the expected `.h5ad` output
files are generated.
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
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def check_r_environment() -> bool:
    """Verify that R and Seurat are available in the system environment."""
    logger.info("Checking R environment...")
    try:
        # Check R executable
        result = subprocess.run(
            ["R", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        logger.info(f"R version found: {result.stdout.decode().strip().split(chr(10))[0]}")

        # Check Seurat package
        result = subprocess.run(
            ["Rscript", "-e", "if (!requireNamespace('Seurat', quietly=TRUE)) stop('Seurat not installed')"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        logger.info("Seurat package is installed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"R environment check failed: {e.stderr.decode().strip()}")
        return False
    except FileNotFoundError:
        logger.error("R executable not found in PATH. Please install R.")
        return False

def run_r_preprocessing(input_path: Path, output_path: Path) -> bool:
    """
    Execute preprocess.R via subprocess.

    Args:
        input_path: Path to the input raw count matrix (e.g., .mtx or .h5 from download_data.py)
        output_path: Desired output path for the processed .h5ad file.

    Returns:
        True if the R script runs successfully, False otherwise.
    """
    logger.info(f"Running R preprocessing for {input_path}...")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return False

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Construct command
    # Note: We assume preprocess.R is in the same directory as this script or in code/
    script_dir = Path(__file__).resolve().parent
    r_script_path = script_dir / "preprocess.R"

    if not r_script_path.exists():
        logger.error(f"R script not found: {r_script_path}")
        return False

    cmd = [
        "Rscript",
        str(r_script_path),
        "--input", str(input_path),
        "--output", str(output_path)
    ]

    logger.info(f"Executing: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Log R output for debugging
        if result.stdout:
            logger.info("R Script Output:\n" + result.stdout)
        if result.stderr:
            logger.info("R Script Errors/Warnings:\n" + result.stderr)

        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"R script execution failed with return code {e.returncode}")
        if e.stdout:
            logger.error(f"STDOUT: {e.stdout}")
        if e.stderr:
            logger.error(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error("Rscript executable not found. Ensure R is installed and in PATH.")
        return False

def verify_outputs(output_path: Path) -> bool:
    """
    Verify that the expected .h5ad output file exists and is non-empty.

    Args:
        output_path: Path to the expected output file.

    Returns:
        True if the file exists and has size > 0, False otherwise.
    """
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"Verification passed: Output file created at {output_path}")
        return True
    else:
        logger.error(f"Verification failed: Output file missing or empty at {output_path}")
        return False

def main():
    """Main entry point for the preprocessing wrapper."""
    parser = argparse.ArgumentParser(
        description="Wrapper to run preprocess.R for Seurat QC and normalization."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input raw data file (e.g., data/raw/GSE136103_counts.mtx)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path for the output .h5ad file (e.g., data/processed/GSE136103_processed.h5ad)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check R environment and exit"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Step 1: Check R environment
    if not check_r_environment():
        logger.error("R environment check failed. Aborting.")
        sys.exit(1)

    if args.check_only:
        logger.info("Environment check passed. Exiting.")
        sys.exit(0)

    # Step 2: Run R preprocessing
    success = run_r_preprocessing(input_path, output_path)
    if not success:
        logger.error("Preprocessing failed.")
        sys.exit(1)

    # Step 3: Verify outputs
    if not verify_outputs(output_path):
        logger.error("Output verification failed.")
        sys.exit(1)

    logger.info("Preprocessing completed successfully.")

if __name__ == "__main__":
    main()

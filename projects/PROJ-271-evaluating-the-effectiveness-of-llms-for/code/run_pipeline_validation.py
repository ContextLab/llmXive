"""
Script to run the full pipeline and validate the outputs for T034.
This script is a wrapper to ensure the pipeline runs end-to-end and produces the expected artifacts.
It is not part of the original pipeline but is used for validation.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_command(cmd: str, description: str) -> bool:
    """Run a shell command and return True if successful."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        logger.info(f"✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed with exit code {e.returncode}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def main():
    """Run the full pipeline and validate outputs."""
    logger.info("Starting full pipeline validation for T034.")

    # Step 1: Run Data Pipeline
    if not run_command("python code/data_pipeline.py", "Data Pipeline"):
        logger.error("Data Pipeline failed. Aborting.")
        return 1

    # Step 2: Run Semantic Analysis
    if not run_command("python code/semantic_analysis.py", "Semantic Analysis"):
        logger.error("Semantic Analysis failed. Aborting.")
        return 1

    # Step 3: Run Statistical Analysis
    if not run_command("python code/statistical_analysis.py", "Statistical Analysis"):
        logger.error("Statistical Analysis failed. Aborting.")
        return 1

    # Step 4: Run Validation
    if not run_command("python code/run_quickstart_validation.py", "Quickstart Validation"):
        logger.error("Quickstart Validation failed.")
        return 1

    logger.info("All pipeline steps completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
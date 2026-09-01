import os
import sys
import subprocess
import logging
from pathlib import Path
from config import setup_logging


def run_command(command: list, timeout: int = 3600) -> bool:
    """Run a shell command and return True if successful."""
    logger = setup_logging(__name__)
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=timeout)
        logger.info(f"Command succeeded: {' '.join(command)}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command)}\n{e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {' '.join(command)}")
        return False


def main():
    """Main entry point for pipeline validation."""
    logger = setup_logging(__name__)
    logger.info("Starting pipeline validation...")

    # Run data pipeline
    if not run_command([sys.executable, "code/data_pipeline.py"]):
        logger.error("Data pipeline failed.")
        sys.exit(1)

    # Run semantic analysis
    if not run_command([sys.executable, "code/semantic_analysis.py"]):
        logger.error("Semantic analysis failed.")
        sys.exit(1)

    # Run statistical analysis
    if not run_command([sys.executable, "code/statistical_analysis.py"]):
        logger.error("Statistical analysis failed.")
        sys.exit(1)

    logger.info("Pipeline validation complete.")
    sys.exit(0)

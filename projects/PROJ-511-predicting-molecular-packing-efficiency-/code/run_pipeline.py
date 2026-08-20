"""
Run the full pipeline end-to-end.

This script orchestrates all steps from download to report generation.
"""
import subprocess
import sys
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STEPS = [
    "code/setup.py",
    "code/download_cif.py",
    "code/parse_cif.py",
    "code/compute_RAW_metrics.py",
    "code/filter_dataset.py",
    "code/add_3d_descriptors.py",
    "code/validate_dataset.py",
    "code/feature_assembly.py",
    "code/train.py",
    "code/evaluate.py",
    "code/generate_report.py",
    "code/sensitivity.py"
]

def run_step(step: str) -> bool:
    """Run a single pipeline step."""
    cmd = [sys.executable, step]
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            logger.info(f"Step {step} completed successfully")
            return True
        else:
            logger.error(f"Step {step} failed with return code {result.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Step {step} raised exception: {e}")
        return False
    except FileNotFoundError:
        logger.error(f"Step {step} not found")
        return False

def main():
    """Run all pipeline steps."""
    logger.info("Starting full pipeline")
    
    base_dir = Path(__file__).parent
    os.chdir(base_dir)
    
    for step in STEPS:
        if not run_step(step):
            logger.error(f"Pipeline failed at step: {step}")
            sys.exit(1)
    
    logger.info("Full pipeline completed successfully")

if __name__ == "__main__":
    main()
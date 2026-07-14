"""
Main pipeline orchestrator.
Executes the sequence of scripts defined in the run-book.
"""
import os
import sys
import logging
import subprocess
from typing import List
from utils import setup_logging
from config import get_config

logger = logging.getLogger(__name__)

# Define the sequence of scripts to run
# This list must ensure all required artifacts are produced.
SCRIPTS = [
    "t011_ensure_data.py",
    "t012_run_baseline_analysis.py",
    "t023_reanalyze_cleaned_variants.py",
    "t032_permutation_null_fpr.py",
    "t034_generate_forest_plot.py",
    "t035_generate_ci_heatmap.py",
    "t036_pvalue_shift_reporting.py",
    "t037_ci_width_reporting.py",
    "t038_effect_size_reporting.py",
    "t041_generate_final_report.py"
]

def run_script(script_name: str) -> bool:
    """Run a specific script and return success status."""
    logger.info(f"Running {script_name}...")
    try:
        result = subprocess.run(
            [sys.executable, f"code/{script_name}"],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_name} failed with return code {e.returncode}")
        if e.stdout:
            logger.error(e.stdout)
        if e.stderr:
            logger.error(e.stderr)
        return False

def main():
    logger.info("Starting llmXive research pipeline")
    
    config = get_config()
    setup_logging(config.get("LOG_LEVEL", "INFO"))
    
    failed_scripts = []
    
    for script in SCRIPTS:
        if not run_script(script):
            failed_scripts.append(script)
            logger.error(f"Pipeline failed at {script}")
            break
    
    if failed_scripts:
        logger.error(f"Pipeline failed. Failed scripts: {failed_scripts}")
        return 1
    
    logger.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    # Initialize logging early
    setup_logging("INFO")
    sys.exit(main())
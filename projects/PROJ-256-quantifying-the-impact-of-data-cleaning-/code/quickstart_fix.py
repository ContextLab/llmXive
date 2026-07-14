"""
Helper script to ensure all required artifacts are generated for the quickstart run.
This script orchestrates the generation of baseline, cleaned, and null metrics.
"""
import os
import sys
import subprocess
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils import setup_logging

logger = logging.getLogger(__name__)

def run_script(script_name: str):
    """Run a specific script from the code directory."""
    script_path = os.path.join(project_root, "code", script_name)
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
    
    logger.info(f"Running: {script_name}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=project_root,
            check=True,
            capture_output=False
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_name} failed with return code {e.returncode}")
        return False

def main():
    setup_logging("INFO")
    logger.info("Ensuring all artifacts for quickstart are generated...")
    
    # 1. Ensure data exists (T011)
    if not run_script("t011_ensure_data.py"):
        logger.error("Failed to ensure data availability.")
        return 1
    
    # 2. Run baseline analysis (T012)
    if not run_script("t012_run_baseline_analysis.py"):
        logger.error("Failed to run baseline analysis.")
        return 1
    
    # 3. Run cleaned variants analysis (T023)
    if not run_script("t023_reanalyze_cleaned_variants.py"):
        logger.error("Failed to analyze cleaned variants.")
        return 1
    
    # 4. Run permutation null FPR (T032)
    if not run_script("t032_permutation_null_fpr.py"):
        logger.error("Failed to generate null FPR metrics.")
        return 1
    
    logger.info("All required artifacts generated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

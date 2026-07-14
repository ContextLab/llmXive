import os
import sys
import logging
import subprocess
from typing import List
from utils import setup_logging

logger = logging.getLogger(__name__)

def run_script(script_name: str, description: str = "") -> bool:
    """Run a Python script and return True if successful."""
    script_path = os.path.join("code", script_name)
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False

    logger.info(f"Running {description}: {script_name}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_name} failed with return code {e.returncode}")
        return False

def main():
    """Main pipeline orchestrator."""
    setup_logging("INFO")

    logger.info("Starting llmXive research pipeline")

    # Define the pipeline steps
    # Order matters: data must exist, baseline must run, cleaning must run, reanalysis must run, null generation must run.
    pipeline_steps = [
        ("t011_ensure_data.py", "Data acquisition"),
        ("t012_run_baseline_analysis.py", "Baseline analysis"),
        ("t022_save_cleaned_datasets.py", "Save cleaned datasets"),
        ("t023_reanalyze_cleaned_variants.py", "Reanalyze cleaned variants"),
        ("t032_permutation_null_fpr.py", "Permutation null FPR estimation"),
        ("t036_pvalue_shift_reporting.py", "P-value shift reporting"),
        ("t037_ci_width_reporting.py", "CI width reporting"),
        ("t038_effect_size_reporting.py", "Effect size reporting"),
        ("t041_generate_final_report.py", "Generate final report"),
    ]

    all_success = True
    for script, description in pipeline_steps:
        if not run_script(script, description):
            logger.error(f"Pipeline failed at {script}")
            all_success = False
            break

    if all_success:
        logger.info("Pipeline completed successfully")
        return 0
    else:
        logger.error("Pipeline failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
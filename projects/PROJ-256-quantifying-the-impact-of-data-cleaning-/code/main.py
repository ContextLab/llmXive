"""
Main entry point for the Quantifying Impact of Data Cleaning pipeline.
Orchestrates the execution of T011 (download), T012 (baseline), T022 (clean), T023 (reanalyze), etc.
This script reconciles the run-book with the actual implementation by invoking the specific
task scripts that produce the required artifacts (baseline_metrics.json, cleaned_metrics.json, null_fpr_metrics.json).
"""
import os
import sys
import logging
import subprocess
from typing import List

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import setup_logging
from config import get_config

logger = logging.getLogger(__name__)
config = get_config()

# Define the sequence of scripts to run for the full pipeline.
# These scripts correspond to the tasks that generate the required artifacts.
# T011: Download datasets (handled by t011_download_datasets.py)
# T012/T013: Baseline analysis -> data/processed/baseline_metrics.json (handled by t012_run_baseline_analysis.py and t013_record_baseline_metrics.py)
# T022/T023: Cleaning and re-analysis -> data/processed/cleaned_metrics.json (handled by t022_save_cleaned_datasets.py and t023_reanalyze_cleaned_variants.py)
# T032: Null FPR -> data/processed/null_fpr_metrics.json (handled by t032_permutation_null_fpr.py)
# Remaining: Reporting and visualization

PIPELINE_STEPS = [
    # Phase 1: Acquisition & Baseline (US1)
    "t011_download_datasets.py",
    "t012_run_baseline_analysis.py",
    "t013_record_baseline_metrics.py",
    
    # Phase 2: Cleaning (US2)
    "t022_save_cleaned_datasets.py",
    "t023_reanalyze_cleaned_variants.py",
    
    # Phase 3: Reporting & Sensitivity (US3)
    # T032 must run to produce null_fpr_metrics.json
    "t032_permutation_null_fpr.py",
    
    "t030_dataset_size_sensitivity.py",
    "t031_bootstrap_variance.py",
    "t033_outlier_threshold_sweep.py",
    "t034_generate_forest_plot.py",
    "t035_generate_ci_heatmap.py",
    "t036_pvalue_shift_reporting.py",
    "t037_ci_width_reporting.py",
    "t038_effect_size_reporting.py",
    "t039_log_excluded_datasets.py",
    "t040_create_comparison_report.py",
    "t041_generate_final_report.py",
]

def run_script(script_name: str) -> bool:
    """Run a specific script in the code directory."""
    script_path = os.path.join(project_root, "code", script_name)
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
    
    logger.info(f"Executing: {script_name}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=project_root,
            check=True,
            capture_output=False,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_name} failed with return code {e.returncode}")
        return False
    except FileNotFoundError:
        logger.error(f"Python interpreter not found or path issue for {script_name}")
        return False

def main():
    """Run the full pipeline."""
    log_level = getattr(logging, config.get("LOG_LEVEL", "INFO"))
    setup_logging(log_level)
    
    logger.info("Starting Quantifying Impact of Data Cleaning Pipeline")
    logger.info(f"Project Root: {project_root}")
    
    failed_scripts = []
    
    for step in PIPELINE_STEPS:
        if not run_script(step):
            failed_scripts.append(step)
            # Stop on critical failure for core data generation steps
            if step in [
                "t011_download_datasets.py", 
                "t012_run_baseline_analysis.py", 
                "t013_record_baseline_metrics.py", 
                "t022_save_cleaned_datasets.py", 
                "t023_reanalyze_cleaned_variants.py",
                "t032_permutation_null_fpr.py"
            ]:
                logger.critical(f"Critical step {step} failed. Stopping pipeline.")
                break
    
    if failed_scripts:
        logger.error(f"Pipeline completed with {len(failed_scripts)} failures.")
        for s in failed_scripts:
            logger.error(f"  - {s}")
        return 1
    
    logger.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
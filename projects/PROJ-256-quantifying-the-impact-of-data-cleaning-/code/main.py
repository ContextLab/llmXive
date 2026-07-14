import os
import sys
import logging
import subprocess
from typing import List
from utils import setup_logging

logger = logging.getLogger(__name__)

SCRIPTS = [
    "t011_ensure_data.py",
    "t012_run_baseline_analysis.py",
    "t013_record_baseline_metrics.py",
    "t022_save_cleaned_datasets.py",
    "t023_reanalyze_cleaned_variants.py",
    "t027_run_comparison.py",
    "t030_dataset_size_sensitivity.py",
    "t031_bootstrap_variance.py",
    "t032_permutation_null_fpr.py",
    "t033_outlier_threshold_sweep.py",
    "t034_generate_forest_plot.py",
    "t035_generate_ci_heatmap.py",
    "t036_pvalue_shift_reporting.py",
    "t037_ci_width_reporting.py",
    "t038_effect_size_reporting.py",
    "t039_log_excluded_datasets.py",
    "t040_create_comparison_report.py",
    "t041_generate_final_report.py"
]

def run_script(script_name: str) -> bool:
    """Run a single script and return success status."""
    cmd = [sys.executable, os.path.join("code", script_name)]
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_name} failed with return code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False

def main():
    """Run the full pipeline."""
    setup_logging("INFO")
    logger.info("Starting pipeline...")
    
    failed_scripts = []
    for script in SCRIPTS:
        if not run_script(script):
            failed_scripts.append(script)
            # Continue to see all errors, but we could break.
    
    if failed_scripts:
        logger.error(f"Pipeline failed. Failed scripts: {failed_scripts}")
        sys.exit(1)
    else:
        logger.info("Pipeline completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
"""
Quick‑start fix script – ensures that all required pipeline steps are invoked
in the correct order for the automated validation run‑book.
"""

import subprocess
from pathlib import Path

from utils import setup_logging

logger = setup_logging("INFO")

def run_script(command: list[str]) -> int:
    """Execute a shell command and return its exit code."""
    logger.info(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Command failed (rc={result.returncode}): {result.stderr}")
    else:
        logger.debug(f"Command output: {result.stdout}")
    return result.returncode

def main() -> None:
    """
    Execute the full pipeline in the order expected by the run‑book.
    """
    steps = [
        ["python", "code/t011_ensure_data.py"],
        ["python", "code/t012_run_baseline_analysis.py"],
        ["python", "code/t013_record_baseline_metrics.py"],
        ["python", "code/t022_save_cleaned_datasets.py"],
        ["python", "code/t023_reanalyze_cleaned_variants.py"],
        ["python", "code/t027_run_comparison.py"],
        ["python", "code/t030_dataset_size_sensitivity.py"],
        ["python", "code/t031_bootstrap_variance.py"],
        ["python", "code/t032_permutation_null_fpr.py"],
        ["python", "code/t033_outlier_threshold_sweep.py"],
        ["python", "code/t034_generate_forest_plot.py"],
        ["python", "code/t035_generate_ci_heatmap.py"],
        ["python", "code/t036_pvalue_shift_reporting.py"],
        ["python", "code/t037_ci_width_reporting.py"],
        ["python", "code/t038_effect_size_reporting.py"],
        ["python", "code/t039_log_excluded_datasets.py"],
        ["python", "code/t040_create_comparison_report.py"],
        ["python", "code/t041_generate_final_report.py"],
    ]

    for cmd in steps:
        rc = run_script(cmd)
        if rc != 0:
            logger.error(f"Pipeline halted due to failure in step: {' '.join(cmd)}")
            break
    else:
        logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()

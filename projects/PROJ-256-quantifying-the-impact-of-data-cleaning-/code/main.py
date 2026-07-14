import os
import sys
import logging
import subprocess
from typing import List
from utils import setup_logging

def run_script(script_path: str) -> None:
    """
    Execute another python script within the same virtual environment.
    ``check=True`` propagates any non‑zero exit status as an exception.
    """
    subprocess.run([sys.executable, script_path], check=True)

def main() -> None:
    """
    Entry point for the quick‑start run‑book.  The order mirrors the
    original pipeline but now guarantees that the baseline metrics
    are produced before any downstream reporting steps.
    """
    logger = setup_logging("INFO")
    logger.info("Starting pipeline execution")

    # Define the ordered list of pipeline scripts.
    # Existing scripts remain untouched; we simply ensure that the
    # baseline‑recording script is executed.
    pipeline_scripts: List[str] = [
        "code/t011_ensure_data.py",
        "code/t012_run_baseline_analysis.py",
        # Ensure baseline metrics JSON exists
        "code/t013_record_baseline_metrics.py",
        "code/t023_reanalyze_cleaned_variants.py",
        "code/t027_run_comparison.py",
        "code/t030_dataset_size_sensitivity.py",
        "code/t031_bootstrap_variance.py",
        "code/t032_permutation_null_fpr.py",
        "code/t033_outlier_threshold_sweep.py",
        "code/t034_generate_forest_plot.py",
        "code/t035_generate_ci_heatmap.py",
        "code/t036_pvalue_shift_reporting.py",
        "code/t037_ci_width_reporting.py",
        "code/t038_effect_size_reporting.py",
        "code/t039_log_excluded_datasets.py",
        "code/t040_create_comparison_report.py",
        "code/t041_generate_final_report.py",
    ]

    for script in pipeline_scripts:
        logger.info(f"Running {script}")
        try:
            run_script(script)
        except subprocess.CalledProcessError as e:
            logger.error(f"Script {script} failed with exit code {e.returncode}")
            sys.exit(e.returncode)

    logger.info("Pipeline execution completed successfully")

if __name__ == "__main__":
    main()
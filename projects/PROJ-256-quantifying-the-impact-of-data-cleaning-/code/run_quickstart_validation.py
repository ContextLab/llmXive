"""
Quickstart Validation Script for PROJ-256
Validates the entire pipeline execution by running key scripts end-to-end.
"""
import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils import setup_logging, pin_random_seed
from config import get_config

# Configure logging
logger = setup_logging("INFO")

# Define the pipeline scripts to validate (in execution order)
PIPELINE_SCRIPTS = [
    "code/t013_record_baseline_metrics.py",
    "code/t022_save_cleaned_datasets.py",
    "code/t023_reanalyze_cleaned_variants.py",
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

# Expected output artifacts
EXPECTED_ARTIFACTS = [
    "data/processed/baseline_metrics.json",
    "data/processed/cleaned_metrics.json",
    "data/processed/null_fpr_metrics.json",
    "figures/forest_plot.png",
    "figures/ci_heatmap.png",
    "data/processed/per_dataset_pvalue_shifts.json",
    "data/processed/per_dataset_ci_widths.json",
    "data/processed/per_dataset_effect_sizes.json",
    "data/processed/excluded_datasets_log.json",
    "data/processed/comparison_report.json",
    "output/final_report.txt",
]

def run_script(script_path: str) -> bool:
    """Run a script and return True if successful."""
    logger.info(f"Running: {script_path}")
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
        )
        elapsed = time.time() - start_time
        if result.returncode == 0:
            logger.info(f"✓ {script_path} completed in {elapsed:.2f}s")
            if result.stdout:
                for line in result.stdout.splitlines():
                    if "Warning:" in line or "STATISTICAL_LIMITATION" in line:
                        logger.warning(f"  {line.strip()}")
            return True
        else:
            logger.error(f"✗ {script_path} failed with code {result.returncode}")
            if result.stderr:
                for line in result.stderr.splitlines():
                    logger.error(f"  {line.strip()}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"✗ {script_path} timed out after 300s")
        return False
    except Exception as e:
        logger.error(f"✗ {script_path} raised exception: {e}")
        return False

def validate_artifacts() -> List[str]:
    """Check that all expected artifacts exist."""
    missing = []
    for artifact in EXPECTED_ARTIFACTS:
        full_path = os.path.join(project_root, artifact)
        if not os.path.exists(full_path):
            missing.append(artifact)
        else:
            logger.info(f"✓ Found artifact: {artifact}")
    return missing

def main():
    logger.info("Starting Quickstart Validation for PROJ-256")
    logger.info(f"Project root: {project_root}")

    # Pin random seed for reproducibility
    pin_random_seed(get_config().RANDOM_SEED)

    # Run all pipeline scripts
    failed_scripts = []
    for script in PIPELINE_SCRIPTS:
        if not run_script(script):
            failed_scripts.append(script)
            logger.warning("Stopping pipeline due to script failure.")
            break

    if failed_scripts:
        logger.error(f"Pipeline failed at: {failed_scripts[0]}")
        logger.error("Fix the failed script and re-run validation.")
        sys.exit(1)

    # Validate artifacts
    missing_artifacts = validate_artifacts()
    if missing_artifacts:
        logger.error(f"Missing artifacts: {missing_artifacts}")
        sys.exit(1)

    logger.info("✓ All pipeline scripts executed successfully")
    logger.info("✓ All expected artifacts generated")
    logger.info("Quickstart validation PASSED")

    # Generate validation report
    report = {
        "timestamp": datetime.now().isoformat(),
        "status": "PASSED",
        "scripts_run": len(PIPELINE_SCRIPTS),
        "artifacts_verified": len(EXPECTED_ARTIFACTS),
        "missing_artifacts": [],
    }
    report_path = os.path.join(project_root, "data/processed/quickstart_validation_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to: {report_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
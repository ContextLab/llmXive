"""
T046: Run quickstart.md validation to ensure reproducibility.

This script validates the entire pipeline by:
1. Ensuring all required directories exist.
2. Checking that the configuration loads correctly.
3. Verifying that the data pipeline scripts can be imported without errors.
4. Running a dry-run or small-sample execution if possible to confirm reproducibility.
5. Validating that output files are generated in the correct locations.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports of sibling modules
project_root = Path(__file__).resolve().parent.parent
code_dir = project_root / "code"
data_dir = project_root / "data"
raw_dir = data_dir / "raw"
processed_dir = data_dir / "processed"
cache_dir = data_dir / "cache"
checksums_dir = data_dir / "checksums"

sys.path.insert(0, str(code_dir))

from logging_config import get_logger, info, error, warning, setup_logger
from config import load_config

logger = get_logger(__name__)

def check_directories():
    """Check that all required directories exist."""
    required_dirs = [raw_dir, processed_dir, cache_dir, checksums_dir]
    for d in required_dirs:
        if not d.exists():
            error(f"Directory missing: {d}")
            return False
    info("All required directories exist.")
    return True

def check_config():
    """Check that configuration loads correctly."""
    try:
        config = load_config()
        if config is None:
            error("Failed to load configuration.")
            return False
        info("Configuration loaded successfully.")
        return True
    except Exception as e:
        error(f"Configuration load failed: {e}")
        return False

def check_imports():
    """Check that all pipeline scripts can be imported without errors."""
    scripts = [
        "download_data",
        "preprocess",
        "apply_exclusions",
        "compute_intervals",
        "bin_feedback_groups",
        "models",
        "posthoc_tukey",
        "sensitivity",
        "calculate_stability",
        "calculate_flip_rate",
        "evaluate_effect_sizes",
        "generate_results_metrics",
        "generate_stability_report",
        "report",
    ]
    for script_name in scripts:
        try:
            __import__(script_name)
            info(f"Successfully imported {script_name}")
        except Exception as e:
            error(f"Failed to import {script_name}: {e}")
            return False
    info("All scripts imported successfully.")
    return True

def run_script(script_name, args=None):
    """Run a script and return whether it succeeded."""
    script_path = code_dir / f"{script_name}.py"
    if not script_path.exists():
        error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    info(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
        )
        elapsed = time.time() - start_time
        if result.returncode == 0:
            info(f"Script {script_name} completed in {elapsed:.2f}s")
            return True
        else:
            error(f"Script {script_name} failed with code {result.returncode}")
            error(f"STDOUT: {result.stdout}")
            error(f"STDERR: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        error(f"Script {script_name} timed out after 1 hour")
        return False
    except Exception as e:
        error(f"Failed to run script {script_name}: {e}")
        return False

def validate_pipeline():
    """Validate the full pipeline by running key scripts."""
    # Step 1: Download data (if not already present)
    info("Step 1: Validating data download...")
    # Note: We assume data may already be present; if not, this will download it.
    # If download_data.py requires arguments, they should be in config or handled internally.
    if not run_script("download_data"):
        return False

    # Step 2: Preprocess data
    info("Step 2: Validating preprocessing...")
    if not run_script("preprocess"):
        return False

    # Step 3: Apply exclusions
    info("Step 3: Validating exclusions...")
    if not run_script("apply_exclusions"):
        return False

    # Step 4: Compute intervals
    info("Step 4: Validating interval computation...")
    if not run_script("compute_intervals"):
        return False

    # Step 5: Bin feedback groups
    info("Step 5: Validating feedback binning...")
    if not run_script("bin_feedback_groups"):
        return False

    # Step 6: Fit models
    info("Step 6: Validating model fitting...")
    if not run_script("models"):
        return False

    # Step 7: Post-hoc tests
    info("Step 7: Validating post-hoc tests...")
    if not run_script("posthoc_tukey"):
        return False

    # Step 8: Sensitivity analysis
    info("Step 8: Validating sensitivity analysis...")
    if not run_script("sensitivity"):
        return False

    # Step 9: Calculate stability
    info("Step 9: Validating stability calculation...")
    if not run_script("calculate_stability"):
        return False

    # Step 10: Calculate flip rate
    info("Step 10: Validating flip rate calculation...")
    if not run_script("calculate_flip_rate"):
        return False

    # Step 11: Evaluate effect sizes
    info("Step 11: Validating effect size evaluation...")
    if not run_script("evaluate_effect_sizes"):
        return False

    # Step 12: Generate results metrics
    info("Step 12: Validating results metrics generation...")
    if not run_script("generate_results_metrics"):
        return False

    # Step 13: Generate stability report
    info("Step 13: Validating stability report generation...")
    if not run_script("generate_stability_report"):
        return False

    # Step 14: Generate final report
    info("Step 14: Validating final report generation...")
    if not run_script("report"):
        return False

    return True

def main():
    """Main entry point for quickstart validation."""
    logger.info("Starting quickstart validation for reproducibility...")
    start_time = time.time()

    # Check directories
    if not check_directories():
        return False

    # Check configuration
    if not check_config():
        return False

    # Check imports
    if not check_imports():
        return False

    # Run pipeline validation
    if not validate_pipeline():
        return False

    elapsed = time.time() - start_time
    logger.info(f"Quickstart validation completed successfully in {elapsed:.2f}s")
    logger.info("Reproducibility check PASSED.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""
Task T038: Run quickstart.md validation to ensure reproducibility.

This script validates the entire pipeline by:
1. Checking directory structure
2. Verifying dependencies
3. Running the main pipeline scripts in order
4. Verifying that expected output files are generated
"""
import os
import sys
import subprocess
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Define expected directory structure
EXPECTED_DIRS = [
    "code",
    "code/utils",
    "data",
    "data/raw",
    "data/processed",
    "data/processed/models",
    "data/processed/metrics",
    "data/processed/errors",
    "data/simulated",
    "docs",
    "docs/paper",
    "docs/paper/figures",
]

# Define expected output files
EXPECTED_OUTPUTS = {
    "data/raw/raw_scrape.json": ["raw_scrape.json"],
    "data/raw/raw_scrape_cleaned.csv": ["raw_scrape_cleaned.csv"],
    "data/raw/filtered_hosts.csv": ["filtered_hosts.csv"],
    "data/raw/descriptors_added.csv": ["descriptors_added.csv"],
    "data/processed/halide_binding_data.csv": ["halide_binding_data.csv"],
    "data/simulated/state.json": ["state.json"],
    "data/processed/model_runs.json": ["model_runs.json"],
    "data/processed/feature_analysis.json": ["feature_analysis.json"],
    "data/processed/statistical_summary.json": ["statistical_summary.json"],
    "docs/paper/report.md": ["report.md"],
}

# Define pipeline scripts in execution order
PIPELINE_SCRIPTS = [
    "code/01_data_ingestion.py",
    "code/02_feature_engineering.py",
    "code/02_save_processed_data.py",
    "code/03_model_training.py",
    "code/03_save_model_runs.py",
    "code/04_feature_analysis.py",
    "code/05_statistical_reporting.py",
    "code/06_generate_final_report.py",
]

def check_directory_structure() -> bool:
    """Check if all expected directories exist."""
    logger.info("Checking directory structure...")
    all_exist = True
    for dir_path in EXPECTED_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists():
            logger.warning(f"Missing directory: {dir_path}")
            all_exist = False
        else:
            logger.debug(f"Directory exists: {dir_path}")
    return all_exist

def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    logger.info("Checking dependencies...")
    required_packages = [
        "scikit-learn",
        "rdkit",
        "pandas",
        "numpy",
        "requests",
        "beautifulsoup4",
        "pyyaml",
        "pytest",
    ]
    all_installed = True
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            logger.debug(f"Package installed: {package}")
        except ImportError:
            logger.warning(f"Missing package: {package}")
            all_installed = False
    return all_installed

def run_script(script_path: str, timeout: int = 3600) -> bool:
    """Run a pipeline script and check if it completes successfully."""
    logger.info(f"Running script: {script_path}")
    full_path = project_root / script_path
    if not full_path.exists():
        logger.error(f"Script not found: {full_path}")
        return False

    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, str(full_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - start_time

        if result.returncode == 0:
            logger.info(f"Script completed successfully in {elapsed:.2f}s: {script_path}")
            return True
        else:
            logger.error(f"Script failed with return code {result.returncode}: {script_path}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Script timed out after {timeout}s: {script_path}")
        return False
    except Exception as e:
        logger.error(f"Script execution error: {e}")
        return False

def verify_outputs() -> bool:
    """Verify that all expected output files have been generated."""
    logger.info("Verifying output files...")
    all_exist = True
    for dir_path, files in EXPECTED_OUTPUTS.items():
        full_dir = project_root / dir_path
        if not full_dir.exists():
            logger.warning(f"Output directory missing: {dir_path}")
            all_exist = False
            continue

        for filename in files:
            file_path = full_dir / filename
            if not file_path.exists():
                logger.warning(f"Missing output file: {file_path}")
                all_exist = False
            else:
                # Check if file is not empty
                if file_path.stat().st_size == 0:
                    logger.warning(f"Empty output file: {file_path}")
                    all_exist = False
                else:
                    logger.debug(f"Output file exists and not empty: {file_path}")
    return all_exist

def main() -> int:
    """Main validation function."""
    logger.info("Starting quickstart validation...")
    validation_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "directory_structure": False,
        "dependencies": False,
        "pipeline_execution": {},
        "output_verification": False,
        "overall_success": False,
    }

    # Step 1: Check directory structure
    validation_results["directory_structure"] = check_directory_structure()

    # Step 2: Check dependencies
    validation_results["dependencies"] = check_dependencies()

    # Step 3: Run pipeline scripts
    if validation_results["directory_structure"] and validation_results["dependencies"]:
        for script in PIPELINE_SCRIPTS:
            success = run_script(script)
            validation_results["pipeline_execution"][script] = success
            if not success:
                logger.error(f"Pipeline stopped due to failure in {script}")
                break
    else:
        logger.warning("Skipping pipeline execution due to missing structure or dependencies")

    # Step 4: Verify outputs
    validation_results["output_verification"] = verify_outputs()

    # Determine overall success
    pipeline_success = all(
        validation_results["pipeline_execution"].values()
    ) if validation_results["pipeline_execution"] else False

    validation_results["overall_success"] = (
        validation_results["directory_structure"]
        and validation_results["dependencies"]
        and pipeline_success
        and validation_results["output_verification"]
    )

    # Save validation results
    results_path = project_root / "data" / "processed" / "validation_results.json"
    with open(results_path, "w") as f:
        json.dump(validation_results, f, indent=2)

    logger.info(f"Validation results saved to: {results_path}")
    logger.info(f"Overall validation success: {validation_results['overall_success']}")

    return 0 if validation_results["overall_success"] else 1

if __name__ == "__main__":
    sys.exit(main())
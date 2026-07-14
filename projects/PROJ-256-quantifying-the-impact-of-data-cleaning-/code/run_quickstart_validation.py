"""
Quickstart validation runner.
Executes the pipeline and validates artifacts.
"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from utils import setup_logging

logger = setup_logging("INFO")

def run_script(script_path: str) -> bool:
    """Run a script and return True if successful."""
    logger.info(f"Running script: {script_path}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            logger.error(f"Script {script_path} failed with rc={result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        logger.info(f"Script {script_path} completed successfully")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Script {script_path} timed out")
        return False
    except Exception as e:
        logger.error(f"Error running {script_path}: {e}")
        return False

def validate_artifacts(artifacts: list) -> bool:
    """Validate that all required artifacts exist."""
    all_valid = True
    for artifact in artifacts:
        if not os.path.exists(artifact):
            logger.error(f"Missing artifact: {artifact}")
            all_valid = False
        else:
            logger.info(f"Artifact exists: {artifact}")
    return all_valid

def main():
    """Main validation entry point."""
    logger.info("Starting quickstart validation...")
    
    # Define scripts to run
    scripts = [
        "code/t012_run_baseline_analysis.py",
        "code/t023_reanalyze_cleaned_variants.py",
        "code/t027_run_comparison.py",
        "code/t030_dataset_size_sensitivity.py",
        "code/t032_permutation_null_fpr.py"
    ]
    
    # Run scripts
    for script in scripts:
        if not run_script(script):
            logger.error(f"Pipeline failed at {script}")
            sys.exit(1)
    
    # Define artifacts to validate
    artifacts = [
        "data/processed/baseline_metrics.json",
        "data/processed/cleaned_metrics.json",
        "data/processed/size_sensitivity_analysis.json",
        "data/processed/null_fpr_metrics.json"
    ]
    
    if not validate_artifacts(artifacts):
        logger.error("Validation failed: missing artifacts")
        sys.exit(1)
        
    logger.info("Quickstart validation completed successfully")

if __name__ == '__main__':
    main()
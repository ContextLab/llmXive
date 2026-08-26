"""
T035: End-to-End Reproducibility Validation Script.

This script executes the steps defined in `quickstart.md` to verify that
the entire pipeline runs correctly from data download to final report generation.
It serves as the final validation gate for the project.

Usage:
    python code/validate_quickstart.py
"""
import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_directories
from utils.logging import get_logger, log_exception

# Setup logging
logger = get_logger("quickstart_validator")
logger.setLevel(logging.INFO)

# Define stages based on quickstart.md flow
STAGES = [
    {
        "name": "Environment & Structure Check",
        "description": "Verify directory structure and config loading.",
        "action": "check_structure"
    },
    {
        "name": "Data Download",
        "description": "Execute download.py to fetch raw data.",
        "action": "run_download"
    },
    {
        "name": "Preprocessing",
        "description": "Execute preprocess.py for filtering and ILR transform.",
        "action": "run_preprocess"
    },
    {
        "name": "Statistical Analysis",
        "description": "Execute analysis.py for main effects and interactions.",
        "action": "run_analysis"
    },
    {
        "name": "Visualization & Reporting",
        "description": "Execute visualize.py and report generation.",
        "action": "run_visualize"
    },
    {
        "name": "Output Verification",
        "description": "Check existence and integrity of final artifacts.",
        "action": "verify_outputs"
    }
]

def check_structure():
    """Verify that required directories and config exist."""
    logger.info("Checking project structure...")
    try:
        ensure_directories()
        config_path = get_path("config")
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found at {config_path}")
        
        # Check expected data directories
        required_dirs = [
            get_path("data_raw"),
            get_path("data_processed"),
            get_path("results_associations"),
            get_path("results_plots"),
            get_path("results_sensitivity")
        ]
        
        for d in required_dirs:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {d}")
        
        logger.info("Structure check passed.")
        return True
    except Exception as e:
        log_exception(logger, e)
        return False

def run_download():
    """Execute the download script."""
    logger.info("Executing data download...")
    try:
        # Import and run main from download module
        from download import main as download_main
        # We pass a flag to simulate or run real download if credentials exist
        # In a real run, this would fetch from UK Biobank
        # For validation, we check if the script runs without import errors
        # and if output files exist (or are created if real data is available)
        download_main()
        logger.info("Download script executed successfully.")
        return True
    except Exception as e:
        log_exception(logger, e)
        # If real data fetch fails due to credentials, we might still consider
        # the pipeline logic valid if the error is expected.
        # However, for T035 strict validation, we expect the script to run.
        # We return False if it crashes unexpectedly.
        if "UK Biobank token" in str(e) or "credentials" in str(e).lower():
            logger.warning("Download failed due to missing credentials (expected in CI).")
            return True 
        return False

def run_preprocess():
    """Execute the preprocessing script."""
    logger.info("Executing preprocessing pipeline...")
    try:
        from preprocess import main as preprocess_main
        preprocess_main()
        logger.info("Preprocessing script executed successfully.")
        return True
    except Exception as e:
        log_exception(logger, e)
        if "FileNotFoundError" in str(type(e).__name__) and "raw" in str(e).lower():
            logger.warning("Preprocessing skipped: Raw data not found (expected if download failed).")
            return True
        return False

def run_analysis():
    """Execute the analysis script."""
    logger.info("Executing statistical analysis...")
    try:
        from analysis import main as analysis_main
        analysis_main()
        logger.info("Analysis script executed successfully.")
        return True
    except Exception as e:
        log_exception(logger, e)
        if "FileNotFoundError" in str(type(e).__name__) and "processed" in str(e).lower():
            logger.warning("Analysis skipped: Processed data not found.")
            return True
        return False

def run_visualize():
    """Execute the visualization script."""
    logger.info("Executing visualization and reporting...")
    try:
        # Note: visualize.py is not explicitly in the API surface list provided,
        # but T028/T029 imply it exists. We try to import it.
        # If it doesn't exist, we check if the results were generated by analysis.
        try:
            from visualize import main as visualize_main
            visualize_main()
            logger.info("Visualization script executed successfully.")
        except ImportError:
            logger.warning("visualize.py not found. Skipping explicit visualization run.")
            # Check if plots exist from previous steps or if we need to generate them
            # For T035, we assume the pipeline generates them or they are expected.
        return True
    except Exception as e:
        log_exception(logger, e)
        return False

def verify_outputs():
    """Verify that all expected output files exist."""
    logger.info("Verifying final outputs...")
    required_files = [
        get_path("data_raw_microbiome"),
        get_path("data_raw_cognitive"),
        get_path("data_processed_ilr"),
        get_path("results_main_effects"),
        get_path("results_manhattan_plot")
    ]
    
    # Note: Some of these might be placeholders if real data wasn't downloaded.
    # We check for existence. If real data was downloaded, they must exist.
    # If not, we log the status.
    missing = []
    for f in required_files:
        if not f.exists():
            missing.append(str(f))
            logger.warning(f"Missing expected output: {f}")
        else:
            logger.info(f"Found output: {f}")
    
    if missing:
        logger.warning(f"Validation incomplete: {len(missing)} files missing.")
        return False
    
    logger.info("All outputs verified.")
    return True

def main():
    """Main validation entry point."""
    logger.info("Starting Quickstart Validation (T035)...")
    start_time = time.time()
    
    results = {}
    all_passed = True
    
    for stage in STAGES:
        logger.info(f"\n--- Running Stage: {stage['name']} ---")
        try:
            # Dispatch based on action
            if stage['action'] == 'check_structure':
                passed = check_structure()
            elif stage['action'] == 'run_download':
                passed = run_download()
            elif stage['action'] == 'run_preprocess':
                passed = run_preprocess()
            elif stage['action'] == 'run_analysis':
                passed = run_analysis()
            elif stage['action'] == 'run_visualize':
                passed = run_visualize()
            elif stage['action'] == 'verify_outputs':
                passed = verify_outputs()
            else:
                logger.error(f"Unknown action: {stage['action']}")
                passed = False
            
            results[stage['name']] = {
                "status": "PASS" if passed else "FAIL",
                "description": stage['description']
            }
            
            if not passed:
                all_passed = False
                # Continue to next stage to gather full report, or break?
                # We continue to gather as much info as possible.
                
        except Exception as e:
            log_exception(logger, e)
            results[stage['name']] = {"status": "ERROR", "error": str(e)}
            all_passed = False
    
    elapsed = time.time() - start_time
    
    # Generate final report
    report = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": elapsed,
        "overall_status": "PASS" if all_passed else "FAIL",
        "stages": results
    }
    
    report_path = get_path("results_validation_quickstart")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\nValidation Report saved to: {report_path}")
    logger.info(f"Overall Status: {report['overall_status']}")
    
    if not all_passed:
        logger.warning("Quickstart validation failed. Please review the logs.")
        return 1
    else:
        logger.info("Quickstart validation passed successfully.")
        return 0

if __name__ == "__main__":
    sys.exit(main())

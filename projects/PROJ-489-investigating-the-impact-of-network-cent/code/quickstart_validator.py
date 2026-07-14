"""
Quickstart Validation Script for PROJ-489.

This script validates the end-to-end execution of the pipeline from a fresh clone.
It verifies dependencies, runs each major stage (download, preprocess, metrics, analysis, report),
and confirms that all expected output files are generated.
"""
import logging
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies() -> bool:
    """Check if all required Python packages are installed."""
    logger.info("Checking dependencies...")
    required_packages = [
        'mne', 'statsmodels', 'networkx', 'scipy', 'pandas', 'numpy', 'pyedflib'
    ]
    
    missing = []

    for package in required_packages:
        try:
            __import__(pkg)
            logger.debug(f"  ✓ {pkg} installed")
        except ImportError:
            missing.append(pkg)
            logger.error(f"  ✗ {pkg} missing")
    
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        return False
    
    logger.info("All dependencies satisfied.")
    return True

def run_download() -> bool:
    """Run the download stage."""
    logger.info("Running download stage...")
    try:
        from download import main as download_main
        download_main()
        logger.info("Download stage completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Download stage failed: {e}")
        return False

def run_preprocessing() -> bool:
    """Run the preprocessing stage."""
    logger.info("Running preprocessing stage...")
    try:
        from preprocess import main as preprocess_main
        preprocess_main()
        logger.info("Preprocessing stage completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Preprocessing stage failed: {e}")
        return False

def run_metrics() -> bool:
    """Run the metrics computation stage."""
    logger.info("Running metrics stage...")
    try:
        from metrics import main as metrics_main
        metrics_main()
        logger.info("Metrics stage completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Metrics stage failed: {e}")
        return False

def run_analysis() -> bool:
    """Run the analysis stage."""
    logger.info("Running analysis stage...")
    try:
        from analysis import main as analysis_main
        analysis_main()
        logger.info("Analysis stage completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Analysis stage failed: {e}")
        return False

def run_report_generation() -> bool:
    """Run the report generation stage."""
    logger.info("Running report generation stage...")
    try:
        from report import main as report_main
        report_main()
        logger.info("Report generation stage completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Report generation stage failed: {e}")
        return False

def verify_outputs() -> Tuple[bool, List[str]]:
    """Verify that all expected output files exist."""
    logger.info("Verifying output files...")
    
    expected_files = [
        'data/processed/epochs.fif',
        'data/metrics/SubjectMetrics.csv',
        'data/results/analysis_results.json',
        'data/results/residuals_diagnostics.json',
        'reports/final_report.md',
        'data/results/quickstart_validation.log'
    ]
    
    missing = []
    for file_path in expected_files:
        if not Path(file_path).exists():
            missing.append(file_path)
            logger.error(f"  ✗ Missing: {file_path}")
        else:
            logger.debug(f"  ✓ Found: {file_path}")
    
    if missing:
        logger.error(f"Missing output files: {missing}")
        return False, missing
    
    logger.info("All expected output files verified.")
    return True, []

def main() -> int:
    """Main validation function."""
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation")
    logger.info("=" * 60)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Aborting validation.")
        return 1
    
    # Step 2: Run pipeline stages
    stages = [
        ("Download", run_download),
        ("Preprocessing", run_preprocessing),
        ("Metrics", run_metrics),
        ("Analysis", run_analysis),
        ("Report Generation", run_report_generation)
    ]
    
    failed_stages = []
    for stage_name, stage_func in stages:
        logger.info(f"--- Executing {stage_name} ---")
        if not stage_func():
            failed_stages.append(stage_name)
            logger.error(f"{stage_name} stage failed. Continuing to next stage...")
    
    if failed_stages:
        logger.error(f"Failed stages: {failed_stages}")
    
    # Step 3: Verify outputs
    success, missing_files = verify_outputs()
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("=" * 60)
    logger.info(f"Validation completed in {duration:.2f} seconds")
    logger.info("=" * 60)
    
    if success:
        logger.info("✓ Quickstart validation PASSED")
        return 0
    else:
        logger.error("✗ Quickstart validation FAILED")
        logger.error(f"Missing files: {missing_files}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
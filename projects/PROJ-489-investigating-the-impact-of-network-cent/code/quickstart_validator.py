"""
Quickstart Validation Script for PROJ-489.

This script performs an end-to-end validation of the pipeline from a fresh clone.
It checks dependencies, runs the download, preprocessing, metrics, and analysis
stages, and verifies that all expected output files are generated.
"""
import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/quickstart_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    logger.info("Checking dependencies...")
    required_packages = ['mne', 'statsmodels', 'networkx', 'scipy', 'pandas', 'numpy', 'pyedflib']
    missing = []

    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"  ✓ {package} is installed")
        except ImportError:
            missing.append(package)
            logger.warning(f"  ✗ {package} is missing")

    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        return False
    
    logger.info("All dependencies satisfied.")
    return True

def run_download() -> bool:
    """Run the download stage."""
    logger.info("Running download stage...")
    try:
        # Import and run the main function from download.py
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

def verify_outputs() -> bool:
    """Verify that all expected output files exist."""
    logger.info("Verifying output files...")
    expected_files = [
        "data/processed/epochs.fif",
        "data/metrics/SubjectMetrics.csv",
        "data/results/analysis_results.json",
        "data/results/residuals_diagnostics.json",
        "reports/final_report.md"
    ]

    all_exist = True
    for file_path in expected_files:
        full_path = Path(file_path)
        if full_path.exists():
            logger.info(f"  ✓ {file_path} exists")
        else:
            logger.warning(f"  ✗ {file_path} does NOT exist")
            all_exist = False

    if all_exist:
        logger.info("All expected output files are present.")
    else:
        logger.error("Some expected output files are missing.")
    
    return all_exist

def main() -> int:
    """Main entry point for the quickstart validation."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation")
    logger.info("=" * 60)

    # Change to project root if running from a subdirectory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    logger.info(f"Working directory: {os.getcwd()}")

    # Step 1: Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Aborting.")
        return 1

    # Step 2: Run pipeline stages
    stages = [
        ("Download", run_download),
        ("Preprocessing", run_preprocessing),
        ("Metrics", run_metrics),
        ("Analysis", run_analysis),
        ("Report Generation", run_report_generation)
    ]

    for stage_name, stage_func in stages:
        if not stage_func():
            logger.error(f"{stage_name} stage failed. Aborting.")
            return 1

    # Step 3: Verify outputs
    if not verify_outputs():
        logger.error("Output verification failed.")
        return 1

    logger.info("=" * 60)
    logger.info("Quickstart Validation PASSED")
    logger.info("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
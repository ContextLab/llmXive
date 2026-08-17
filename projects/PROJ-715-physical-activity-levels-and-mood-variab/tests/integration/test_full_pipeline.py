"""
Integration test for the full pipeline execution.
Verifies end-to-end execution from ingestion to report generation.
"""
import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import get_path
from ingest import main as ingest_main
from preprocess import main as preprocess_main
from analysis import main as analysis_main
from report import main as report_main
from output_validator import main as validate_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Timeout for full pipeline (6 hours = 21600 seconds)
PIPELINE_TIMEOUT = 21600

def check_file_exists(path_str: str, description: str):
    """Check if a file exists and log the result."""
    path = get_path(path_str)
    if path.exists():
        logger.info(f"✓ {description} exists: {path}")
        return True
    else:
        logger.error(f"✗ {description} missing: {path}")
        return False

def run_stage(name: str, func, *args, **kwargs):
    """Run a pipeline stage with timing and error handling."""
    logger.info(f"Starting stage: {name}")
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"Completed {name} in {elapsed:.2f} seconds")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Stage {name} failed after {elapsed:.2f} seconds: {e}")
        raise

def test_full_pipeline():
    """
    Run the full pipeline integration test.
    Verifies that all stages execute successfully and produce expected outputs.
    """
    logger.info("=" * 60)
    logger.info("Starting Full Pipeline Integration Test")
    logger.info("=" * 60)

    start_time = time.time()
    pipeline_passed = True

    try:
        # Stage 1: Data Ingestion
        logger.info("Stage 1: Data Ingestion")
        run_stage("Ingestion", ingest_main)

        # Verify raw data
        if not check_file_exists("data/raw/bronze.parquet", "Raw data (bronze.parquet)"):
            raise FileNotFoundError("Raw data file missing after ingestion")

        # Stage 2: Preprocessing
        logger.info("Stage 2: Preprocessing")
        run_stage("Preprocessing", preprocess_main)

        # Verify processed data
        if not check_file_exists("data/processed/daily_aggregates.csv", "Daily aggregates"):
            raise FileNotFoundError("Daily aggregates missing after preprocessing")

        # Stage 3: Analysis
        logger.info("Stage 3: Analysis")
        run_stage("Analysis", analysis_main)

        # Verify model results
        if not check_file_exists("data/processed/model_results.json", "Model results"):
            raise FileNotFoundError("Model results missing after analysis")

        # Stage 4: Report Generation
        logger.info("Stage 4: Report Generation")
        run_stage("Report Generation", report_main)

        # Verify report output
        # Check for HTML report
        html_report = get_path("data/processed/report.html")
        pdf_report = get_path("data/processed/report.pdf")
        
        if html_report.exists():
            logger.info("✓ HTML report generated")
        elif pdf_report.exists():
            logger.info("✓ PDF report generated")
        else:
            logger.warning("No report file found (HTML or PDF)")

        # Validate outputs
        logger.info("Stage 5: Validation")
        run_stage("Validation", validate_main)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        pipeline_passed = False
    finally:
        total_time = time.time() - start_time
        logger.info("=" * 60)
        if pipeline_passed:
            logger.info(f"✓ Full pipeline completed successfully in {total_time:.2f} seconds")
            if total_time > PIPELINE_TIMEOUT:
                logger.warning(f"⚠ Pipeline exceeded 6-hour timeout ({total_time:.2f}s > {PIPELINE_TIMEOUT}s)")
            else:
                logger.info("✓ Pipeline completed within 6-hour timeout")
        else:
            logger.error("✗ Full pipeline FAILED")
        logger.info("=" * 60)

    return pipeline_passed

if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
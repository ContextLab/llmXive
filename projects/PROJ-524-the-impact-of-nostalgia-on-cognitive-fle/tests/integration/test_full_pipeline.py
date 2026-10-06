"""
Integration test for the full pipeline (T054).
Runs the entire pipeline from ingestion to final report generation on the simulation dataset
and asserts that all required JSON artifacts are created with non-null values.
"""
import os
import sys
import json
import subprocess
import logging
from pathlib import Path
import pytest

# Configure logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project root (parent of 'tests')
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# Expected output artifacts from the pipeline
REQUIRED_ARTIFACTS = {
    # From Ingestion (US1)
    "raw_dataset.csv": RAW_DIR / "raw_dataset.csv",
    "cleaned_dataset.csv": PROCESSED_DIR / "cleaned_dataset.csv",
    "cleaned_dataset_no_mmse.csv": PROCESSED_DIR / "cleaned_dataset_no_mmse.csv",
    "final_cleaned_dataset.csv": PROCESSED_DIR / "final_cleaned_dataset.csv",
    "exclusion_log.json": PROCESSED_DIR / "exclusion_log.json",
    "validity_metrics.json": PROCESSED_DIR / "validity_metrics.json",
    "mmse_flag.json": PROCESSED_DIR / "mmse_flag.json",
    "metadata.json": RAW_DIR / "metadata.json",
    "stimuli_checksums.json": DATA_DIR / "stimuli_checksums.json",
    
    # From Analysis (US2)
    "statistical_report.json": RESULTS_DIR / "statistical_report.json",
    "assumption_checks.json": RESULTS_DIR / "assumption_checks.json",
    
    # From Sensitivity (US3)
    "sensitivity_report.json": RESULTS_DIR / "sensitivity_report.json",
    "sensitivity_comparison.json": RESULTS_DIR / "sensitivity_comparison.json",
    "robustness_report.json": RESULTS_DIR / "robustness_report.json",
    "primary_analysis_report.json": RESULTS_DIR / "primary_analysis_report.json",
    "robustness_summary.md": RESULTS_DIR / "robustness_summary.md",
    
    # From Verification
    "citation_status.json": DATA_DIR / "citation_status.json",
}

def run_pipeline():
    """Executes the main pipeline script."""
    main_script = CODE_DIR / "main.py"
    if not main_script.exists():
        pytest.fail(f"Main pipeline script not found at {main_script}")
    
    logger.info(f"Running pipeline from {main_script}...")
    try:
        # Run as a subprocess to ensure a clean environment
        result = subprocess.run(
            [sys.executable, str(main_script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300 # 5 minutes timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Pipeline failed with return code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            pytest.fail(f"Pipeline execution failed: {result.stderr}")
        
        logger.info("Pipeline execution completed successfully.")
        return True
    except subprocess.TimeoutExpired:
        pytest.fail("Pipeline execution timed out.")
    except Exception as e:
        pytest.fail(f"Error running pipeline: {str(e)}")

def verify_artifacts():
    """Verifies that all required artifacts exist and contain non-null values."""
    missing_files = []
    empty_or_null_files = []
    
    for name, path in REQUIRED_ARTIFACTS.items():
        if not path.exists():
            missing_files.append(str(path))
            continue
        
        # Check content for JSON files
        if path.suffix == ".json":
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                # Check if the file is empty or contains only nulls
                if data is None:
                    empty_or_null_files.append(str(path))
                elif isinstance(data, dict) and len(data) == 0:
                    empty_or_null_files.append(str(path))
                elif isinstance(data, list) and len(data) == 0:
                    empty_or_null_files.append(str(path))
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON in {path}")
        
        # Check content for CSV files (non-empty)
        elif path.suffix == ".csv":
            if path.stat().st_size == 0:
                empty_or_null_files.append(str(path))
        
        # Check content for Markdown files (non-empty)
        elif path.suffix == ".md":
            if path.stat().st_size == 0:
                empty_or_null_files.append(str(path))

    if missing_files:
        pytest.fail(f"Missing required artifacts: {', '.join(missing_files)}")
    
    if empty_or_null_files:
        pytest.fail(f"Artifacts exist but are empty or contain only nulls: {', '.join(empty_or_null_files)}")

    logger.info("All required artifacts verified successfully.")

@pytest.fixture(scope="module", autouse=True)
def setup_and_run_pipeline():
    """Fixture to ensure pipeline runs before tests."""
    # Ensure data directories exist (T001)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "raw").mkdir(exist_ok=True)
    (DATA_DIR / "processed").mkdir(exist_ok=True)
    (DATA_DIR / "results").mkdir(exist_ok=True)
    (DATA_DIR / "stimuli").mkdir(exist_ok=True)
    
    # Run the pipeline
    run_pipeline()
    yield
    
def test_all_artifacts_created_and_populated():
    """Main test assertion: verify artifacts."""
    verify_artifacts()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
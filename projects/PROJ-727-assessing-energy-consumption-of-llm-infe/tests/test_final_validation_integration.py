"""
Integration Test for Final Validation (T035)

This test simulates the full pipeline execution context by creating
mock artifacts and verifying the validation script behaves correctly.
"""
import os
import csv
import tempfile
import shutil
from pathlib import Path
import subprocess
import sys
import pytest

# Test directories
TEST_ROOT = Path("tests/integration_tmp")
TEST_DATA_DIR = TEST_ROOT / "data" / "processed"
TEST_LOGS_DIR = TEST_ROOT / "logs"

def setup_module(module):
    """Create temporary directories."""
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEST_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def teardown_module(module):
    """Clean up temporary directories."""
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)

def create_mock_csv(filepath, rows=None):
    """Helper to create a mock CSV file."""
    if rows is None:
        rows = [
            {'model_id': 'model1', 'problem_id': '1', 'tokens_generated': '10', 
             'energy_kwh': '0.5', 'runtime_seconds': '1.0', 'pass_fail_status': '1'}
        ]
    
    with open(filepath, 'w', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        else:
            f.write("")

def create_mock_png(filepath):
    """Helper to create a mock PNG file (minimal valid header)."""
    with open(filepath, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + b'x' * 100)

def create_mock_log(filepath, content="Pipeline completed.\n"):
    """Helper to create a mock log file."""
    with open(filepath, 'w') as f:
        f.write(content)

@pytest.mark.integration
def test_validation_with_all_artifacts():
    """
    Integration test: Create all required artifacts and verify validation passes.
    """
    # Create all required files
    csv_path = TEST_DATA_DIR / "energy_results_aggregated.csv"
    create_mock_csv(csv_path)

    stats_path = TEST_DATA_DIR / "stats_report.csv"
    create_mock_csv(stats_path)

    bar_path = TEST_DATA_DIR / "energy_bar.png"
    create_mock_png(bar_path)

    scatter_path = TEST_DATA_DIR / "tradeoff_scatter.png"
    create_mock_png(scatter_path)

    duration_log = TEST_LOGS_DIR / "pipeline_duration.log"
    create_mock_log(duration_log)

    # We need to run the validation script with modified config paths
    # Since we can't easily patch the config in a subprocess, we will
    # rely on the fact that the test setup creates files in the expected
    # relative locations if we run from the project root.
    
    # Instead, let's test the logic by calling the module directly
    # with patched constants
    import code.final_validation as fv
    
    original_data = fv.DATA_PROCESSED_DIR
    original_logs = fv.LOGS_DIR
    
    fv.DATA_PROCESSED_DIR = str(TEST_DATA_DIR)
    fv.LOGS_DIR = str(TEST_LOGS_DIR)
    
    try:
        result = fv.main()
        assert result == 0, "Validation should pass when all artifacts exist"
    finally:
        fv.DATA_PROCESSED_DIR = original_data
        fv.LOGS_DIR = original_logs

@pytest.mark.integration
def test_validation_with_missing_csv():
    """
    Integration test: Missing CSV file should cause validation to fail.
    """
    # Create only images and logs
    bar_path = TEST_DATA_DIR / "energy_bar.png"
    create_mock_png(bar_path)

    scatter_path = TEST_DATA_DIR / "tradeoff_scatter.png"
    create_mock_png(scatter_path)

    duration_log = TEST_LOGS_DIR / "pipeline_duration.log"
    create_mock_log(duration_log)

    # Import and patch
    import code.final_validation as fv
    
    original_data = fv.DATA_PROCESSED_DIR
    original_logs = fv.LOGS_DIR
    
    fv.DATA_PROCESSED_DIR = str(TEST_DATA_DIR)
    fv.LOGS_DIR = str(TEST_LOGS_DIR)
    
    try:
        result = fv.main()
        assert result == 1, "Validation should fail when CSV is missing"
    finally:
        fv.DATA_PROCESSED_DIR = original_data
        fv.LOGS_DIR = original_logs

@pytest.mark.integration
def test_validation_with_empty_csv():
    """
    Integration test: Empty CSV file should cause validation to fail.
    """
    # Create empty CSV
    csv_path = TEST_DATA_DIR / "energy_results_aggregated.csv"
    create_mock_csv(csv_path, rows=[])

    # Create other files
    stats_path = TEST_DATA_DIR / "stats_report.csv"
    create_mock_csv(stats_path)

    bar_path = TEST_DATA_DIR / "energy_bar.png"
    create_mock_png(bar_path)

    scatter_path = TEST_DATA_DIR / "tradeoff_scatter.png"
    create_mock_png(scatter_path)

    duration_log = TEST_LOGS_DIR / "pipeline_duration.log"
    create_mock_log(duration_log)

    # Import and patch
    import code.final_validation as fv
    
    original_data = fv.DATA_PROCESSED_DIR
    original_logs = fv.LOGS_DIR
    
    fv.DATA_PROCESSED_DIR = str(TEST_DATA_DIR)
    fv.LOGS_DIR = str(TEST_LOGS_DIR)
    
    try:
        result = fv.main()
        assert result == 1, "Validation should fail when CSV is empty"
    finally:
        fv.DATA_PROCESSED_DIR = original_data
        fv.LOGS_DIR = original_logs
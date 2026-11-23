"""
Contract tests for the data ingestion output schema (T012).

Verifies that code/01_ingest.py produces the expected output files
and that the data adheres to the schema defined in T007a.
"""
import os
import json
import pandas as pd
import pytest
from pathlib import Path

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

@pytest.fixture
def ingest_script():
    return PROJECT_ROOT / "code" / "01_ingest.py"

def test_ingest_script_exists(ingest_script):
    """Test that the ingestion script exists."""
    assert ingest_script.exists(), "code/01_ingest.py not found"

def test_ingest_produces_merged_csv(ingest_script):
    """
    Test that running the ingestion script produces the merged CSV.
    This is a contract test for the output file existence.
    """
    # Note: We assume the script has been run or will be run by the test runner.
    # In a real CI, this might be an integration test that runs the script.
    # Here we check if the file exists as a result of a previous run.
    output_path = DATA_PROCESSED_DIR / "merged_dataset.csv"
    
    # If the file doesn't exist, we can't validate it yet.
    # In a real test suite, we would run: subprocess.run(["python", str(ingest_script)])
    # For now, we assert existence as a contract.
    assert output_path.exists(), f"Expected output file {output_path} not found. Run code/01_ingest.py first."

def test_merged_csv_schema():
    """
    Contract test for the schema of merged_dataset.csv.
    Verifies required columns and data types.
    """
    output_path = DATA_PROCESSED_DIR / "merged_dataset.csv"
    if not output_path.exists():
        pytest.skip("Output file not found. Run code/01_ingest.py first.")
    
    df = pd.read_csv(output_path)
    
    # Required columns from T007a schema
    required_cols = ["sample_id", "temperature", "light_intensity", "co2_level"]
    
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check numeric types
    assert pd.api.types.is_numeric_dtype(df["temperature"]), "temperature must be numeric"
    assert pd.api.types.is_numeric_dtype(df["light_intensity"]), "light_intensity must be numeric"
    assert pd.api.types.is_numeric_dtype(df["co2_level"]), "co2_level must be numeric"
    
    # Check row count (T012 requires >= 50 samples)
    assert len(df) >= 50, f"Dataset has {len(df)} samples, expected >= 50"

def test_validation_report_exists():
    """Test that the validation report JSON is produced."""
    report_path = DATA_RESULTS_DIR / "data_validation_report.json"
    assert report_path.exists(), f"Validation report {report_path} not found."

def test_validation_report_schema():
    """Test the schema of the validation report."""
    report_path = DATA_RESULTS_DIR / "data_validation_report.json"
    if not report_path.exists():
        pytest.skip("Validation report not found.")
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    required_keys = ["total_samples", "excluded_samples", "validation_status"]
    for key in required_keys:
        assert key in report, f"Missing key in validation report: {key}"
    
    assert report["validation_status"] == "passed", "Validation status should be 'passed'"
    assert report["total_samples"] >= 50, "Report should indicate >= 50 samples"

def test_query_log_exists():
    """Test that the query log is produced."""
    log_path = DATA_RAW_DIR / "query_log.json"
    assert log_path.exists(), f"Query log {log_path} not found."
"""
Tests for ingestion module, specifically T017 data gap validation.
"""
import os
import json
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import validate_data_gap, generate_data_availability_report, DATA_RAW_DIR, DATA_REPORTS_DIR, MIN_VALID_ENTRIES

@pytest.fixture
def temp_data_dirs():
    """Create temporary directories for test data."""
    temp_root = tempfile.mkdtemp()
    original_raw = DATA_RAW_DIR
    original_reports = DATA_REPORTS_DIR
    
    # Monkey patch global constants to use temp dirs
    DATA_RAW_DIR = Path(temp_root) / "raw"
    DATA_REPORTS_DIR = Path(temp_root) / "reports"
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    yield {
        "root": temp_root,
        "raw": DATA_RAW_DIR,
        "reports": DATA_REPORTS_DIR
    }
    
    # Cleanup
    shutil.rmtree(temp_root)

def test_validate_data_gap_insufficient_data(temp_data_dirs):
    """
    Test that validate_data_gap returns False and generates a report when N < 30.
    """
    # Create a small sample dataset (29 rows)
    # We need to mock the combined_raw.csv creation
    small_df = pd.DataFrame({
        'composition': [f'Al2O3_{i}' for i in range(29)],
        'weibull_modulus': [10.0 + i for i in range(29)],
        'sample_count': [50] * 29,
        'primary_anion_cation_group': ['O-Al'] * 29
    })
    
    combined_path = temp_data_dirs['raw'] / "combined_raw.csv"
    small_df.to_csv(combined_path, index=False)
    
    # Temporarily override the global constants in the module
    import ingestion
    ingestion.DATA_RAW_DIR = temp_data_dirs['raw']
    ingestion.DATA_REPORTS_DIR = temp_data_dirs['reports']
    ingestion.MIN_VALID_ENTRIES = 30

    try:
        passed, df = ingestion.validate_data_gap()
        
        assert passed is False, "Expected validation to fail for N < 30"
        assert df.empty, "Expected empty DataFrame on failure"
        
        # Check report generation
        report_path = temp_data_dirs['reports'] / "data_availability_report.json"
        assert report_path.exists(), "Data Availability Report should be generated"
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report['status'] == 'HALTED'
        assert report['actual_count'] == 29
        assert report['threshold'] == 30
        
    finally:
        # Restore original constants
        ingestion.DATA_RAW_DIR = Path("data/raw")
        ingestion.DATA_REPORTS_DIR = Path("data/reports")
        ingestion.MIN_VALID_ENTRIES = 30

def test_validate_data_gap_sufficient_data(temp_data_dirs):
    """
    Test that validate_data_gap returns True when N >= 30.
    """
    # Create a sufficient sample dataset (35 rows)
    large_df = pd.DataFrame({
        'composition': [f'Al2O3_{i}' for i in range(35)],
        'weibull_modulus': [10.0 + i for i in range(35)],
        'sample_count': [50] * 35,
        'primary_anion_cation_group': ['O-Al'] * 35
    })
    
    combined_path = temp_data_dirs['raw'] / "combined_raw.csv"
    large_df.to_csv(combined_path, index=False)
    
    import ingestion
    ingestion.DATA_RAW_DIR = temp_data_dirs['raw']
    ingestion.DATA_REPORTS_DIR = temp_data_dirs['reports']
    ingestion.MIN_VALID_ENTRIES = 30

    try:
        passed, df = ingestion.validate_data_gap()
        
        assert passed is True, "Expected validation to pass for N >= 30"
        assert len(df) == 35, "Expected DataFrame with 35 rows"
        
        # Check that report was NOT generated
        report_path = temp_data_dirs['reports'] / "data_availability_report.json"
        assert not report_path.exists(), "Data Availability Report should NOT be generated on success"
        
    finally:
        ingestion.DATA_RAW_DIR = Path("data/raw")
        ingestion.DATA_REPORTS_DIR = Path("data/reports")
        ingestion.MIN_VALID_ENTRIES = 30

def test_generate_data_availability_report_structure(temp_data_dirs):
    """
    Test the structure of the generated report.
    """
    test_df = pd.DataFrame({
        'composition': ['Al2O3'],
        'weibull_modulus': [10.0],
        'primary_anion_cation_group': ['O-Al']
    })
    
    ingestion.DATA_REPORTS_DIR = temp_data_dirs['reports']
    ingestion.generate_data_availability_report(25, test_df)
    
    report_path = temp_data_dirs['reports'] / "data_availability_report.json"
    assert report_path.exists()
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    required_keys = ['status', 'reason', 'threshold', 'actual_count', 'missing_count', 'timestamp']
    for key in required_keys:
        assert key in report, f"Report missing key: {key}"
    
    assert report['status'] == 'HALTED'
    assert report['reason'] == 'Insufficient data'
    assert report['actual_count'] == 25
    assert report['threshold'] == 30
    assert report['missing_count'] == 5

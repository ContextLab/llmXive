"""
Integration test for T023: HRV Metrics Output.

Verifies that code/02_preprocess_hrv.py produces a valid CSV at 
data/derived/hrv_metrics.csv with the correct schema.
"""
import os
import sys
import pandas as pd
import pytest
from pathlib import Path

# Add code directory to path
ROOT_DIR = Path(__file__).resolve().parent.parent
CODE_DIR = ROOT_DIR / "code"
sys.path.insert(0, str(CODE_DIR))

@pytest.fixture
def output_file_path():
    return ROOT_DIR / "data" / "derived" / "hrv_metrics.csv"

def test_hrv_output_csv_exists(output_file_path):
    """Test that the output CSV file exists."""
    assert output_file_path.exists(), f"Output file {output_file_path} does not exist."

def test_hrv_output_schema(output_file_path):
    """Test that the CSV has the required columns."""
    df = pd.read_csv(output_file_path)
    required_columns = ['subject_id', 'phase', 'RMSSD', 'SDNN']
    assert list(df.columns) == required_columns, \
        f"Columns mismatch: expected {required_columns}, got {list(df.columns)}"

def test_hrv_output_no_nans(output_file_path):
    """Test that numeric columns do not contain NaNs."""
    df = pd.read_csv(output_file_path)
    assert df['RMSSD'].isna().sum() == 0, "RMSSD column contains NaNs."
    assert df['SDNN'].isna().sum() == 0, "SDNN column contains NaNs."

def test_hrv_output_phases(output_file_path):
    """Test that only valid phases are present."""
    df = pd.read_csv(output_file_path)
    valid_phases = ['Baseline', 'Stress']
    assert df['phase'].isin(valid_phases).all(), \
        f"Invalid phases found: {df['phase'].unique()}"

def test_hrv_output_positive_values(output_file_path):
    """Test that HRV metrics are positive."""
    df = pd.read_csv(output_file_path)
    assert (df['RMSSD'] > 0).all(), "RMSSD contains non-positive values."
    assert (df['SDNN'] > 0).all(), "SDNN contains non-positive values."

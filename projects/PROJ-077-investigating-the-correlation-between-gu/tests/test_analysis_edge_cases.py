import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the functions we are testing
# Assuming the module is accessible as 'analysis' or relative import
# For this test file, we assume it's run from the project root
import sys
sys.path.insert(0, 'code')
from analysis import check_zero_variance, log_zero_variance_warning

@pytest.fixture
def temp_output_dir(tmp_path):
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    return str(processed_dir)

def test_check_zero_variance_true():
    """Test that zero variance is detected."""
    df = pd.DataFrame({
        'fluid_intelligence': [5.0, 5.0, 5.0, 5.0]
    })
    assert check_zero_variance(df, 'fluid_intelligence') is True

def test_check_zero_variance_false():
    """Test that non-zero variance is detected."""
    df = pd.DataFrame({
        'fluid_intelligence': [4.0, 5.0, 6.0, 7.0]
    })
    assert check_zero_variance(df, 'fluid_intelligence') is False

def test_check_zero_variance_all_nan():
    """Test that all NaN is treated as zero variance."""
    df = pd.DataFrame({
        'fluid_intelligence': [np.nan, np.nan, np.nan]
    })
    assert check_zero_variance(df, 'fluid_intelligence') is True

def test_log_zero_variance_warning_creates_file(temp_output_dir):
    """Test that the warning log file is created and contains the message."""
    output_path = os.path.join(temp_output_dir, "analysis_warnings.log")
    
    # Call the function
    log_zero_variance_warning('fluid_intelligence', output_path)
    
    # Verify file exists
    assert os.path.exists(output_path)
    
    # Verify content
    with open(output_path, 'r') as f:
        content = f.read()
    
    assert "Warning: Zero variance in fluid_intelligence; skipping correlation." in content

def test_log_zero_variance_warning_appends(temp_output_dir):
    """Test that the warning is appended if file exists."""
    output_path = os.path.join(temp_output_dir, "analysis_warnings.log")
    
    # Write initial content
    with open(output_path, 'w') as f:
        f.write("Initial log\n")
    
    # Call the function
    log_zero_variance_warning('fluid_intelligence', output_path)
    
    # Verify content
    with open(output_path, 'r') as f:
        content = f.read()
    
    assert "Initial log" in content
    assert "Warning: Zero variance in fluid_intelligence; skipping correlation." in content
import pytest
import pandas as pd
import os
from pathlib import Path
import tempfile
import yaml

from code.plot_sensitivity_curve import (
    load_sensitivity_results,
    check_classification_status,
    generate_sensitivity_curve,
    generate_n_a_plot
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_sensitivity_results_missing_file(temp_dir):
    """Test that load_sensitivity_results returns None when file is missing."""
    # Change to temp directory to avoid side effects
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        result = load_sensitivity_results()
        assert result is None
    finally:
        os.chdir(original_cwd)

def test_load_sensitivity_results_valid_file(temp_dir):
    """Test loading valid sensitivity results."""
    # Create test data
    df = pd.DataFrame({
        'threshold': [0.1, 0.2, 0.3],
        'FPR': [0.05, 0.1, 0.15],
        'FNR': [0.2, 0.15, 0.1]
    })
    
    # Write to expected location
    output_dir = temp_dir / "results"
    output_dir.mkdir()
    data_dir = output_dir / "sensitivity_fpr_fnr.csv"
    df.to_csv(data_dir, index=False)
    
    # Change to temp directory
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        result = load_sensitivity_results()
        assert result is not None
        assert len(result) == 3
        assert 'threshold' in result.columns
        assert 'FPR' in result.columns
        assert 'FNR' in result.columns
    finally:
        os.chdir(original_cwd)

def test_check_classification_status_missing_file(temp_dir):
    """Test status check when file is missing."""
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        status = check_classification_status()
        assert status == "SKIPPED"
    finally:
        os.chdir(original_cwd)

def test_check_classification_status_valid_file(temp_dir):
    """Test status check with valid file."""
    # Create state directory and file
    state_dir = temp_dir / "state"
    state_dir.mkdir()
    status_file = state_dir / "classification_status.yaml"
    
    with open(status_file, 'w') as f:
        yaml.dump({'status': 'RUNNING'}, f)
    
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        status = check_classification_status()
        assert status == "RUNNING"
    finally:
        os.chdir(original_cwd)

def test_generate_sensitivity_curve_creates_file(temp_dir):
    """Test that sensitivity curve plot is generated correctly."""
    # Create test data
    df = pd.DataFrame({
        'threshold': [0.1, 0.2, 0.3, 0.4, 0.5],
        'FPR': [0.05, 0.1, 0.15, 0.2, 0.25],
        'FNR': [0.3, 0.2, 0.15, 0.1, 0.05]
    })
    
    output_dir = temp_dir / "results" / "figures"
    output_dir.mkdir(parents=True)
    output_path = output_dir / "sensitivity_curve.png"
    
    generate_sensitivity_curve(df, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_generate_n_a_plot_creates_file(temp_dir):
    """Test that N/A plot is generated correctly."""
    output_dir = temp_dir / "results" / "figures"
    output_dir.mkdir(parents=True)
    output_path = output_dir / "sensitivity_curve.png"
    
    generate_n_a_plot(output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0
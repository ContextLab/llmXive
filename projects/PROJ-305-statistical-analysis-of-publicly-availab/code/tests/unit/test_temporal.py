import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Import the function to test
from src.analysis.temporal import (
    load_signals, 
    identify_top_signals, 
    generate_empty_signal_warning, 
    run_temporal_preparation
)

@pytest.fixture
def sample_signals_with_data():
    """Create a sample signals DataFrame with valid data."""
    data = {
        'soc': ['SOC_1', 'SOC_2', 'SOC_3', 'SOC_4'],
        'ror': [3.0, 2.5, 1.2, 4.0],
        'ror_ci_lower': [1.5, 1.1, 0.8, 2.0],
        'ror_ci_upper': [6.0, 5.0, 1.8, 8.0],
        'prr': [2.8, 2.2, 1.1, 3.5],
        'prr_ci_lower': [1.4, 1.0, 0.7, 1.9],
        'prr_ci_upper': [5.6, 4.4, 1.5, 6.5],
        'ic': [1.5, 1.2, 0.1, 1.8],
        'ic_ci_lower': [0.5, 0.2, -0.2, 0.9],
        'ic_ci_upper': [2.5, 2.2, 0.4, 2.7],
        'p_adj': [0.01, 0.02, 0.45, 0.005],
        'signal_flag': [True, True, False, True] # SOC_3 is not a signal
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_signals_no_signals():
    """Create a sample signals DataFrame with no signals meeting threshold."""
    data = {
        'soc': ['SOC_1', 'SOC_2'],
        'ror': [1.1, 1.2],
        'ror_ci_lower': [0.5, 0.6],
        'ror_ci_upper': [2.0, 2.2],
        'prr': [1.0, 1.1],
        'prr_ci_lower': [0.5, 0.6],
        'prr_ci_upper': [1.5, 1.6],
        'ic': [0.1, 0.2],
        'ic_ci_lower': [-0.5, -0.4],
        'ic_ci_upper': [0.7, 0.8],
        'p_adj': [0.5, 0.4],
        'signal_flag': [False, False]
    }
    return pd.DataFrame(data)

def test_load_signals_valid_file(sample_signals_with_data, tmp_path):
    """Test loading signals from a valid CSV file."""
    file_path = tmp_path / "signals.csv"
    sample_signals_with_data.to_csv(file_path, index=False)
    
    loaded_df = load_signals(str(file_path))
    assert len(loaded_df) == len(sample_signals_with_data)
    assert 'soc' in loaded_df.columns
    assert 'signal_flag' in loaded_df.columns

def test_load_signals_missing_file(tmp_path):
    """Test that load_signals raises FileNotFoundError for missing file."""
    non_existent_path = tmp_path / "non_existent.csv"
    with pytest.raises(FileNotFoundError):
        load_signals(str(non_existent_path))

def test_identify_top_signals_basic(sample_signals_with_data):
    """Test basic identification of top signals."""
    top = identify_top_signals(sample_signals_with_data, top_n=2)
    
    assert len(top) == 2
    # SOC_4 (ROR 4.0) and SOC_1 (ROR 3.0) should be top 2
    # SOC_3 is excluded because signal_flag is False
    socs = [s['soc'] for s in top]
    assert 'SOC_4' in socs
    assert 'SOC_1' in socs
    assert 'SOC_3' not in socs # Not a signal
    assert 'SOC_2' not in socs # Lower ROR than SOC_1

def test_identify_top_signals_fewer_than_n(sample_signals_with_data):
    """Test when fewer than N signals exist."""
    # Only 3 signals exist in fixture
    top = identify_top_signals(sample_signals_with_data, top_n=10)
    assert len(top) == 3 # Returns all available signals

def test_identify_top_signals_no_signals(sample_signals_no_signals):
    """Test when no signals meet the threshold."""
    top = identify_top_signals(sample_signals_no_signals, top_n=5)
    assert len(top) == 0

def test_generate_empty_signal_warning(tmp_path):
    """Test generation of empty signal warning file."""
    output_dir = str(tmp_path)
    result_path = generate_empty_signal_warning(output_dir)
    
    assert os.path.exists(result_path)
    with open(result_path, 'r') as f:
        content = f.read()
        assert "WARNING" in content
        assert "No candidate SOCs" in content

def test_run_temporal_preparation_no_signals(sample_signals_no_signals, tmp_path):
    """Test run_temporal_preparation when no signals exist."""
    signals_path = tmp_path / "signals.csv"
    output_dir = tmp_path / "output"
    signals_path.mkdir(parents=True)
    sample_signals_no_signals.to_csv(signals_path, index=False)
    
    result_socs = run_temporal_preparation(
        signals_input=str(signals_path),
        output_dir=str(output_dir),
        top_n=5
    )
    
    assert result_socs == []
    # Check that warning file was created
    warning_file = output_dir / "empty_signal_warning.txt"
    assert warning_file.exists()

def test_run_temporal_preparation_success(sample_signals_with_data, tmp_path):
    """Test successful run with signals."""
    signals_path = tmp_path / "signals.csv"
    output_dir = tmp_path / "output"
    sample_signals_with_data.to_csv(signals_path, index=False)
    
    result_socs = run_temporal_preparation(
        signals_input=str(signals_path),
        output_dir=str(output_dir),
        top_n=2
    )
    
    assert len(result_socs) == 2
    assert 'SOC_4' in result_socs
    assert 'SOC_1' in result_socs
    
    # Check manifest file
    manifest = output_dir / "selected_soc_manifest.csv"
    assert manifest.exists()
    
    manifest_df = pd.read_csv(manifest)
    assert len(manifest_df) == 2
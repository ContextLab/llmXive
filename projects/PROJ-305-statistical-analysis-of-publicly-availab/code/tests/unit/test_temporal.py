import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the module under test
# Note: The project structure uses code/ as the root for source, 
# but imports are relative to code/src.
# We need to ensure the path is set correctly for the import to work.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.analysis.temporal import (
    load_signals, 
    identify_top_signals, 
    generate_empty_signal_warning, 
    run_temporal_preparation
)

# Fixtures and sample data
@pytest.fixture
def sample_signals_with_data():
    """Create a temporary signals.csv file with valid data."""
    data = {
        'soc': ['SOC001', 'SOC002', 'SOC003', 'SOC004', 'SOC005', 'SOC006'],
        'ror': [3.5, 2.8, 1.9, 4.1, 2.2, 1.5],
        'ror_ci_lower': [1.2, 1.1, 0.8, 2.0, 1.0, 0.5],
        'ror_ci_upper': [5.8, 4.5, 3.0, 6.2, 3.4, 2.5],
        'prr': [2.1, 1.8, 1.2, 2.5, 1.6, 0.9],
        'prr_ci_lower': [1.1, 1.0, 0.6, 1.2, 0.9, 0.4],
        'prr_ci_upper': [3.1, 2.6, 1.8, 3.8, 2.3, 1.4],
        'ic': [0.8, 0.6, 0.2, 1.1, 0.5, -0.2],
        'ic_ci_lower': [0.1, 0.0, -0.5, 0.4, -0.1, -0.9],
        'ic_ci_upper': [1.5, 1.2, 0.9, 1.8, 1.1, 0.5],
        'p_adj': [0.01, 0.03, 0.15, 0.005, 0.08, 0.25],
        'signal_flag': [True, True, False, True, True, False]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        return f.name

@pytest.fixture
def sample_signals_no_signals():
    """Create a temporary signals.csv file with no signals flagged."""
    data = {
        'soc': ['SOC001', 'SOC002'],
        'ror': [1.1, 1.2],
        'ror_ci_lower': [0.8, 0.9],
        'ror_ci_upper': [1.4, 1.5],
        'prr': [1.0, 1.1],
        'prr_ci_lower': [0.7, 0.8],
        'prr_ci_upper': [1.3, 1.4],
        'ic': [0.1, 0.2],
        'ic_ci_lower': [-0.2, -0.1],
        'ic_ci_upper': [0.4, 0.5],
        'p_adj': [0.5, 0.6],
        'signal_flag': [False, False]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        return f.name

def test_load_signals_valid_file(sample_signals_with_data):
    """Test loading signals from a valid CSV file."""
    signals = load_signals(sample_signals_with_data)
    assert signals is not None
    assert len(signals) == 6
    assert 'soc' in signals.columns
    assert 'signal_flag' in signals.columns
    assert signals['signal_flag'].sum() == 4  # 4 signals flagged

def test_load_signals_missing_file():
    """Test loading signals from a non-existent file raises an error."""
    with pytest.raises(FileNotFoundError):
        load_signals('/non/existent/path/signals.csv')

def test_identify_top_signals_basic(sample_signals_with_data):
    """Test identifying top N signals when N is available."""
    signals = load_signals(sample_signals_with_data)
    top_signals, top_indices = identify_top_signals(signals, n=3)
    
    assert len(top_signals) == 3
    assert len(top_indices) == 3
    # Verify they are the top 3 by signal_flag and then by ROR
    # Expected top 3 based on data: SOC004 (ROR 4.1), SOC001 (ROR 3.5), SOC002 (ROR 2.8)
    assert top_signals['soc'].iloc[0] == 'SOC004'
    assert top_signals['soc'].iloc[1] == 'SOC001'
    assert top_signals['soc'].iloc[2] == 'SOC002'

def test_identify_top_signals_fewer_than_n(sample_signals_with_data):
    """Test identifying top N signals when fewer than N are available."""
    signals = load_signals(sample_signals_with_data)
    # Only 4 signals are flagged, request 10
    top_signals, top_indices = identify_top_signals(signals, n=10)
    
    assert len(top_signals) == 4
    assert len(top_indices) == 4

def test_identify_top_signals_no_signals(sample_signals_no_signals):
    """Test identifying top N signals when no signals are flagged."""
    signals = load_signals(sample_signals_no_signals)
    top_signals, top_indices = identify_top_signals(signals, n=5)
    
    assert len(top_signals) == 0
    assert len(top_indices) == 0

def test_generate_empty_signal_warning(tmp_path):
    """Test generating an empty signal warning file."""
    output_dir = tmp_path / "temporal_profiles"
    output_dir.mkdir()
    
    warning_file = generate_empty_signal_warning(str(output_dir))
    
    assert warning_file.exists()
    content = warning_file.read_text()
    assert "No signals found" in content
    assert "temporal analysis" in content.lower()

def test_run_temporal_preparation_no_signals(sample_signals_no_signals, tmp_path):
    """Test run_temporal_preparation when no signals are found."""
    output_dir = tmp_path / "temporal_profiles"
    output_dir.mkdir()
    
    result = run_temporal_preparation(sample_signals_no_signals, str(output_dir))
    
    assert result is False
    assert (output_dir / "empty_signal_warning.txt").exists()

def test_run_temporal_preparation_success(sample_signals_with_data, tmp_path):
    """Test run_temporal_preparation with valid signals."""
    output_dir = tmp_path / "temporal_profiles"
    output_dir.mkdir()
    
    # Note: This test verifies the preparation logic (loading and identifying top signals).
    # The actual plotting (T033/T034) is not performed here as it requires cleaned data
    # which is not provided in this unit test scope. The function returns True if
    # top signals are identified successfully.
    result = run_temporal_preparation(sample_signals_with_data, str(output_dir))
    
    # Since we have signals, it should return True
    assert result is True
    # The warning file should NOT exist
    assert not (output_dir / "empty_signal_warning.txt").exists()
"""
Unit tests for visualization generation.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.visualizer import plot_completion_time, plot_error_count, plot_sus_score

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with usability metrics."""
    np.random.seed(42)
    n = 50
    data = {
        'participant_id': [f'P{i:03d}' for i in range(n)],
        'interface_type': ['Traditional'] * (n // 2) + ['Explainable'] * (n // 2),
        'completion_time': np.random.uniform(10, 100, n),
        'error_count': np.random.poisson(2, n),
        'sus_score': np.random.uniform(20, 100, n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    return tmp_path

def test_plot_completion_time_creates_file(sample_df, temp_output_dir):
    """Test that completion time plot is created and is a valid PNG."""
    output_path = temp_output_dir / "completion_time.png"
    result_path = plot_completion_time(sample_df, str(output_path))
    
    assert os.path.exists(result_path), "Output file was not created"
    assert os.path.getsize(result_path) > 0, "Output file is empty"
    
    # Verify it's a valid PNG by checking header
    with open(result_path, 'rb') as f:
        header = f.read(8)
        assert header[:8] == b'\x89PNG\r\n\x1a\n', "Invalid PNG header"

def test_plot_error_count_creates_file(sample_df, temp_output_dir):
    """Test that error count plot is created and is a valid PNG."""
    output_path = temp_output_dir / "error_count.png"
    result_path = plot_error_count(sample_df, str(output_path))
    
    assert os.path.exists(result_path), "Output file was not created"
    assert os.path.getsize(result_path) > 0, "Output file is empty"
    
    # Verify it's a valid PNG by checking header
    with open(result_path, 'rb') as f:
        header = f.read(8)
        assert header[:8] == b'\x89PNG\r\n\x1a\n', "Invalid PNG header"

def test_plot_sus_score_creates_file(sample_df, temp_output_dir):
    """Test that SUS score plot is created and is a valid PNG."""
    output_path = temp_output_dir / "sus_score.png"
    result_path = plot_sus_score(sample_df, str(output_path))
    
    assert os.path.exists(result_path), "Output file was not created"
    assert os.path.getsize(result_path) > 0, "Output file is empty"
    
    # Verify it's a valid PNG by checking header
    with open(result_path, 'rb') as f:
        header = f.read(8)
        assert header[:8] == b'\x89PNG\r\n\x1a\n', "Invalid PNG header"
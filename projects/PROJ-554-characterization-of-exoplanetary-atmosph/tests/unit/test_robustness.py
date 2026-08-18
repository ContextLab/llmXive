import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from robustness import load_retrieval_results, compute_ci_width, determine_threshold_met, save_robustness_report

def test_load_retrieval_results_missing_file(tmp_path):
    """Test that FileNotFoundError is raised if the retrieval results file is missing."""
    # Create a config dict with a non-existent path
    config = {
        'paths': {
            'processed': str(tmp_path)
        }
    }
    
    with pytest.raises(FileNotFoundError):
        load_retrieval_results(config)

def test_load_retrieval_results_missing_columns(tmp_path):
    """Test that ValueError is raised if required columns are missing."""
    # Create a dummy CSV with missing columns
    csv_path = tmp_path / 'retrieval_results.csv'
    df = pd.DataFrame({
        'planet_name': ['A'],
        'other_col': [1.0]
    })
    df.to_csv(csv_path, index=False)
    
    config = {
        'paths': {
            'processed': str(tmp_path)
        }
    }
    
    with pytest.raises(ValueError):
        load_retrieval_results(config)

def test_determine_threshold_met():
    """Test the threshold logic."""
    assert determine_threshold_met(0.15) is True
    assert determine_threshold_met(0.20) is True
    assert determine_threshold_met(0.21) is False
    assert determine_threshold_met(0.0) is True

def test_save_robustness_report(tmp_path):
    """Test saving the robustness report."""
    output_path = tmp_path / 'test_robustness.json'
    save_robustness_report(0.15, True, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['ci_width'] == 0.15
    assert data['threshold_met'] is True
    assert data['threshold_value'] == 0.2
"""
Unit tests for compare_methods.py logic.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Import the function to test
from code.compare_methods import compare_methods, compute_relative_error
from code.config import Config

def test_compute_relative_error():
    assert compute_relative_error(10.0, 10.0) == 0.0
    assert compute_relative_error(10.0, 11.0) == 0.1
    assert compute_relative_error(10.0, 9.0) == 0.1
    assert compute_relative_error(10.0, 15.0) == 0.5
    # Zero case
    assert compute_relative_error(0.0, 0.0) == 0.0
    assert compute_relative_error(0.0, 1.0) == float('inf')

@pytest.fixture
def mock_config():
    """Mock config with required attributes."""
    cfg = MagicMock(spec=Config)
    cfg.NUM_REALIZATIONS = 100
    cfg.MIN_L_FOR_TM = 400
    cfg.AGREEMENT_THRESHOLD = 0.10
    cfg.MIN_AGREEMENT_FRACTION = 0.80
    cfg.SCALING_FITS_PATH = Path("dummy_pr.json")
    cfg.LYAPUNOV_EXPONENTS_PATH = Path("dummy_tm.json")
    cfg.METHOD_AGREEMENT_PATH = Path("dummy_report.json")
    return cfg

def test_compare_methods_no_matches(mock_config):
    """Test when no realizations match."""
    pr_data = [
        {"W": 0.5, "L": 200, "realization_index": 0, "xi": 10.0} # L < 400
    ]
    tm_data = [
        {"W": 0.5, "L": 400, "realization_index": 0, "xi": 10.0}
    ]
    
    with patch('code.compare_methods.load_scaling_fits', return_value=pr_data), \
         patch('code.compare_methods.load_lyapunov_exponents', return_value=tm_data), \
         patch('code.compare_methods.get_config', return_value=mock_config):
         
         result = compare_methods()
         
         assert result["status"] == "failed"
         assert "No matching realizations" in result["reason"]

def test_compare_methods_pass(mock_config):
    """Test when agreement is high enough."""
    # Create 100 matches, 90 agreed, 10 disagreed
    pr_data = []
    tm_data = []
    
    for i in range(100):
        pr_data.append({"W": 1.0, "L": 400, "realization_index": i, "xi": 10.0})
        # 90% agree (error 0), 10% disagree (error 0.2)
        if i < 90:
            tm_data.append({"W": 1.0, "L": 400, "realization_index": i, "xi": 10.0})
        else:
            tm_data.append({"W": 1.0, "L": 400, "realization_index": i, "xi": 12.0}) # 20% error
    
    with patch('code.compare_methods.load_scaling_fits', return_value=pr_data), \
         patch('code.compare_methods.load_lyapunov_exponents', return_value=tm_data), \
         patch('code.compare_methods.get_config', return_value=mock_config):
         
         result = compare_methods()
         
         assert result["status"] == "passed"
         assert result["agreed_count"] == 90
         assert result["agreement_fraction"] == 0.90

def test_compare_methods_fail(mock_config):
    """Test when agreement is too low."""
    # 50% agree
    pr_data = []
    tm_data = []
    
    for i in range(100):
        pr_data.append({"W": 1.0, "L": 400, "realization_index": i, "xi": 10.0})
        if i < 50:
            tm_data.append({"W": 1.0, "L": 400, "realization_index": i, "xi": 10.0})
        else:
            tm_data.append({"W": 1.0, "L": 400, "realization_index": i, "xi": 15.0}) # 50% error
    
    with patch('code.compare_methods.load_scaling_fits', return_value=pr_data), \
         patch('code.compare_methods.load_lyapunov_exponents', return_value=tm_data), \
         patch('code.compare_methods.get_config', return_value=mock_config):
         
         result = compare_methods()
         
         assert result["status"] == "failed"
         assert result["agreement_fraction"] == 0.50
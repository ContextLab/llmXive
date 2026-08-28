"""
Unit tests for sensitivity_analysis.py
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.sensitivity_analysis import (
    run_group_analysis_on_betas,
    SMOOTHING_KERNELS
)

def test_run_group_analysis_on_betas():
    """Test the t-test logic with known values."""
    # Mock data: Excluded (low), Included (high)
    betas = [
        {'group': 'excluded', 'beta': 1.0},
        {'group': 'excluded', 'beta': 1.1},
        {'group': 'included', 'beta': 2.0},
        {'group': 'included', 'beta': 2.1},
    ]
    
    result = run_group_analysis_on_betas(betas, 6.0)
    
    assert result['n_excluded'] == 2
    assert result['n_included'] == 2
    assert result['t_stat'] is not None
    assert result['p_value'] is not None
    assert result['cohens_d'] is not None
    # Check direction (excluded < included => negative difference)
    assert result['mean_excluded'] < result['mean_included']

def test_run_group_analysis_insufficient_data():
    """Test behavior with insufficient data."""
    betas = [
        {'group': 'excluded', 'beta': 1.0},
    ]
    
    result = run_group_analysis_on_betas(betas, 6.0)
    
    assert result['t_stat'] is None
    assert result['p_value'] is None
    assert result['cohens_d'] is None

def test_smoothing_kernels_defined():
    """Ensure the smoothing kernels list is defined."""
    assert isinstance(SMOOTHING_KERNELS, list)
    assert len(SMOOTHING_KERNELS) > 0
    assert all(isinstance(k, (int, float)) for k in SMOOTHING_KERNELS)

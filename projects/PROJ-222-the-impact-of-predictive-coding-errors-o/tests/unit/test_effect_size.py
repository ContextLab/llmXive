import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis import calculate_effect_sizes, fit_lmm

@pytest.fixture
def sample_data():
    """Create a small sample dataset for testing effect size calculation."""
    np.random.seed(42)
    n = 100
    data = {
        'duration_estimate': np.random.normal(10, 2, n),
        'surprisal': np.random.normal(0, 1, n),
        'sequence_length': np.random.randint(1, 10, n),
        'modality': np.random.choice(['visual', 'auditory'], n),
        'participant_id': [f'P{i}' for i in range(n)]
    }
    return pd.DataFrame(data)

def test_calculate_effect_sizes_returns_dict(sample_data):
    """Test that calculate_effect_sizes returns a dictionary with required keys."""
    # Mock a model result (None to trigger fallback logic)
    result = calculate_effect_sizes(sample_data, model_result=None)
    
    assert isinstance(result, dict)
    assert 'cohens_d' in result
    assert 'ci_low' in result
    assert 'ci_high' in result
    assert 'method' in result

def test_calculate_effect_sizes_with_model(sample_data):
    """Test effect size calculation with a fitted model."""
    # Fit a simple model first
    model_result, _ = fit_lmm(sample_data)
    
    if model_result is not None:
        result = calculate_effect_sizes(sample_data, model_result)
        assert isinstance(result, dict)
        assert 'cohens_d' in result
        assert 'ci_low' in result
        assert 'ci_high' in result
    else:
        # If model fitting fails (e.g., due to small sample size in test),
        # the function should still return a dict with None values or handle gracefully
        result = calculate_effect_sizes(sample_data, model_result)
        assert isinstance(result, dict)

def test_effect_size_values_reasonable(sample_data):
    """Test that calculated effect sizes are within a reasonable range."""
    result = calculate_effect_sizes(sample_data, model_result=None)
    
    # Cohen's d should typically be between -5 and 5 for real data
    if result['cohens_d'] is not None:
        assert -5 <= result['cohens_d'] <= 5
        
    if result['ci_low'] is not None and result['ci_high'] is not None:
        assert result['ci_low'] <= result['ci_high']
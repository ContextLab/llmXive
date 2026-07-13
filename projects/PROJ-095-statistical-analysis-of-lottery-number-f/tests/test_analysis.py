import pytest
import pandas as pd
import numpy as np
import json
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis import run_tier_analysis, compute_correlation_continuous, generate_warnings

@pytest.fixture
def sample_dataframe():
    """Create a synthetic dataframe for tier analysis testing."""
    data = {
        'draw_id': range(1, 21),
        'jackpot_amount': [
            1000, 2000, 3000,  # Small (assuming mean ~ 10000, threshold 5000)
            4000, 5000, 6000,  # Small/Medium boundary
            8000, 9000, 10000, # Medium
            12000, 13000, 14000, # Medium/Large boundary
            16000, 17000, 18000, # Large
            20000, 25000, 30000, # Large
            50000, 100000 # Extreme Large
        ],
        'birthday_cluster_ratio': np.random.rand(20)
    }
    return pd.DataFrame(data)

def test_run_tier_analysis_structure(sample_dataframe):
    """Test that tier analysis returns the correct structure."""
    result = run_tier_analysis(sample_dataframe)
    
    assert isinstance(result, dict), "Result must be a dictionary"
    assert 'Small' in result, "Result must contain 'Small' tier"
    assert 'Medium' in result, "Result must contain 'Medium' tier"
    assert 'Large' in result, "Result must contain 'Large' tier"
    
    # Check keys in a populated tier
    if result['Small']['draw_count'] > 0:
        assert 'draw_count' in result['Small']
        assert 'avg_birthday_cluster_ratio' in result['Small']
        assert 'avg_jackpot_amount' in result['Small']
        assert 'jackpot_range' in result['Small']
        assert 'threshold_range' in result['Small']

def test_run_tier_analysis_empty_data():
    """Test tier analysis with empty dataframe."""
    df_empty = pd.DataFrame(columns=['jackpot_amount', 'birthday_cluster_ratio'])
    result = run_tier_analysis(df_empty)
    
    assert result['Small']['draw_count'] == 0
    assert result['Medium']['draw_count'] == 0
    assert result['Large']['draw_count'] == 0

def test_generate_warnings_insufficient_data(sample_dataframe):
    """Test that warnings are generated for tiers with < 5 draws."""
    # Create a dataframe where one tier has < 5 draws
    # We'll manipulate the data to force a small tier
    df_small = pd.DataFrame({
        'jackpot_amount': [100, 200, 300], # Only 3 items
        'birthday_cluster_ratio': [0.1, 0.2, 0.3]
    })
    
    warnings = generate_warnings(df_small)
    
    # Should have a warning for at least one tier
    assert len(warnings) > 0
    assert any(w['type'] == 'insufficient_data' for w in warnings)

def test_compute_correlation_continuous(sample_dataframe):
    """Test correlation computation."""
    result = compute_correlation_continuous(sample_dataframe)
    
    assert 'correlation_coefficient' in result
    assert 'p_value' in result
    assert 'control_variable_note' in result
    
    # Check types
    assert isinstance(result['correlation_coefficient'], float)
    assert isinstance(result['p_value'], float)
    assert result['control_variable_note'] == "Quick Pick rate unobservable; no control applied"

def test_tier_analysis_integration(sample_dataframe):
    """Integration test: verify tier counts sum to total draws."""
    result = run_tier_analysis(sample_dataframe)
    total_count = sum(result[tier]['draw_count'] for tier in ['Small', 'Medium', 'Large'])
    assert total_count == len(sample_dataframe), "Sum of tier counts must equal total rows"

def test_run_tier_analysis_missing_columns():
    """Test behavior when required columns are missing."""
    df_missing = pd.DataFrame({'other_col': [1, 2, 3]})
    result = run_tier_analysis(df_missing)
    
    assert result['Small'] == {}
    assert result['Medium'] == {}
    assert result['Large'] == {}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

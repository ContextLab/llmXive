import pytest
import pandas as pd
from src.services.analysis import run_full_analysis

def test_binned_analysis_execution():
    """
    Integration test: Verify that the full statistical pipeline runs without error.
    """
    data = pd.DataFrame({
        'bridging_coefficient': [0.1, 0.2, 0.3, 0.4, 0.5],
        'citation_count': [10, 20, 30, 40, 50],
        'novelty_score': [0.5, 0.4, 0.3, 0.2, 0.1]
    })
    
    result = run_full_analysis(data)
    
    assert result is not None
    assert 'correlations' in result
    assert 'regressions' in result

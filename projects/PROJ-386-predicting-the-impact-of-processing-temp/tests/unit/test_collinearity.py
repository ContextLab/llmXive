import pytest
import pandas as pd
import numpy as np
from data.preprocessing import detect_collinearity

def test_detect_collinearity_no_flags():
    """Test that no pairs are flagged when correlation is low."""
    data = {
        'A': np.random.rand(100),
        'B': np.random.rand(100),
        'C': np.random.rand(100)
    }
    df = pd.DataFrame(data)
    report = detect_collinearity(df, threshold=0.8)
    
    assert report['flagged_count'] == 0
    assert report['flagged_pairs'] == []

def test_detect_collinearity_with_flags():
    """Test that pairs are correctly flagged when correlation is high."""
    n = 100
    base = np.random.rand(n)
    data = {
        'A': base,
        'B': base + np.random.normal(0, 0.01, n), # Highly correlated
        'C': np.random.rand(n)
    }
    df = pd.DataFrame(data)
    report = detect_collinearity(df, threshold=0.8)
    
    assert report['flagged_count'] == 1
    assert len(report['flagged_pairs']) == 1
    pair = report['flagged_pairs'][0]
    assert ('A', 'B') == tuple(pair) or ('B', 'A') == tuple(pair)

def test_detect_collinearity_report_schema():
    """Verify the report schema matches requirements."""
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [1, 2, 3]})
    report = detect_collinearity(df, threshold=0.8)
    
    assert 'flagged_pairs' in report
    assert isinstance(report['flagged_pairs'], list)
    if report['flagged_pairs']:
        assert isinstance(report['flagged_pairs'][0], list) or isinstance(report['flagged_pairs'][0], tuple)
    assert 'threshold' in report
    assert report['threshold'] == 0.8
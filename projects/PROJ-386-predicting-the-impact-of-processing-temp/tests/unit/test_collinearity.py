"""
Unit tests for collinearity detection logic in preprocessing.py
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile
import os

# Import the function to test
# We need to adjust the import path if running directly
try:
    from code.data.preprocessing import detect_collinearity
except ImportError:
    # Fallback for running from project root
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from code.data.preprocessing import detect_collinearity


def test_no_collinearity():
    """Test that no pairs are flagged when correlation is low."""
    # Create a dataframe with uncorrelated columns
    np.random.seed(42)
    df = pd.DataFrame({
        'A': np.random.rand(100),
        'B': np.random.rand(100),
        'C': np.random.rand(100)
    })
    
    report = detect_collinearity(df, threshold=0.8)
    
    assert report['flagged_pairs'] == []
    assert report['threshold'] == 0.8
    assert report['total_pairs_checked'] == 3


def test_high_collinearity_flagged():
    """Test that highly correlated pairs are flagged."""
    # Create a dataframe with one highly correlated pair
    np.random.seed(42)
    base = np.random.rand(100)
    df = pd.DataFrame({
        'A': base,
        'B': base + np.random.normal(0, 0.01, 100),  # Very high correlation
        'C': np.random.rand(100)  # Uncorrelated
    })
    
    report = detect_collinearity(df, threshold=0.8)
    
    assert len(report['flagged_pairs']) == 1
    # Check that the pair (A, B) is present (sorted)
    pair = report['flagged_pairs'][0]
    assert set(pair) == {'A', 'B'}


def test_multiple_collinear_pairs():
    """Test detection of multiple correlated pairs."""
    np.random.seed(42)
    base = np.random.rand(100)
    df = pd.DataFrame({
        'A': base,
        'B': base + np.random.normal(0, 0.01, 100),
        'C': base + np.random.normal(0, 0.01, 100),
        'D': np.random.rand(100)
    })
    
    report = detect_collinearity(df, threshold=0.8)
    
    # Should flag (A,B), (A,C), (B,C)
    assert len(report['flagged_pairs']) == 3
    pairs_set = {tuple(sorted(p)) for p in report['flagged_pairs']}
    assert ('A', 'B') in pairs_set
    assert ('A', 'C') in pairs_set
    assert ('B', 'C') in pairs_set


def test_report_schema():
    """Test that the report JSON has the required schema."""
    np.random.seed(42)
    df = pd.DataFrame({
        'A': np.random.rand(100),
        'B': np.random.rand(100)
    })
    
    report = detect_collinearity(df)
    
    assert 'threshold' in report
    assert 'flagged_pairs' in report
    assert 'total_pairs_checked' in report
    assert 'message' in report
    
    assert isinstance(report['flagged_pairs'], list)
    # Check that pairs are lists of strings
    if report['flagged_pairs']:
        for pair in report['flagled_pairs']:
            assert isinstance(pair, list)
            assert len(pair) == 2
            assert all(isinstance(x, str) for x in pair)


def test_file_generation():
    """Test that the JSON file is actually written to disk."""
    np.random.seed(42)
    df = pd.DataFrame({
        'A': np.random.rand(100),
        'B': np.random.rand(100)
    })
    
    # Temporarily change the output path logic if needed, 
    # but detect_collinearity writes to data/artifacts/collinearity_report.json
    # We check if that file exists after calling the function.
    # Note: In a real CI, we might mock the path, but for this test we assume
    # the directory exists or is created by the function.
    
    report = detect_collinearity(df)
    
    output_path = Path("data/artifacts/collinearity_report.json")
    assert output_path.exists(), "Collinearity report JSON file was not created."
    
    with open(output_path, 'r') as f:
        loaded_report = json.load(f)
    
    assert loaded_report == report
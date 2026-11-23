import pytest
import json
import os
import sys
import numpy as np

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis import run_tier_analysis, compute_correlation_continuous

@pytest.fixture
def sample_data():
    """Generate a small dataset for testing tier analysis."""
    # Create data with distinct jackpot sizes
    data = []
    # Small tier (1-3)
    for i in range(3):
        data.append({
            "jackpot_amount": 100.0 + i,
            "birthday_cluster_ratio": 0.1 + i * 0.05,
            "consecutive_pattern_count": 0
        })
    # Medium tier (4-6)
    for i in range(3):
        data.append({
            "jackpot_amount": 200.0 + i,
            "birthday_cluster_ratio": 0.2 + i * 0.05,
            "consecutive_pattern_count": 0
        })
    # Large tier (7-9)
    for i in range(3):
        data.append({
            "jackpot_amount": 300.0 + i,
            "birthday_cluster_ratio": 0.3 + i * 0.05,
            "consecutive_pattern_count": 0
        })
    return data

def test_run_tier_analysis_structure(sample_data):
    """Test that tier analysis returns the expected structure."""
    result = run_tier_analysis(sample_data)
    
    assert isinstance(result, list)
    assert len(result) == 3  # Small, Medium, Large
    
    tiers = {t['tier']: t for t in result}
    assert "Small" in tiers
    assert "Medium" in tiers
    assert "Large" in tiers
    
    # Check required keys
    for t in result:
        assert 'tier' in t
        assert 'count' in t
        assert 'status' in t
        assert 'correlation_coefficient' in t
        assert 'p_value' in t

def test_tier_counts(sample_data):
    """Test that counts are correct for each tier."""
    result = run_tier_analysis(sample_data)
    tiers = {t['tier']: t for t in result}
    
    # With 3 items each and quantiles at 33/66, we expect roughly equal distribution
    # Depending on exact quantile calculation, counts might vary slightly but should be close
    total_count = sum(t['count'] for t in result)
    assert total_count == 9

def test_insufficient_data_flag():
    """Test that tiers with < 5 draws are flagged."""
    # Create data with only 2 items
    data = [
        {"jackpot_amount": 100.0, "birthday_cluster_ratio": 0.1, "consecutive_pattern_count": 0},
        {"jackpot_amount": 105.0, "birthday_cluster_ratio": 0.2, "consecutive_pattern_count": 0}
    ]
    result = run_tier_analysis(data)
    
    # All items will fall into one or two tiers, all with count < 5
    for t in result:
        assert t['status'] == 'insufficient_data'

def test_correlation_computation():
    """Test correlation computation with known data."""
    # Perfect positive correlation
    data = [
        {"jackpot_amount": 100, "birthday_cluster_ratio": 0.1},
        {"jackpot_amount": 200, "birthday_cluster_ratio": 0.2},
        {"jackpot_amount": 300, "birthday_cluster_ratio": 0.3},
        {"jackpot_amount": 400, "birthday_cluster_ratio": 0.4},
        {"jackpot_amount": 500, "birthday_cluster_ratio": 0.5}
    ]
    corr, p = compute_correlation_continuous(data)
    assert abs(corr - 1.0) < 1e-6
    assert p < 0.05

def test_correlation_empty_data():
    """Test correlation with empty data."""
    corr, p = compute_correlation_continuous([])
    assert corr == 0.0
    assert p == 1.0
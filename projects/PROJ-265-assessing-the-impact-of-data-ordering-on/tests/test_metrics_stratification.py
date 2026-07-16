import pytest
import numpy as np
from metrics import stratify_by_phi

def test_stratify_by_phi_empty_results():
    """Test that empty results return empty list."""
    result = stratify_by_phi([], [0.0, 0.5, 1.0])
    assert result == []

def test_stratify_by_phi_missing_phi_key():
    """Test that results without 'phi' key return empty list."""
    results = [{'foo': 'bar'}]
    result = stratify_by_phi(results, [0.0, 0.5, 1.0])
    assert result == []

def test_stratify_by_phi_basic():
    """Test basic stratification functionality."""
    results = [
        {'phi': 0.1, 'ordered_cov': 0.95, 'shuffled_cov': 0.95},
        {'phi': 0.2, 'ordered_cov': 0.94, 'shuffled_cov': 0.95},
        {'phi': 0.7, 'ordered_cov': 0.85, 'shuffled_cov': 0.95},
        {'phi': 0.8, 'ordered_cov': 0.80, 'shuffled_cov': 0.95},
    ]
    bins = [0.0, 0.5, 1.0]
    result = stratify_by_phi(results, bins)
    
    assert len(result) == 2
    
    # Check first bin (0.0-0.5)
    bin0 = next(r for r in result if r['bin'] == '0.0-0.5')
    assert bin0['n_samples'] == 2
    assert abs(bin0['mean_ordered_cov'] - 0.945) < 0.001
    assert abs(bin0['mean_shuffled_cov'] - 0.95) < 0.001
    
    # Check second bin (0.5-1.0)
    bin1 = next(r for r in result if r['bin'] == '0.5-1.0')
    assert bin1['n_samples'] == 2
    assert abs(bin1['mean_ordered_cov'] - 0.825) < 0.001
    assert abs(bin1['mean_shuffled_cov'] - 0.95) < 0.001

def test_stratify_by_phi_coverage_drop():
    """Test that coverage drop is calculated correctly."""
    results = [
        {'phi': 0.1, 'ordered_cov': 0.95, 'shuffled_cov': 0.95},
        {'phi': 0.7, 'ordered_cov': 0.80, 'shuffled_cov': 0.95},
    ]
    bins = [0.0, 0.5, 1.0]
    result = stratify_by_phi(results, bins)
    
    # Bin 0.0-0.5
    bin0 = next(r for r in result if r['bin'] == '0.0-0.5')
    assert abs(bin0['coverage_drop']) < 0.01  # ~0.0
    
    # Bin 0.5-1.0
    bin1 = next(r for r in result if r['bin'] == '0.5-1.0')
    assert abs(bin1['coverage_drop'] - (-0.15)) < 0.01  # 0.80 - 0.95 = -0.15

def test_stratify_by_phi_edge_cases():
    """Test edge cases like phi at bin boundaries."""
    results = [
        {'phi': 0.5, 'ordered_cov': 0.90, 'shuffled_cov': 0.95},
        {'phi': 0.0, 'ordered_cov': 0.95, 'shuffled_cov': 0.95},
        {'phi': 1.0, 'ordered_cov': 0.70, 'shuffled_cov': 0.95},
    ]
    bins = [0.0, 0.5, 1.0]
    result = stratify_by_phi(results, bins)
    
    # Should have 2 bins
    assert len(result) == 2
    
    # Check that all results are assigned
    total_samples = sum(r['n_samples'] for r in result)
    assert total_samples == 3
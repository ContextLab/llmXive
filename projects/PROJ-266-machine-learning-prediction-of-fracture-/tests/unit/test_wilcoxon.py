"""
Unit tests for the Wilcoxon statistical test functionality.
"""
import pytest
from code.train.stats import wilcoxon_test, aggregate_mae_distributions

def test_wilcoxon_test_basic():
    """Test basic Wilcoxon test functionality."""
    sample_a = [0.15, 0.14, 0.16, 0.13, 0.15]
    sample_b = [0.25, 0.24, 0.26, 0.23, 0.25]
    
    result = wilcoxon_test(sample_a, sample_b)
    
    assert 'p_value' in result
    assert 'statistic' in result
    assert 'significant' in result
    assert isinstance(result['p_value'], float)
    assert isinstance(result['statistic'], float)
    assert isinstance(result['significant'], bool)
    
    # With these values, we expect significant difference
    assert result['significant'] is True

def test_wilcoxon_test_identical_samples():
    """Test Wilcoxon test with identical samples (p-value should be 1.0)."""
    sample = [0.15, 0.14, 0.16, 0.13, 0.15]
    
    result = wilcoxon_test(sample, sample)
    
    assert result['p_value'] == 1.0
    assert result['significant'] is False

def test_wilcoxon_test_mismatched_lengths():
    """Test that Wilcoxon test raises error for mismatched lengths."""
    sample_a = [0.15, 0.14, 0.16]
    sample_b = [0.25, 0.24, 0.26, 0.23]
    
    with pytest.raises(ValueError, match="Samples must be of equal length"):
        wilcoxon_test(sample_a, sample_b)

def test_wilcoxon_test_insufficient_samples():
    """Test that Wilcoxon test raises error for insufficient samples."""
    sample_a = [0.15]
    sample_b = [0.25]
    
    with pytest.raises(ValueError, match="Need at least 2 samples"):
        wilcoxon_test(sample_a, sample_b)

def test_aggregate_mae_distributions():
    """Test summary statistics calculation."""
    mae_dict = {
        'cnn': [0.15, 0.14, 0.16, 0.13, 0.15],
        'linear': [0.25, 0.24, 0.26, 0.23, 0.25]
    }
    
    summary = aggregate_mae_distributions(mae_dict)
    
    assert 'cnn' in summary
    assert 'linear' in summary
    assert 'mean' in summary['cnn']
    assert 'std' in summary['cnn']
    assert 'min' in summary['cnn']
    assert 'max' in summary['cnn']
    
    # Check calculated values
    assert summary['cnn']['mean'] == 0.146
    assert summary['linear']['mean'] == 0.246

def test_aggregate_mae_distributions_empty_list():
    """Test summary statistics with empty list."""
    mae_dict = {
        'cnn': [],
        'linear': [0.25, 0.24, 0.26]
    }
    
    summary = aggregate_mae_distributions(mae_dict)
    
    assert summary['cnn']['mean'] is None
    assert summary['cnn']['std'] is None
    assert summary['linear']['mean'] is not None
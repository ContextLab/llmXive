"""
Unit tests for T023a: validate_cohesion.py

Tests the Spearman correlation calculation and validation logic.
"""
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import logging
import pytest

# Import the functions to test
# Note: In a real setup, these would be imported from code/validate_cohesion
# For testing purposes, we'll mock the dependencies

@pytest.fixture
def sample_aligned_data():
    """Create sample aligned data for testing."""
    np.random.seed(42)
    n_samples = 50
    manual_scores = np.random.normal(0.5, 0.2, n_samples)
    # Create correlated VADER scores (with some noise)
    vader_scores = manual_scores + np.random.normal(0, 0.1, n_samples)
    
    df = pd.DataFrame({
        "project_id": ["proj1"] * n_samples,
        "comment_id": [f"comment_{i}" for i in range(n_samples)],
        "manual_cohesion_score": manual_scores,
        "vader_compound": vader_scores
    })
    return df

@pytest.fixture
def small_sample_data():
    """Create a small sample dataset (below threshold)."""
    return pd.DataFrame({
        "project_id": ["proj1"] * 3,
        "comment_id": ["c1", "c2", "c3"],
        "manual_cohesion_score": [0.1, 0.5, 0.9],
        "vader_compound": [0.1, 0.5, 0.9]
    })

@pytest.fixture
def empty_aligned_data():
    """Create an empty aligned dataset."""
    return pd.DataFrame(columns=["project_id", "comment_id", "manual_cohesion_score", "vader_compound"])

@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = MagicMock(spec=logging.Logger)
    return logger

def test_sufficient_samples_calculates_correlation(sample_aligned_data, mock_logger):
    """Test that correlation is calculated when sufficient samples exist."""
    from scipy.stats import spearmanr
    
    # Mock the spearmanr function to return known values
    expected_rho = 0.75
    expected_p = 0.001
    
    with patch("validate_cohesion.spearmanr", return_value=(expected_rho, expected_p)):
        from validate_cohesion import calculate_spearman_correlation
        
        rho, p_value, pass_status = calculate_spearman_correlation(sample_aligned_data, mock_logger)
        
        assert rho is not None
        assert p_value is not None
        assert rho == expected_rho
        assert p_value == expected_p
        assert pass_status is True  # 0.75 >= 0.5

def test_insufficient_samples_returns_none(small_sample_data, mock_logger):
    """Test that insufficient samples return None values."""
    from validate_cohesion import calculate_spearman_correlation
    
    rho, p_value, pass_status = calculate_spearman_correlation(small_sample_data, mock_logger)
    
    assert rho is None
    assert p_value is None
    assert pass_status is False
    
    # Verify warning was logged
    mock_logger.warning.assert_called()

def test_empty_dataframe_returns_none(empty_aligned_data, mock_logger):
    """Test that empty dataframe returns None values."""
    from validate_cohesion import calculate_spearman_correlation
    
    rho, p_value, pass_status = calculate_spearman_correlation(empty_aligned_data, mock_logger)
    
    assert rho is None
    assert p_value is None
    assert pass_status is False

def test_pass_threshold_logic(sample_aligned_data, mock_logger):
    """Test pass/fail logic based on threshold."""
    from validate_cohesion import calculate_spearman_correlation
    
    # Test with high correlation (pass)
    with patch("validate_cohesion.spearmanr", return_value=(0.8, 0.001)):
        _, _, pass_status = calculate_spearman_correlation(sample_aligned_data, mock_logger)
        assert pass_status is True
    
    # Test with low correlation (fail)
    with patch("validate_cohesion.spearmanr", return_value=(0.3, 0.001)):
        _, _, pass_status = calculate_spearman_correlation(sample_aligned_data, mock_logger)
        assert pass_status is False
    
    # Test with exactly threshold (pass)
    with patch("validate_cohesion.spearmanr", return_value=(0.5, 0.001)):
        _, _, pass_status = calculate_spearman_correlation(sample_aligned_data, mock_logger)
        assert pass_status is True

def test_nan_correlation_handling(sample_aligned_data, mock_logger):
    """Test handling of NaN correlation values."""
    from validate_cohesion import calculate_spearman_correlation
    
    with patch("validate_cohesion.spearmanr", return_value=(np.nan, np.nan)):
        rho, p_value, pass_status = calculate_spearman_correlation(sample_aligned_data, mock_logger)
        
        assert rho is None
        assert p_value is None
        assert pass_status is False
        
        # Verify warning was logged
        mock_logger.warning.assert_called()

def test_exception_handling(sample_aligned_data, mock_logger):
    """Test that exceptions during correlation calculation are handled."""
    from validate_cohesion import calculate_spearman_correlation
    
    with patch("validate_cohesion.spearmanr", side_effect=Exception("Test error")):
        rho, p_value, pass_status = calculate_spearman_correlation(sample_aligned_data, mock_logger)
        
        assert rho is None
        assert p_value is None
        assert pass_status is False
        
        # Verify error was logged
        mock_logger.error.assert_called()
"""
Integration test for 'Hypothesis Not Supported' flag logic.

This test verifies that the correlation analysis correctly flags results
as 'Hypothesis Not Supported' when the directional effect condition (r < -0.5)
is not met, or when statistical significance (p < 0.05) is not achieved.

It simulates a scenario where the correlation is weak or positive, ensuring
the pipeline does not falsely claim support for the hypothesis.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.correlation import (
    calculate_spearman_correlation,
    evaluate_hypothesis,
    perform_bootstrap_resampling,
    calculate_statistical_power
)
from utils.logger import get_logger

logger = get_logger(__name__)

# Fixed seed for reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

@pytest.fixture
def weak_negative_correlation_data():
    """
    Generate synthetic data with a weak negative correlation (r ~ -0.2).
    This should result in 'Hypothesis Not Supported' because |r| < 0.5.
    """
    n_samples = 50
    # Generate island_width
    island_width = np.random.uniform(0.01, 0.05, n_samples)
    # Generate tau_e with a weak negative relationship + noise
    # tau_e = -0.2 * island_width + noise
    tau_e = -0.2 * island_width + np.random.normal(0, 0.05, n_samples)
    
    # Create DataFrame
    df = pd.DataFrame({
        'discharge_id': range(1000, 1000 + n_samples),
        'island_width': island_width,
        'tau_e': tau_e,
        'confinement_mode': ['L-mode'] * n_samples,
        'resonant_surface_density': np.random.uniform(0, 2, n_samples)
    })
    return df

@pytest.fixture
def strong_positive_correlation_data():
    """
    Generate synthetic data with a strong positive correlation (r ~ 0.8).
    This should result in 'Hypothesis Not Supported' because r > -0.5 (directional effect fails).
    """
    n_samples = 50
    island_width = np.random.uniform(0.01, 0.05, n_samples)
    # tau_e increases with island_width
    tau_e = 0.8 * island_width + np.random.normal(0, 0.02, n_samples)
    
    df = pd.DataFrame({
        'discharge_id': range(2000, 2000 + n_samples),
        'island_width': island_width,
        'tau_e': tau_e,
        'confinement_mode': ['H-mode'] * n_samples,
        'resonant_surface_density': np.random.uniform(0, 2, n_samples)
    })
    return df

@pytest.fixture
def insignificant_correlation_data():
    """
    Generate data with r ~ -0.6 but high noise leading to p > 0.05.
    This should result in 'Hypothesis Not Supported' due to lack of significance.
    """
    n_samples = 10  # Small sample size to make significance harder
    island_width = np.random.uniform(0.01, 0.05, n_samples)
    # Strong negative slope but massive noise
    tau_e = -0.6 * island_width + np.random.normal(0, 0.5, n_samples)
    
    df = pd.DataFrame({
        'discharge_id': range(3000, 3000 + n_samples),
        'island_width': island_width,
        'tau_e': tau_e,
        'confinement_mode': ['L-mode'] * n_samples,
        'resonant_surface_density': np.random.uniform(0, 2, n_samples)
    })
    return df

def test_hypothesis_not_supported_weak_correlation(weak_negative_correlation_data):
    """
    Test Case 1: Weak negative correlation (r ~ -0.2).
    Expected: hypothesis_supported = False, reason = "Directional effect not met (|r| < 0.5)"
    """
    df = weak_negative_correlation_data
    
    # Calculate correlation
    corr_result = calculate_spearman_correlation(df, 'island_width', 'tau_e')
    
    logger.info(f"Calculated correlation: r={corr_result['r']:.3f}, p={corr_result['p_value']:.3f}")
    
    # Evaluate hypothesis
    hypothesis_result = evaluate_hypothesis(
        r=corr_result['r'],
        p_value=corr_result['p_value'],
        effect_size_threshold=-0.5,
        p_threshold=0.05
    )
    
    assert hypothesis_result['hypothesis_supported'] is False
    assert "Directional effect not met" in hypothesis_result['reason'] or "statistical significance not met" in hypothesis_result['reason']
    logger.info(f"Hypothesis Result: {hypothesis_result}")

def test_hypothesis_not_supported_positive_correlation(strong_positive_correlation_data):
    """
    Test Case 2: Strong positive correlation (r ~ 0.8).
    Expected: hypothesis_supported = False, reason = "Directional effect not met (r >= -0.5)"
    """
    df = strong_positive_correlation_data
    
    corr_result = calculate_spearman_correlation(df, 'island_width', 'tau_e')
    
    logger.info(f"Calculated correlation: r={corr_result['r']:.3f}, p={corr_result['p_value']:.3f}")
    
    hypothesis_result = evaluate_hypothesis(
        r=corr_result['r'],
        p_value=corr_result['p_value'],
        effect_size_threshold=-0.5,
        p_threshold=0.05
    )
    
    assert hypothesis_result['hypothesis_supported'] is False
    assert "Directional effect not met" in hypothesis_result['reason']
    logger.info(f"Hypothesis Result: {hypothesis_result}")

def test_hypothesis_not_supported_insufficient_significance(insignificant_correlation_data):
    """
    Test Case 3: Moderate negative correlation (r ~ -0.6) but insignificant p-value.
    Expected: hypothesis_supported = False, reason = "Statistical significance not met (p >= 0.05)"
    """
    df = insignificant_correlation_data
    
    corr_result = calculate_spearman_correlation(df, 'island_width', 'tau_e')
    
    logger.info(f"Calculated correlation: r={corr_result['r']:.3f}, p={corr_result['p_value']:.3f}")
    
    hypothesis_result = evaluate_hypothesis(
        r=corr_result['r'],
        p_value=corr_result['p_value'],
        effect_size_threshold=-0.5,
        p_threshold=0.05
    )
    
    assert hypothesis_result['hypothesis_supported'] is False
    assert "statistical significance not met" in hypothesis_result['reason'].lower()
    logger.info(f"Hypothesis Result: {hypothesis_result}")

def test_hypothesis_supported_strong_significant_negative():
    """
    Test Case 4: Strong negative correlation (r ~ -0.7) with significance.
    Expected: hypothesis_supported = True.
    This serves as a control to ensure the logic isn't broken.
    """
    n_samples = 50
    island_width = np.random.uniform(0.01, 0.05, n_samples)
    # Strong negative relationship with low noise
    tau_e = -0.7 * island_width + np.random.normal(0, 0.01, n_samples)
    
    df = pd.DataFrame({
        'discharge_id': range(4000, 4000 + n_samples),
        'island_width': island_width,
        'tau_e': tau_e,
        'confinement_mode': ['L-mode'] * n_samples,
        'resonant_surface_density': np.random.uniform(0, 2, n_samples)
    })
    
    corr_result = calculate_spearman_correlation(df, 'island_width', 'tau_e')
    
    logger.info(f"Calculated correlation: r={corr_result['r']:.3f}, p={corr_result['p_value']:.3f}")
    
    hypothesis_result = evaluate_hypothesis(
        r=corr_result['r'],
        p_value=corr_result['p_value'],
        effect_size_threshold=-0.5,
        p_threshold=0.05
    )
    
    assert hypothesis_result['hypothesis_supported'] is True
    logger.info(f"Hypothesis Result: {hypothesis_result}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

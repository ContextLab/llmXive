import pytest
import numpy as np
from pathlib import Path
from scipy.stats import norm

from code.analysis.metrics import (
    calculate_bias, 
    compute_metrics_for_resolution, 
    calculate_hellinger_distance
)
from code.data.models import PosteriorDistribution

@pytest.fixture
def mock_baseline_posterior():
    """Create a mock baseline posterior with known stats."""
    # Mean = 30, Std = 1.0
    np.random.seed(42)
    samples = np.random.normal(loc=30.0, scale=1.0, size=(10000, 1))
    return PosteriorDistribution(
        samples=samples,
        parameter_names=['mchirp'],
        metadata={'status': 'valid'}
    )

@pytest.fixture
def mock_downsampled_posterior_shifted():
    """Create a mock downsampled posterior with a significant bias."""
    # Mean = 35.0 (Shifted by 5.0), Std = 1.0
    np.random.seed(43)
    samples = np.random.normal(loc=35.0, scale=1.0, size=(10000, 1))
    return PosteriorDistribution(
        samples=samples,
        parameter_names=['mchirp'],
        metadata={'status': 'valid'}
    )

@pytest.fixture
def mock_downsampled_posterior_close():
    """Create a mock downsampled posterior with negligible bias."""
    # Mean = 30.1 (Shifted by 0.1), Std = 1.0
    np.random.seed(44)
    samples = np.random.normal(loc=30.1, scale=1.0, size=(10000, 1))
    return PosteriorDistribution(
        samples=samples,
        parameter_names=['mchirp'],
        metadata={'status': 'valid'}
    )

def test_bias_exceeds_catalog_threshold(mock_baseline_posterior, mock_downsampled_posterior_shifted):
    """
    Test that bias is correctly flagged when it exceeds the catalog-reported 90% CI.
    Scenario: Bias = 5.0, Catalog 90% CI Threshold = 2.0. Expect True.
    """
    # Calculate intrinsic uncertainty (90% CI width) for baseline
    # Width = 2 * 1.645 * sigma = 2 * 1.645 * 1.0 = 3.29
    catalog_90_ci = 3.29 
    
    # Injected truth is None, so it will compare against baseline mean (30.0)
    # Downsampled mean is 35.0. Bias = 5.0.
    
    metrics = compute_metrics_for_resolution(
        downsampled_posterior=mock_downsampled_posterior_shifted,
        baseline_posterior=mock_baseline_posterior,
        catalog_uncertainty_90=catalog_90_ci,
        injected_truth=None,
        catalog_truth=None,
        param_name='mchirp'
    )
    
    assert metrics['absolute_bias'] == pytest.approx(5.0, rel=0.1)
    assert metrics['bias_exceeds_catalog_uncertainty'] is True

def test_bias_within_catalog_threshold(mock_baseline_posterior, mock_downsampled_posterior_close):
    """
    Test that bias is NOT flagged when it is within the catalog-reported 90% CI.
    Scenario: Bias = 0.1, Catalog 90% CI Threshold = 3.29. Expect False.
    """
    catalog_90_ci = 3.29
    
    metrics = compute_metrics_for_resolution(
        downsampled_posterior=mock_downsampled_posterior_close,
        baseline_posterior=mock_baseline_posterior,
        catalog_uncertainty_90=catalog_90_ci,
        injected_truth=None,
        catalog_truth=None,
        param_name='mchirp'
    )
    
    assert metrics['absolute_bias'] == pytest.approx(0.1, rel=0.1)
    assert metrics['bias_exceeds_catalog_uncertainty'] is False

def test_bias_calculation_with_injected_truth(mock_downsampled_posterior_shifted):
    """
    Test bias calculation when injected truth is provided.
    Injected Truth = 30.0. Downsampled Mean = 35.0. Bias = 5.0.
    """
    injected_truth = {'mchirp': 30.0}
    
    # We need a baseline here just to satisfy the function signature, 
    # but it shouldn't be used for the mean if injected_truth is present.
    baseline = mock_downsampled_posterior_shifted # Dummy
    
    metrics = compute_metrics_for_resolution(
        downsampled_posterior=mock_downsampled_posterior_shifted,
        baseline_posterior=baseline,
        catalog_uncertainty_90=10.0,
        injected_truth=injected_truth,
        catalog_truth=None,
        param_name='mchirp'
    )
    
    assert metrics['absolute_bias'] == pytest.approx(5.0, rel=0.1)
    assert metrics['truth_source'] == 'injected'

def test_hellinger_distance_symmetry(mock_baseline_posterior, mock_downsampled_posterior_shifted):
    """Verify Hellinger distance is symmetric and non-negative."""
    h1 = calculate_hellinger_distance(mock_baseline_posterior, mock_downsampled_posterior_shifted, 'mchirp')
    h2 = calculate_hellinger_distance(mock_downsampled_posterior_shifted, mock_baseline_posterior, 'mchirp')
    
    assert h1 == pytest.approx(h2, rel=1e-5)
    assert h1 >= 0.0
    assert h1 <= 1.0
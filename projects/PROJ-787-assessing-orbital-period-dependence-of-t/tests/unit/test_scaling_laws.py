"""
Unit tests for the scaling_laws module.
Verifies that theoretical distributions are loaded correctly and behave as expected.
"""

import sys
import os
import pytest
import numpy as np
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from theory.scaling_laws import load_theoretical_laws, TheoreticalDistribution, get_theoretical_overlap

@pytest.fixture
def theories():
    """Load theoretical distributions for testing."""
    return load_theoretical_laws()

def test_load_theoretical_laws_exists(theories):
    """Test that the load_theoretical_laws function returns a dictionary."""
    assert isinstance(theories, dict)
    assert len(theories) > 0

def test_owen_wu_parameters(theories):
    """Test Owen & Wu (photoevaporation) parameters match FR-007 source of truth."""
    assert "owen_wu" in theories
    owen_wu = theories["owen_wu"]
    
    assert owen_wu.name == "owen_wu"
    assert abs(owen_wu.mean_slope - (-0.11)) < 1e-6
    assert abs(owen_wu.std_slope - 0.02) < 1e-6
    assert "Photoevaporation" in owen_wu.description

def test_ginzburg_parameters(theories):
    """Test Ginzburg et al. (core-powered) parameters match FR-007 source of truth."""
    assert "ginzburg" in theories
    ginzburg = theories["ginzburg"]
    
    assert ginzburg.name == "ginzburg"
    assert abs(ginzburg.mean_slope - (-0.15)) < 1e-6
    assert abs(ginzburg.std_slope - 0.03) < 1e-6
    assert "Core-powered" in ginzburg.description

def test_distribution_method(theories):
    """Test that get_distribution returns a valid scipy frozen distribution."""
    from scipy import stats
    
    for name, theory in theories.items():
        dist = theory.get_distribution()
        assert isinstance(dist, stats._continuous_distns.norm_frozen)
        
        # Verify mean and std
        assert abs(dist.mean() - theory.mean_slope) < 1e-6
        assert abs(dist.std() - theory.std_slope) < 1e-6

def test_pdf_calculation(theories):
    """Test PDF calculation returns valid probabilities."""
    owen_wu = theories["owen_wu"]
    
    # At the mean, PDF should be at its maximum
    max_pdf = owen_wu.pdf(owen_wu.mean_slope)
    assert max_pdf > 0
    
    # Far from the mean, PDF should be very small
    far_pdf = owen_wu.pdf(owen_wu.mean_slope + 5 * owen_wu.std_slope)
    assert far_pdf < max_pdf
    assert far_pdf > 0

def test_cdf_calculation(theories):
    """Test CDF calculation returns valid cumulative probabilities."""
    owen_wu = theories["owen_wu"]
    
    # CDF at mean should be ~0.5
    cdf_mean = owen_wu.cdf(owen_wu.mean_slope)
    assert abs(cdf_mean - 0.5) < 0.01
    
    # CDF at -inf should be ~0
    cdf_low = owen_wu.cdf(owen_wu.mean_slope - 10 * owen_wu.std_slope)
    assert cdf_low < 0.001
    
    # CDF at +inf should be ~1
    cdf_high = owen_wu.cdf(owen_wu.mean_slope + 10 * owen_wu.std_slope)
    assert cdf_high > 0.999

def test_sampling(theories):
    """Test that sampling generates data with correct statistical properties."""
    ginzburg = theories["ginzburg"]
    size = 100000
    samples = ginzburg.sample(size)
    
    assert len(samples) == size
    
    # Check sample mean is close to theoretical mean
    sample_mean = np.mean(samples)
    assert abs(sample_mean - ginzburg.mean_slope) < 0.01 * abs(ginzburg.mean_slope)
    
    # Check sample std is close to theoretical std
    sample_std = np.std(samples)
    assert abs(sample_std - ginzburg.std_slope) < 0.01 * abs(ginzburg.std_slope)

def test_theoretical_overlap(theories):
    """Test overlap calculation between two distributions."""
    owen_wu = theories["owen_wu"]
    ginzburg = theories["ginzburg"]
    
    overlap = get_theoretical_overlap(owen_wu, ginzburg, num_samples=10000)
    
    # Overlap should be between 0 and 1
    assert 0.0 <= overlap <= 1.0
    
    # Since the means are different (-0.11 vs -0.15) and stds are small,
    # there should be some overlap but not total overlap
    assert overlap > 0.01
    assert overlap < 0.99
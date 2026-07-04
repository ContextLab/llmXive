"""
Unit tests for entropy calculation functions.
"""
import pytest
import numpy as np
from code.entropy import compute_sample_entropy, compute_multiscale_entropy

@pytest.fixture
def sample_entropy_vector():
    """Generate a sample time series for testing."""
    np.random.seed(42)
    return np.random.randn(100)

@pytest.fixture
def sample_2d_data():
    """Generate 2D data for testing."""
    np.random.seed(42)
    return np.random.randn(5, 100)

def test_compute_sample_entropy_basic(sample_entropy_vector):
    """
    Test that compute_sample_entropy returns a float for a valid input vector.
    """
    m = 2
    r = 0.2 * np.std(sample_entropy_vector)
    
    result = compute_sample_entropy(sample_entropy_vector, m, r)
    
    assert isinstance(result, float)
    assert result >= 0
    assert not np.isnan(result)

def test_compute_sample_entropy_nan_handling():
    """
    Test behavior with NaN values in input.
    """
    data = np.random.randn(50)
    data[10] = np.nan
    
    result = compute_sample_entropy(data, m=2, r=0.2)
    
    assert np.isnan(result)

def test_compute_sample_entropy_insufficient_data():
    """
    Test behavior with insufficient data points.
    """
    data = np.random.randn(3)  # Too short for m=2
    
    result = compute_sample_entropy(data, m=2, r=0.2)
    
    assert np.isnan(result)

def test_compute_sample_entropy_zero_std():
    """
    Test behavior with zero standard deviation.
    """
    data = np.ones(50)  # All same value
    
    result = compute_sample_entropy(data, m=2, r=0.2)
    
    assert np.isnan(result)

def test_compute_sample_entropy_2d_input(sample_2d_data):
    """
    Test entropy calculation on 2D input.
    """
    result = compute_sample_entropy(sample_2d_data, m=2, r=0.2, axis=1)
    
    assert isinstance(result, np.ndarray)
    assert len(result) == sample_2d_data.shape[0]
    assert all(not np.isnan(r) for r in result)

def test_compute_multiscale_entropy_basic(sample_entropy_vector):
    """
    Test multiscale entropy calculation.
    """
    entropy_profile, auc = compute_multiscale_entropy(sample_entropy_vector, m=2, r_factor=0.2)
    
    assert isinstance(entropy_profile, np.ndarray)
    assert len(entropy_profile) == 20  # Default scales 1-20
    assert isinstance(auc, float)
    assert auc >= 0

def test_compute_multiscale_entropy_custom_scales(sample_entropy_vector):
    """
    Test multiscale entropy with custom scales.
    """
    scales = np.array([1, 2, 3, 4, 5])
    entropy_profile, auc = compute_multiscale_entropy(
        sample_entropy_vector, m=2, r_factor=0.2, scales=scales
    )
    
    assert len(entropy_profile) == 5
    # Verify AUC calculation matches trapezoidal integration
    expected_auc = np.trapz(entropy_profile, dx=1)
    assert np.allclose(auc, expected_auc), f"AUC {auc} does not match expected {expected_auc}"

def test_known_small_matrix():
    """
    Test against a known small matrix with predictable entropy.
    This is the core validation test mentioned in T010.
    """
    # Create a highly regular signal (low entropy expected)
    regular_signal = np.sin(np.linspace(0, 10*np.pi, 100))
    entropy_regular = compute_sample_entropy(regular_signal, m=2, r=0.2*np.std(regular_signal))
    
    # Create a random signal (higher entropy expected)
    np.random.seed(42)
    random_signal = np.random.randn(100)
    entropy_random = compute_sample_entropy(random_signal, m=2, r=0.2*np.std(random_signal))
    
    # Regular signal should have lower entropy than random signal
    assert entropy_regular < entropy_random, \
        f"Expected regular signal entropy ({entropy_regular}) < random signal entropy ({entropy_random})"
    
    # Both should be non-negative
    assert entropy_regular >= 0
    assert entropy_random >= 0

def test_2d_multiscale_entropy(sample_2d_data):
    """
    Test multiscale entropy on 2D data.
    """
    entropy_profile, auc = compute_multiscale_entropy(sample_2d_data, m=2, r_factor=0.2, axis=1)
    
    assert isinstance(entropy_profile, np.ndarray)
    assert len(entropy_profile) == 20
    assert isinstance(auc, float)
    assert auc >= 0

def test_auc_aggregation_accuracy(sample_entropy_vector):
    """
    Integration test for AUC aggregation in compute_multiscale_entropy.
    Verifies that the Area Under the Curve is correctly calculated across scales 1-20.
    """
    # Generate a deterministic signal for reproducible entropy values
    np.random.seed(123)
    signal = np.random.randn(200) * 0.5
    
    # Compute multiscale entropy
    entropy_profile, auc = compute_multiscale_entropy(signal, m=2, r_factor=0.2)
    
    # Verify the profile has the expected length (scales 1-20)
    assert len(entropy_profile) == 20, f"Expected 20 scales, got {len(entropy_profile)}"
    
    # Manually calculate expected AUC using trapezoidal rule
    # The x-axis is scale index (1, 2, ..., 20), so dx = 1
    expected_auc = np.trapz(entropy_profile, dx=1)
    
    # Verify the returned AUC matches the manual calculation
    assert np.isclose(auc, expected_auc), \
        f"AUC mismatch: returned {auc}, expected {expected_auc}"
    
    # Verify AUC is positive and within reasonable bounds for Sample Entropy
    assert auc > 0, "AUC should be positive"
    assert auc < 10.0, "AUC should be within reasonable bounds for typical fMRI signals"
    
    # Verify that entropy profile is monotonically decreasing or has expected behavior
    # (Sample entropy typically decreases as scale increases due to coarsening)
    # Note: This is not a strict requirement as some signals may show non-monotonic behavior
    # but the profile should not be all zeros or NaNs
    assert not np.all(entropy_profile == 0), "Entropy profile should not be all zeros"
    assert not np.all(np.isnan(entropy_profile)), "Entropy profile should not contain all NaNs"

def test_auc_aggregation_with_nan_handling():
    """
    Test AUC aggregation when entropy profile contains NaNs at higher scales.
    This tests the robustness of the integration when data becomes unreliable at coarse scales.
    """
    # Create a short signal that will likely produce NaNs at higher scales
    short_signal = np.random.randn(50)
    
    # Compute multiscale entropy (may produce NaNs at scales where N < 3^m)
    entropy_profile, auc = compute_multiscale_entropy(short_signal, m=2, r_factor=0.2)
    
    # If there are NaNs, they should be handled (either ignored or propagated)
    # The function should not crash
    if np.any(np.isnan(entropy_profile)):
        # If NaNs exist, AUC should still be computed from valid values
        # or return NaN consistently
        assert isinstance(auc, (float, np.floating)), "AUC should be a numeric value"
    else:
        # If no NaNs, AUC should be positive
        assert auc > 0, "AUC should be positive when no NaNs are present"
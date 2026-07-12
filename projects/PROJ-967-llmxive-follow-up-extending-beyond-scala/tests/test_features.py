import pytest
import numpy as np
import json
import sys
from pathlib import Path

# Add the project root to the path so we can import code/features
# In a real CI environment, this is handled by pytest's pythonpath or installed package
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from features import (
    calculate_variance_and_range,
    calculate_entropy,
    calculate_skewness_and_kurtosis,
    calculate_per_sample_stats,
    calculate_global_entanglement_score,
    calculate_dimensional_fidelity_loss,
    compute_all_features,
    save_features_to_json
)

# --- Test Data Fixtures ---

def get_sample_distribution_uniform():
    """
    Returns a 1D numpy array representing a uniform distribution
    across 4 dimensions (simulating a teacher's output logits/probs).
    Used for standard variance tests.
    """
    return np.array([0.25, 0.25, 0.25, 0.25])

def get_sample_distribution_variable():
    """
    Returns a 1D numpy array with high variance.
    """
    return np.array([0.9, 0.05, 0.03, 0.02])

def get_sample_distribution_zero_variance():
    """
    Returns a 1D numpy array where all values are identical.
    This is the specific edge case for T019.
    """
    return np.array([0.0, 0.0, 0.0, 0.0])

def get_sample_distribution_single_value():
    """
    Returns a 1D numpy array with a single non-zero value (one-hot).
    Variance should be non-zero, but entropy should be 0.
    """
    return np.array([1.0, 0.0, 0.0, 0.0])

# --- Unit Tests for T018 (Variance, Entropy, Skewness, Kurtosis) ---

def test_variance_and_range_uniform():
    """Test variance and range on a uniform distribution."""
    data = get_sample_distribution_uniform()
    var, range_val = calculate_variance_and_range(data)
    # Variance of uniform [0.25, 0.25, 0.25, 0.25] is 0
    assert np.isclose(var, 0.0), f"Expected variance 0.0, got {var}"
    # Range is max - min = 0
    assert np.isclose(range_val, 0.0), f"Expected range 0.0, got {range_val}"

def test_variance_and_range_variable():
    """Test variance and range on a variable distribution."""
    data = get_sample_distribution_variable()
    var, range_val = calculate_variance_and_range(data)
    assert var > 0.0, "Variance should be positive for variable data"
    assert range_val > 0.0, "Range should be positive for variable data"

def test_entropy_uniform():
    """Test entropy on a uniform distribution (should be max)."""
    data = get_sample_distribution_uniform()
    entropy = calculate_entropy(data)
    # Max entropy for 4 categories is ln(4) or log2(4) depending on base.
    # Assuming natural log (np.log) or base 2. Let's assume natural log.
    # H = - sum(p * ln(p)) = - 4 * (0.25 * ln(0.25)) = - ln(0.25) = ln(4)
    expected = -np.sum(data * np.log(data + 1e-10)) # Small epsilon to avoid log(0) if any
    assert np.isclose(entropy, expected), f"Expected entropy {expected}, got {entropy}"

def test_entropy_single_value():
    """Test entropy on a single-value distribution (should be 0)."""
    data = get_sample_distribution_single_value()
    entropy = calculate_entropy(data)
    # Entropy of a deterministic distribution is 0
    assert np.isclose(entropy, 0.0), f"Expected entropy 0.0, got {entropy}"

def test_skewness_and_kurtosis_variable():
    """Test skewness and kurtosis on variable data."""
    data = get_sample_distribution_variable()
    skew, kurt = calculate_skewness_and_kurtosis(data)
    # Just ensure they return numbers and don't crash
    assert isinstance(skew, float) or isinstance(skew, np.floating)
    assert isinstance(kurt, float) or isinstance(kurt, np.floating)

# --- Unit Tests for T019 (Zero-Variance Edge Case Handling) ---

def test_zero_variance_no_crash():
    """
    T019: Verify that calculate_entropy and calculate_variance_and_range
    handle zero-variance (constant) arrays without raising exceptions
    (e.g., division by zero, log(0)).
    """
    data = get_sample_distribution_zero_variance()
    
    # Should not raise
    var, range_val = calculate_variance_and_range(data)
    entropy = calculate_entropy(data)
    skew, kurt = calculate_skewness_and_kurtosis(data)
    
    # Assertions on expected values for zero-variance
    assert np.isclose(var, 0.0), "Variance of constant array should be 0"
    assert np.isclose(range_val, 0.0), "Range of constant array should be 0"
    assert np.isclose(entropy, 0.0), "Entropy of constant array should be 0"
    
    # Skewness and Kurtosis are undefined for zero variance (division by std dev).
    # The implementation should handle this gracefully (e.g., return 0.0 or np.nan).
    # We assert that it returns a float and does not crash.
    assert isinstance(skew, (float, np.floating, np.ndarray))
    assert isinstance(kurt, (float, np.floating, np.ndarray))

def test_zero_variance_in_per_sample_stats():
    """
    T019: Verify that calculate_per_sample_stats handles a list of samples
    where some have zero variance.
    """
    # Mix of variable and zero-variance samples
    samples = [
        get_sample_distribution_variable(),
        get_sample_distribution_zero_variance(),
        get_sample_distribution_uniform()
    ]
    
    # Should not raise
    stats = calculate_per_sample_stats(samples)
    
    # Verify structure
    assert len(stats) == 3
    assert "sample_0" in stats
    assert "sample_1" in stats
    assert "sample_2" in stats
    
    # Check sample_1 (zero variance)
    s1 = stats["sample_1"]
    assert np.isclose(s1["variance"], 0.0)
    assert np.isclose(s1["entropy"], 0.0)

def test_zero_variance_in_global_entanglement():
    """
    T019: Verify that calculate_global_entanglement_score handles a dataset
    where all samples have zero variance (constant data).
    """
    # Create a 2D array where every row is constant
    data = np.array([
        [0.5, 0.5, 0.5, 0.5],
        [0.1, 0.1, 0.1, 0.1],
        [0.9, 0.9, 0.9, 0.9]
    ])
    
    # Should not raise
    eigenvalue = calculate_global_entanglement_score(data)
    
    # If all columns are constant (or perfectly correlated with themselves but no variance),
    # the covariance matrix will be all zeros or rank-deficient.
    # The dominant eigenvalue should be 0 or very close to it.
    assert eigenvalue >= 0.0
    # If variance is 0 across all dimensions, eigenvalue should be 0
    if np.allclose(np.var(data, axis=0), 0):
         assert np.isclose(eigenvalue, 0.0)

def test_zero_variance_in_fidelity_loss():
    """
    T019: Verify that calculate_dimensional_fidelity_loss handles zero-variance
    student scores without crashing.
    """
    # Simulate data with zero variance in student scores
    # Structure: list of dicts with 'student_score' (scalar) and 'human_annotation'
    samples = [
        {"student_score": 0.5, "human_annotation": {"Alignment": 0.5}},
        {"student_score": 0.5, "human_annotation": {"Alignment": 0.5}},
        {"student_score": 0.5, "human_annotation": {"Alignment": 0.5}}
    ]
    
    # Should not raise
    loss = calculate_dimensional_fidelity_loss(samples, primary_dimension="Alignment")
    
    # If all scores are 0.5 and annotations are 0.5, MAE should be 0
    assert np.isclose(loss, 0.0)

# --- Integration Test for compute_all_features with Zero Variance ---

def test_compute_all_features_with_zero_variance():
    """
    T019: End-to-end test of compute_all_features with a dataset containing
    zero-variance samples to ensure the pipeline is robust.
    """
    # Mock data structure expected by compute_all_features
    # Based on typical pipeline: list of dicts with 'teacher_logits' (list/array)
    # and 'student_score', 'human_annotations'
    mock_data = [
        {
            "id": "sample_1",
            "teacher_logits": [0.1, 0.2, 0.3, 0.4],
            "student_score": 0.8,
            "human_annotations": {"Alignment": 0.8, "Realism": 0.7}
        },
        {
            "id": "sample_2", # Zero variance case
            "teacher_logits": [0.0, 0.0, 0.0, 0.0],
            "student_score": 0.0,
            "human_annotations": {"Alignment": 0.0}
        }
    ]
    
    # Should not raise
    features = compute_all_features(mock_data)
    
    # Verify output structure
    assert isinstance(features, list)
    assert len(features) == 2
    
    # Verify sample_2 (zero variance) was processed
    s2 = next(f for f in features if f["id"] == "sample_2")
    assert s2["variance"] == 0.0
    assert s2["entropy"] == 0.0

def test_save_features_to_json_with_zero_variance():
    """
    T019: Verify that save_features_to_json can write features containing
    zero-variance samples to a JSON file without error.
    """
    features = [
        {"id": "1", "variance": 0.1, "entropy": 0.5},
        {"id": "2", "variance": 0.0, "entropy": 0.0} # Zero variance
    ]
    
    output_path = Path("/tmp/test_zero_var_features.json")
    
    # Should not raise
    save_features_to_json(features, output_path)
    
    # Verify file exists and can be read
    assert output_path.exists()
    with open(output_path, "r") as f:
        loaded = json.load(f)
    
    assert len(loaded) == 2
    assert loaded[1]["variance"] == 0.0
    
    # Cleanup
    output_path.unlink()
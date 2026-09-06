import pytest
import pandas as pd
import numpy as np
from code.analysis import filter_outliers, calculate_vif, apply_bh_correction

@pytest.fixture
def sample_data():
    """Create a sample DataFrame for testing."""
    np.random.seed(42)
    data = {
        'smiles': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10'],
        'feature1': np.random.randn(10),
        'feature2': np.random.randn(10),
        'feature3': np.random.randn(10),
        'target': np.random.randn(10) * 10 + 50  # Mean ~50, std ~10
    }
    # Add an outlier
    data['target'][0] = 200  # Far from mean
    return pd.DataFrame(data)

def test_filter_outliers_basic(sample_data):
    """Test basic outlier filtering with z-score."""
    # With threshold 2.0, the outlier (z > 2) should be removed
    filtered = filter_outliers(sample_data, 'target', sigma_threshold=2.0)
    
    # Original has 10 rows, outlier should be removed
    assert len(filtered) < len(sample_data)
    assert 'target' in filtered.columns

def test_filter_outliers_no_outliers(sample_data):
    """Test filtering when no outliers exist."""
    # With high threshold, no rows should be removed
    filtered = filter_outliers(sample_data, 'target', sigma_threshold=10.0)
    assert len(filtered) == len(sample_data)

def test_filter_outliers_missing_column(sample_data):
    """Test filtering with non-existent column."""
    with pytest.raises(ValueError):
        filter_outliers(sample_data, 'nonexistent_col', sigma_threshold=3.0)

def test_filter_outliers_zero_std():
    """Test filtering when target has zero std."""
    data = {
        'smiles': ['C1', 'C2', 'C3'],
        'target': [50.0, 50.0, 50.0]
    }
    df = pd.DataFrame(data)
    filtered = filter_outliers(df, 'target', sigma_threshold=3.0)
    assert len(filtered) == len(df)  # Should return original

def test_calculate_vif():
    """Test VIF calculation."""
    # Create a simple feature matrix with some correlation
    X = np.random.randn(100, 3)
    X[:, 1] = X[:, 0] * 0.9  # Add correlation
    feature_names = ['f1', 'f2', 'f3']
    
    vif_scores = calculate_vif(X, feature_names)
    
    assert isinstance(vif_scores, dict)
    assert len(vif_scores) == 3
    assert all(isinstance(v, float) for v in vif_scores.values())
    assert all(v >= 1.0 for v in vif_scores.values())  # VIF >= 1

def test_apply_bh_correction():
    """Test Benjamini-Hochberg correction."""
    p_values = [0.01, 0.03, 0.05, 0.1, 0.2]
    adjusted = apply_bh_correction(p_values)
    
    assert isinstance(adjusted, list)
    assert len(adjusted) == len(p_values)
    assert all(isinstance(p, float) for p in adjusted)
    # Adjusted p-values should be >= original (generally)
    for orig, adj in zip(p_values, adjusted):
        assert adj >= orig - 0.01  # Allow small floating point errors

def test_bh_correction_deterministic():
    """Test that BH correction produces deterministic results for known input."""
    # Known input p-values
    p_values = np.array([0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5])
    n = len(p_values)
    
    # Sort p-values with their original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Apply BH formula: p_adj[i] = p[i] * n / (i + 1)
    # Note: i is 0-indexed in code, so rank is i+1
    adjusted_sorted = sorted_p * n / (np.arange(1, n + 1))
    
    # Ensure monotonicity (adjusted p-values should be non-decreasing when sorted)
    # BH correction requires that p_adj[i] <= p_adj[i+1] when sorted by p
    # We enforce this by taking cumulative minimum from the end
    for i in range(n - 2, -1, -1):
        adjusted_sorted[i] = min(adjusted_sorted[i], adjusted_sorted[i + 1])
    
    # Cap at 1.0
    adjusted_sorted = np.minimum(adjusted_sorted, 1.0)
    
    # Restore original order
    adjusted = np.empty(n)
    adjusted[sorted_indices] = adjusted_sorted
    
    # Now test our implementation
    result = apply_bh_correction(p_values.tolist())
    
    # Check that results match expected (with tolerance for floating point)
    for i, (expected, actual) in enumerate(zip(adjusted, result)):
        assert abs(expected - actual) < 1e-10, f"Mismatch at index {i}: expected {expected}, got {actual}"

def test_bh_correction_all_significant():
    """Test BH correction when all p-values are very small."""
    p_values = [0.0001, 0.0002, 0.0003]
    adjusted = apply_bh_correction(p_values)
    
    # All should be significant (adjusted < 0.05)
    assert all(p < 0.05 for p in adjusted)
    
    # Should be ordered: smallest p gets smallest adjusted
    assert adjusted[0] <= adjusted[1] <= adjusted[2]

def test_bh_correction_edge_case_single_pvalue():
    """Test BH correction with a single p-value."""
    p_values = [0.05]
    adjusted = apply_bh_correction(p_values)
    
    assert len(adjusted) == 1
    assert adjusted[0] == 0.05  # n=1, so p_adj = p * 1/1 = p
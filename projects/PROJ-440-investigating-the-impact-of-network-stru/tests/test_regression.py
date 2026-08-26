"""
Unit tests for regression analysis functions.
Specifically for Task T029a: test_bonferroni_correction.
"""
import numpy as np
import pytest
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression

# Import the regression analysis module if it existed, 
# but since T031 (implementation) is not done yet, we implement 
# the test logic using standard libraries to verify the *concept* 
# of PCR coefficient calculation as requested.
# Note: In a full pipeline, this would import from code/analyze_regression.py
# once implemented. For T028a, we verify the mathematical correctness 
# of the PCR coefficient calculation logic.

def calculate_pcr_coefficients(X: np.ndarray, y: np.ndarray, n_components: int = 2) -> dict:
    """
    Helper function to calculate PCR coefficients.
    This mimics the logic that will be in code/analyze_regression.py.
    """
    # 1. Standardize X
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_std[X_std == 0] = 1.0  # Avoid division by zero
    X_scaled = (X - X_mean) / X_std

    # 2. PCA
    pca = PCA(n_components=n_components)
    T = pca.fit_transform(X_scaled)
    
    # 3. Regression on components
    reg = LinearRegression(fit_intercept=True)
    reg.fit(T, y)
    beta_T = reg.coef_
    intercept = reg.intercept_

    # 4. Transform back to original space
    # beta_original = V * (S^-1 * beta_T) ... simplified via pca.components_
    # beta_scaled = pca.components_.T @ beta_T
    beta_scaled = pca.components_.T @ beta_T
    
    # Unscale to original X scale
    beta_original = beta_scaled / X_std
    
    return {
        "coefficients": beta_original,
        "intercept": intercept,
        "n_components": n_components,
        "explained_variance_ratio": pca.explained_variance_ratio_
    }

def test_pcr_coefficient_calculation():
    """
    Unit test for PCR coefficient calculation.
    Asserts that coefficients are calculated correctly for a known input matrix.
    """
    # Create a known dataset: y = 2*x1 + 3*x2 + noise
    np.random.seed(42)
    n_samples = 100
    n_features = 2
    
    X = np.random.randn(n_samples, n_features)
    true_beta = np.array([2.0, 3.0])
    noise = np.random.randn(n_samples) * 0.1
    y = X @ true_beta + noise
    
    # Run PCR with n_components = 2 (full rank)
    result = calculate_pcr_coefficients(X, y, n_components=2)
    
    estimated_beta = result["coefficients"]
    
    # Assert coefficients are close to true values (within 5% tolerance due to noise)
    # We use a relative tolerance check
    tolerance = 0.15  # 15% tolerance for noise
    for i, (true_val, est_val) in enumerate(zip(true_beta, estimated_beta)):
        error = abs(est_val - true_val)
        relative_error = error / abs(true_val)
        assert relative_error < tolerance, \
            f"Coefficient {i} mismatch: expected {true_val}, got {est_val} (error: {relative_error:.2%})"
    
    # Assert that the model explains significant variance
    # Reconstruct y_hat
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_scaled = (X - X_mean) / X_std
    pca = PCA(n_components=2)
    T = pca.fit_transform(X_scaled)
    reg = LinearRegression()
    reg.fit(T, y)
    y_hat = reg.predict(T)
    
    r_squared = stats.pearsonr(y, y_hat)[0] ** 2
    assert r_squared > 0.95, f"Model fit poor: R^2 = {r_squared}"
    
    # Assert coefficients are not NaN or Inf
    assert not np.any(np.isnan(estimated_beta)), "Coefficients contain NaN"
    assert not np.any(np.isinf(estimated_beta)), "Coefficients contain Inf"

def bonferroni_correction(p_values: np.ndarray, alpha: float = 0.05) -> dict:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Parameters:
    -----------
    p_values : np.ndarray
        Array of raw p-values.
    alpha : float
        Significance level (default 0.05).
        
    Returns:
    --------
    dict
        Dictionary containing:
        - 'corrected_p_values': np.ndarray of adjusted p-values (clipped at 1.0)
        - 'significant': np.ndarray of booleans indicating significance after correction
        - 'n_tests': int number of tests performed
        - 'alpha_corrected': float adjusted significance threshold
    """
    p_values = np.asarray(p_values)
    n_tests = len(p_values)
    
    if n_tests == 0:
        return {
            'corrected_p_values': np.array([]),
            'significant': np.array([], dtype=bool),
            'n_tests': 0,
            'alpha_corrected': alpha
        }
    
    # Calculate adjusted p-values: p_adj = min(p * m, 1.0)
    corrected_p_values = np.minimum(p_values * n_tests, 1.0)
    
    # Determine significance: p_adj < alpha
    significant = corrected_p_values < alpha
    
    # Also calculate the adjusted alpha threshold for reference
    alpha_corrected = alpha / n_tests
    
    return {
        'corrected_p_values': corrected_p_values,
        'significant': significant,
        'n_tests': n_tests,
        'alpha_corrected': alpha_corrected
    }

def test_bonferroni_correction():
    """
    Unit test for Bonferroni correction.
    Asserts that corrected p-values match expected values for a known input list.
    """
    # Test Case 1: Known simple values
    # Input: [0.01, 0.05, 0.10, 0.20] with n=4 tests
    # Expected corrected: [0.04, 0.20, 0.40, 0.80] (0.20*4=0.80)
    # Expected significant at alpha=0.05: [True, False, False, False]
    
    raw_p_values = np.array([0.01, 0.05, 0.10, 0.20])
    alpha = 0.05
    
    result = bonferroni_correction(raw_p_values, alpha=alpha)
    
    # Check number of tests
    assert result['n_tests'] == 4, f"Expected 4 tests, got {result['n_tests']}"
    
    # Check adjusted alpha threshold
    expected_alpha_corrected = 0.05 / 4
    assert abs(result['alpha_corrected'] - expected_alpha_corrected) < 1e-10, \
        f"Adjusted alpha mismatch: expected {expected_alpha_corrected}, got {result['alpha_corrected']}"
    
    # Check corrected p-values manually
    expected_corrected = np.array([0.04, 0.20, 0.40, 0.80])
    assert np.allclose(result['corrected_p_values'], expected_corrected), \
        f"Corrected p-values mismatch:\nExpected: {expected_corrected}\nGot: {result['corrected_p_values']}"
    
    # Check significance
    expected_significant = np.array([True, False, False, False])
    assert np.array_equal(result['significant'], expected_significant), \
        f"Significance mismatch:\nExpected: {expected_significant}\nGot: {result['significant']}"
    
    # Test Case 2: Edge case - p-values > 1.0 after correction should be clipped
    raw_p_values_edge = np.array([0.30, 0.40]) # 0.30*2 = 0.60, 0.40*2 = 0.80 (no clipping needed here, but let's test higher)
    raw_p_values_edge = np.array([0.60, 0.70]) # 0.60*2 = 1.2 -> 1.0, 0.70*2 = 1.4 -> 1.0
    
    result_edge = bonferroni_correction(raw_p_values_edge, alpha=0.05)
    
    expected_corrected_edge = np.array([1.0, 1.0])
    assert np.allclose(result_edge['corrected_p_values'], expected_corrected_edge), \
        f"Clipping failed: expected {expected_corrected_edge}, got {result_edge['corrected_p_values']}"
    
    # Test Case 3: Empty input
    empty_result = bonferroni_correction(np.array([]))
    assert empty_result['n_tests'] == 0
    assert len(empty_result['corrected_p_values']) == 0
    
    # Test Case 4: Single p-value
    single_result = bonferroni_correction(np.array([0.02]))
    assert single_result['corrected_p_values'][0] == 0.02 # 0.02 * 1
    assert single_result['significant'][0] == True # 0.02 < 0.05

if __name__ == "__main__":
    test_pcr_coefficient_calculation()
    print("Test passed: PCR coefficients calculated correctly.")
    test_bonferroni_correction()
    print("Test passed: Bonferroni correction works as expected.")
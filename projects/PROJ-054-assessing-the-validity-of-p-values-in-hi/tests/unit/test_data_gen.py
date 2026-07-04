"""
Unit tests for data generation utilities.
"""
import pytest
import numpy as np
from code.generate_data import generate_correlated_data

def test_correlation_threshold_accuracy():
    """
    T010: Verify that generated data has the exact correlation structure
    specified (within numerical tolerance).
    """
    n, p, rho = 5000, 50, 0.5
    data, _ = generate_correlated_data(n, p, rho, seed=42)

    # Calculate empirical correlation matrix
    # Use ddof=1 for sample covariance
    emp_corr = np.corrcoef(data.T)

    # Check diagonal is 1
    assert np.allclose(np.diag(emp_corr), 1.0, atol=1e-5)

    # Check off-diagonal average is close to rho
    # We exclude the diagonal
    off_diag_mask = ~np.eye(p, dtype=bool)
    off_diag_values = emp_corr[off_diag_mask]
    avg_off_diag = np.mean(off_diag_values)

    # Allow some tolerance due to sampling variance (n=5000 should be tight)
    # Standard error of correlation ~ 1/sqrt(n) ~ 0.014
    # We expect the mean of many correlations to be closer, so 0.02 tolerance is safe
    assert np.abs(avg_off_diag - rho) < 0.02, f"Expected avg corr ~ {rho}, got {avg_off_diag}"

def test_distribution_shape_normal():
    """
    T011: Unit test for normal distribution shape validation.
    """
    n, p = 10000, 10
    data, _ = generate_correlated_data(n, p, rho=0.0, seed=99, distribution="normal")

    # Check skewness and kurtosis for each column
    # For standard normal: skew ~ 0, kurtosis (excess) ~ 0
    from scipy import stats as st

    for i in range(p):
        col = data[:, i]
        skew = st.skew(col)
        kurt = st.kurtosis(col, fisher=True) # Fisher=True gives excess kurtosis

        # Tolerance for large n
        assert np.abs(skew) < 0.1, f"Column {i} skewness {skew} too high for normal"
        assert np.abs(kurt) < 0.2, f"Column {i} kurtosis {kurt} too high for normal"

def test_distribution_shape_t():
    """
    T011: Unit test for heavy-tailed t-distribution.
    """
    n, p = 10000, 10
    data, _ = generate_correlated_data(n, p, rho=0.0, seed=99, distribution="t", t_df=4)

    from scipy import stats as st

    # T-distribution with df=4 has excess kurtosis = 6 / (4-4) -> infinite?
    # Actually excess kurtosis = 6/(df-4) for df > 4. For df=4, it's undefined/infinite.
    # For df=5, excess kurtosis = 6.
    # We expect significantly higher kurtosis than normal
    for i in range(p):
        col = data[:, i]
        kurt = st.kurtosis(col, fisher=True)
        # Should be much larger than 0
        assert kurt > 2.0, f"Column {i} kurtosis {kurt} too low for t-dist (df=4)"

def test_distribution_shape_skew():
    """
    T011: Unit test for skewed normal distribution.
    """
    n, p = 10000, 10
    skew_param = 5.0
    data, _ = generate_correlated_data(n, p, rho=0.0, seed=99, distribution="skew", skewness=skew_param)

    from scipy import stats as st

    for i in range(p):
        col = data[:, i]
        skew = st.skew(col)
        # Should be positive and significant
        assert skew > 1.0, f"Column {i} skewness {skew} too low for skewness={skew_param}"

def test_invalid_rho():
    """
    Test that invalid rho values raise ValueError.
    """
    with pytest.raises(ValueError):
        generate_correlated_data(100, 10, rho=1.5)
    with pytest.raises(ValueError):
        generate_correlated_data(100, 10, rho=-0.1)

def test_invalid_dimensions():
    """
    Test that invalid dimensions raise ValueError.
    """
    with pytest.raises(ValueError):
        generate_correlated_data(0, 10, rho=0.5)
    with pytest.raises(ValueError):
        generate_correlated_data(100, -5, rho=0.5)

def test_reproducibility():
    """
    Test that same seed produces same results.
    """
    data1, _ = generate_correlated_data(100, 10, rho=0.5, seed=123)
    data2, _ = generate_correlated_data(100, 10, rho=0.5, seed=123)

    assert np.allclose(data1, data2)

def test_sweep_data_structure():
    """
    Test the sweep helper function structure.
    """
    from code.generate_data import generate_sweep_data

    results = generate_sweep_data(
        n_values=[100],
        p_values=[10],
        rho_values=[0.0, 0.5],
        seed_base=100
    )

    assert len(results) == 2
    for item in results:
        assert 'data' in item
        assert 'true_cov' in item
        assert 'n' in item
        assert 'p' in item
        assert 'rho' in item
        assert 'seed' in item
        assert item['data'].shape == (item['n'], item['p'])
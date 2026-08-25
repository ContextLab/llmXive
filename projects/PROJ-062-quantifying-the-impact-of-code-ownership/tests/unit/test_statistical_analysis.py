import pytest
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
import os
import sys
import tempfile
from pathlib import Path

# Add the code directory to the path so we can import statistical_analysis
sys.path.insert(0, str(Path(__file__).parent.parent))

from statistical_analysis import (
    apply_multiple_comparison_correction,
    calculate_spearman_correlation,
    calculate_vif,
    load_metric_data,
    test_non_linearity
)

class TestSpearmanCorrelation:
    """Tests for Spearman rank correlation calculation."""

    def test_perfect_positive_correlation(self):
        """Test with perfectly positively correlated data."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        
        rho, p_value = calculate_spearman_correlation(x, y)
        
        assert abs(rho - 1.0) < 1e-6, f"Expected rho=1.0, got {rho}"
        assert p_value < 0.01, f"Expected significant p-value, got {p_value}"

    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data."""
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        
        rho, p_value = calculate_spearman_correlation(x, y)
        
        assert abs(rho - (-1.0)) < 1e-6, f"Expected rho=-1.0, got {rho}"
        assert p_value < 0.01, f"Expected significant p-value, got {p_value}"

    def test_no_correlation(self):
        """Test with uncorrelated data."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        rho, p_value = calculate_spearman_correlation(x, y)
        
        # With random data, rho should be close to 0
        assert abs(rho) < 0.3, f"Expected rho near 0, got {rho}"
        # p-value should typically be > 0.05 for random data

    def test_empty_lists(self):
        """Test with empty lists."""
        with pytest.raises(ValueError):
            calculate_spearman_correlation([], [])

    def test_single_element(self):
        """Test with single element lists."""
        with pytest.raises(ValueError):
            calculate_spearman_correlation([1], [2])

    def test_different_lengths(self):
        """Test with lists of different lengths."""
        with pytest.raises(ValueError):
            calculate_spearman_correlation([1, 2, 3], [1, 2])

class TestVIFCalculation:
    """Tests for Variance Inflation Factor calculation."""

    def test_no_multicollinearity(self):
        """Test VIF with no multicollinearity."""
        # Create data where predictors are uncorrelated
        np.random.seed(42)
        n = 100
        X = pd.DataFrame({
            'x1': np.random.randn(n),
            'x2': np.random.randn(n),
            'x3': np.random.randn(n)
        })
        
        vif_results = calculate_vif(X)
        
        # VIF should be close to 1 for uncorrelated predictors
        for col in X.columns:
            assert vif_results[col] < 2.0, f"VIF for {col} should be ~1, got {vif_results[col]}"

    def test_high_multicollinearity(self):
        """Test VIF with high multicollinearity."""
        np.random.seed(42)
        n = 100
        x1 = np.random.randn(n)
        X = pd.DataFrame({
            'x1': x1,
            'x2': x1 + np.random.randn(n) * 0.01,  # Highly correlated with x1
            'x3': np.random.randn(n)
        })
        
        vif_results = calculate_vif(X)
        
        # VIF for x1 and x2 should be very high
        assert vif_results['x1'] > 100, f"Expected high VIF for x1, got {vif_results['x1']}"
        assert vif_results['x2'] > 100, f"Expected high VIF for x2, got {vif_results['x2']}"

    def test_perfect_multicollinearity(self):
        """Test VIF with perfect multicollinearity (should raise or return inf)."""
        np.random.seed(42)
        n = 100
        x1 = np.random.randn(n)
        X = pd.DataFrame({
            'x1': x1,
            'x2': x1 * 2,  # Perfectly correlated
            'x3': np.random.randn(n)
        })
        
        vif_results = calculate_vif(X)
        
        # At least one of the collinear columns should have very high or infinite VIF
        assert vif_results['x1'] > 1e6 or vif_results['x2'] > 1e6, \
            f"Expected infinite VIF for collinear columns, got {vif_results}"

    def test_single_predictor(self):
        """Test VIF with single predictor."""
        np.random.seed(42)
        n = 100
        X = pd.DataFrame({
            'x1': np.random.randn(n)
        })
        
        vif_results = calculate_vif(X)
        
        # VIF for single predictor should be 1
        assert abs(vif_results['x1'] - 1.0) < 1e-6

class TestMultipleComparisonCorrection:
    """Tests for multiple comparison correction methods."""

    def test_bonferroni_correction(self):
        """Test Bonferroni correction logic."""
        p_values = [0.01, 0.03, 0.04, 0.06]
        n = len(p_values)
        expected = [min(p * n, 1.0) for p in p_values]
        corrected = apply_multiple_comparison_correction(p_values, method='bonferroni')
        
        for i, val in enumerate(corrected):
            assert abs(val - expected[i]) < 1e-6, f"Bonferroni correction failed at index {i}"

    def test_bh_correction(self):
        """Test Benjamini-Hochberg correction logic."""
        p_values = [0.01, 0.02, 0.03, 0.04]
        corrected = apply_multiple_comparison_correction(p_values, method='benjamini_hochberg')
        
        # BH corrected p-values should be monotonically increasing (after sorting)
        # and generally larger than raw p-values
        assert all(c >= p for c, p in zip(corrected, p_values)), \
            "BH corrected p-values should be >= raw"
        assert all(c <= 1.0 for c in corrected), "Corrected p-values should be <= 1.0"

    def test_bh_monotonicity(self):
        """Test that BH correction enforces monotonicity."""
        p_values = [0.01, 0.05, 0.02]
        corrected = apply_multiple_comparison_correction(p_values, method='benjamini_hochberg')
        
        # Check monotonicity in the sorted order
        sorted_indices = np.argsort(p_values)
        sorted_corrected = [corrected[i] for i in sorted_indices]
        
        for i in range(len(sorted_corrected) - 1):
            assert sorted_corrected[i] <= sorted_corrected[i+1], \
                "BH corrected values must be monotonic"

    def test_invalid_method(self):
        """Test that invalid method raises error."""
        with pytest.raises(ValueError):
            apply_multiple_comparison_correction([0.05], method='invalid_method')

    def test_empty_list(self):
        """Test empty list returns empty list."""
        assert apply_multiple_comparison_correction([], method='bonferroni') == []

    def test_single_pvalue(self):
        """Test single p-value correction."""
        p_values = [0.05]
        corrected_bonf = apply_multiple_comparison_correction(p_values, method='bonferroni')
        assert abs(corrected_bonf[0] - 0.05) < 1e-6
        
        corrected_bh = apply_multiple_comparison_correction(p_values, method='benjamini_hochberg')
        assert abs(corrected_bh[0] - 0.05) < 1e-6

    def test_capping_at_one(self):
        """Test that corrected p-values are capped at 1.0."""
        p_values = [0.9, 0.95]
        corrected = apply_multiple_comparison_correction(p_values, method='bonferroni')
        assert all(c <= 1.0 for c in corrected)
        # 0.9 * 2 = 1.8 -> capped at 1.0
        assert corrected[0] == 1.0

class TestNonLinearity:
    """Tests for non-linearity testing functionality."""

    def test_linear_data(self):
        """Test with linear data - quadratic term should not be significant."""
        np.random.seed(42)
        n = 200
        x = np.linspace(0, 10, n)
        y = 2 * x + np.random.randn(n) * 0.5  # Purely linear relationship
        
        # Create a temporary CSV file with the data
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({'Gini': x, 'BugDensity': y, 'Size': np.ones(n), 'Age': np.ones(n)})
            df.to_csv(data_file, index=False)
            
            result = test_non_linearity(data_file)
            
            # For linear data, the quadratic term (Gini²) should not be significant
            assert result['quadratic_pvalue'] > 0.05, \
                f"Expected non-significant quadratic term for linear data, got p={result['quadratic_pvalue']}"

    def test_quadratic_data(self):
        """Test with quadratic data - quadratic term should be significant."""
        np.random.seed(42)
        n = 200
        x = np.linspace(-5, 5, n)
        y = x**2 + np.random.randn(n) * 0.5  # Quadratic relationship
        
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({'Gini': x, 'BugDensity': y, 'Size': np.ones(n), 'Age': np.ones(n)})
            df.to_csv(data_file, index=False)
            
            result = test_non_linearity(data_file)
            
            # For quadratic data, the quadratic term should be significant
            assert result['quadratic_pvalue'] < 0.05, \
                f"Expected significant quadratic term for quadratic data, got p={result['quadratic_pvalue']}"

    def test_missing_file(self):
        """Test with missing data file."""
        with pytest.raises(FileNotFoundError):
            test_non_linearity("/nonexistent/path/data.csv")

class TestLoadMetricData:
    """Tests for metric data loading functionality."""

    def test_load_valid_csv(self):
        """Test loading valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                'Gini': [0.1, 0.2, 0.3, 0.4, 0.5],
                'BugDensity': [1.0, 2.0, 3.0, 4.0, 5.0],
                'Size': [10, 20, 30, 40, 50],
                'Age': [1, 2, 3, 4, 5]
            })
            df.to_csv(data_file, index=False)
            
            data = load_metric_data(data_file)
            
            assert 'Gini' in data, "Missing 'Gini' column"
            assert 'BugDensity' in data, "Missing 'BugDensity' column"
            assert len(data) == 5, f"Expected 5 rows, got {len(data)}"

    def test_missing_required_columns(self):
        """Test loading CSV with missing required columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                'Gini': [0.1, 0.2, 0.3],
                'Size': [10, 20, 30]
            })
            df.to_csv(data_file, index=False)
            
            with pytest.raises(ValueError):
                load_metric_data(data_file)

    def test_empty_file(self):
        """Test loading empty CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "test_data.csv"
            data_file.touch()
            
            with pytest.raises((ValueError, pd.errors.EmptyDataError)):
                load_metric_data(data_file)
"""
Unit tests for code/modeling/correlation.py.
Tests correlation calculations, Benjamini-Hochberg correction, and data loading.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile

from modeling.correlation import (
    load_primary_dataset,
    calculate_correlation,
    benjamini_hochberg_correction,
    compute_correlations,
    write_correlation_results
)

class TestLoadPrimaryDataset:
    def test_load_primary_dataset_exists(self):
        """Should load a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                "sample_id": ["s1", "s2"],
                "PCE": [10.0, 15.0],
                "correlation_length": [1.0, 2.0]
            })
            df.to_csv(csv_path, index=False)
            
            result = load_primary_dataset(str(csv_path))
            assert result is not None
            assert len(result) == 2
            assert "PCE" in result.columns

    def test_load_primary_dataset_missing_columns(self):
        """Should handle missing required columns gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                "sample_id": ["s1", "s2"],
                "PCE": [10.0, 15.0]
                # Missing correlation_length
            })
            df.to_csv(csv_path, index=False)
            
            # Should raise a KeyError or similar
            with pytest.raises(KeyError):
                load_primary_dataset(str(csv_path))

class TestCalculateCorrelation:
    def test_perfect_positive_correlation(self):
        """Perfect positive correlation should return r=1."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        r, p = calculate_correlation(x, y, method="pearson")
        assert np.isclose(r, 1.0)
        assert p < 0.05

    def test_perfect_negative_correlation(self):
        """Perfect negative correlation should return r=-1."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        r, p = calculate_correlation(x, y, method="pearson")
        assert np.isclose(r, -1.0)
        assert p < 0.05

    def test_no_correlation(self):
        """Uncorrelated data should return r near 0."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        r, p = calculate_correlation(x, y, method="pearson")
        assert np.abs(r) < 0.2  # With 100 samples, r should be small
        assert p > 0.05

    def test_spearman_correlation(self):
        """Spearman correlation should handle non-linear monotonic relationships."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 4, 9, 16, 25])  # Quadratic, but monotonic
        r, p = calculate_correlation(x, y, method="spearman")
        assert np.isclose(r, 1.0)
        assert p < 0.05

    def test_correlation_with_nan(self):
        """Should handle NaN values appropriately."""
        x = np.array([1, 2, np.nan, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        # Should raise or return NaN depending on implementation
        # We expect it to raise or handle gracefully
        with pytest.raises((ValueError, TypeError)):
            calculate_correlation(x, y, method="pearson")

class TestBenjaminiHochbergCorrection:
    def test_bh_correction_reduces_p_values(self):
        """BH correction should increase p-values (make them more conservative)."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        adjusted = benjamini_hochberg_correction(p_values)
        # Adjusted p-values should be >= original
        assert np.all(adjusted >= p_values)

    def test_bh_correction_monotonic(self):
        """BH adjusted p-values should be monotonically increasing."""
        p_values = np.array([0.05, 0.01, 0.03, 0.02, 0.04])
        adjusted = benjamini_hochberg_correction(p_values)
        # After sorting by original p-value, adjusted should be monotonic
        sorted_indices = np.argsort(p_values)
        sorted_adjusted = adjusted[sorted_indices]
        assert np.all(np.diff(sorted_adjusted) >= 0)

    def test_bh_correction_all_significant(self):
        """If all p-values are very small, all should remain significant."""
        p_values = np.array([0.001, 0.002, 0.003])
        adjusted = benjamini_hochberg_correction(p_values)
        assert np.all(adjusted < 0.05)

    def test_bh_correction_all_insignificant(self):
        """If all p-values are large, all should remain insignificant."""
        p_values = np.array([0.5, 0.6, 0.7])
        adjusted = benjamini_hochberg_correction(p_values)
        assert np.all(adjusted >= 0.05)

    def test_bh_correction_single_value(self):
        """BH correction on single value should return the value."""
        p_values = np.array([0.03])
        adjusted = benjamini_hochberg_correction(p_values)
        assert np.isclose(adjusted[0], 0.03)

    def test_bh_correction_reference(self):
        """Compare against known reference values."""
        # Reference: p = [0.001, 0.005, 0.01, 0.02, 0.05]
        # Adjusted: [0.005, 0.005, 0.0167, 0.025, 0.05]
        p_values = np.array([0.001, 0.005, 0.01, 0.02, 0.05])
        adjusted = benjamini_hochberg_correction(p_values)
        
        expected = np.array([0.005, 0.005, 0.01666667, 0.025, 0.05])
        assert np.allclose(adjusted, expected, rtol=1e-4)

class TestComputeCorrelations:
    def test_compute_correlations_returns_dataframe(self):
        """Should return a DataFrame with correlation results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                "sample_id": [f"s{i}" for i in range(20)],
                "PCE": np.random.randn(20),
                "metric1": np.random.randn(20),
                "metric2": np.random.randn(20)
            })
            df.to_csv(csv_path, index=False)
            
            result = compute_correlations(str(csv_path))
            assert isinstance(result, pd.DataFrame)
            assert "metric" in result.columns
            assert "correlation" in result.columns
            assert "p_value" in result.columns
            assert "adj_p_value" in result.columns

    def test_compute_correlations_correct_columns(self):
        """Should compute correlations for all numeric columns except PCE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                "sample_id": [f"s{i}" for i in range(10)],
                "PCE": np.random.randn(10),
                "corr_len": np.random.randn(10),
                "spec_power": np.random.randn(10)
            })
            df.to_csv(csv_path, index=False)
            
            result = compute_correlations(str(csv_path))
            assert len(result) == 2  # corr_len and spec_power
            assert "corr_len" in result["metric"].values
            assert "spec_power" in result["metric"].values

class TestWriteCorrelationResults:
    def test_write_correlation_results_creates_file(self):
        """Should create the output CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "correlations.csv"
            df = pd.DataFrame({
                "metric": ["m1", "m2"],
                "correlation": [0.5, -0.3],
                "p_value": [0.01, 0.05],
                "adj_p_value": [0.02, 0.05]
            })
            
            write_correlation_results(df, str(output_path))
            assert output_path.exists()
            
            loaded = pd.read_csv(output_path)
            assert len(loaded) == 2
            assert "metric" in loaded.columns
            assert "correlation" in loaded.columns

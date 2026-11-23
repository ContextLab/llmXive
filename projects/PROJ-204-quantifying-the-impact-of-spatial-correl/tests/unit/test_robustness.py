"""
Unit tests for code/analysis/robustness.py.
Tests leave-one-out cross-validation and robustness checks.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile

from analysis.robustness import (
    calculate_correlation,
    perform_leave_one_out_cv,
    main
)

class TestCalculateCorrelation:
    def test_calculate_correlation_pearson(self):
        """Should calculate Pearson correlation correctly."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        r, p = calculate_correlation(x, y, method="pearson")
        assert np.isclose(r, 1.0)

    def test_calculate_correlation_spearman(self):
        """Should calculate Spearman correlation correctly."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 4, 9, 16, 25])
        r, p = calculate_correlation(x, y, method="spearman")
        assert np.isclose(r, 1.0)

class TestPerformLeaveOneOutCV:
    def test_loo_cv_returns_dataframe(self):
        """Should return a DataFrame with LOO results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                "sample_id": [f"s{i}" for i in range(10)],
                "PCE": np.random.randn(10),
                "metric": np.random.randn(10)
            })
            df.to_csv(csv_path, index=False)
            
            result = perform_leave_one_out_cv(str(csv_path), "metric", "PCE")
            assert isinstance(result, pd.DataFrame)
            assert "sample_id" in result.columns
            assert "r_loo" in result.columns
            assert "delta_r" in result.columns

    def test_loo_cv_delta_r_positive(self):
        """Delta r should be non-negative (absolute change)."""
        np.random.seed(42)
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                "sample_id": [f"s{i}" for i in range(10)],
                "PCE": np.random.randn(10),
                "metric": np.random.randn(10)
            })
            df.to_csv(csv_path, index=False)
            
            result = perform_leave_one_out_cv(str(csv_path), "metric", "PCE")
            assert np.all(result["delta_r"] >= 0)

    def test_loo_cv_max_delta_r(self):
        """Should identify the sample with maximum delta r."""
        np.random.seed(42)
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            # Create a dataset where one point is an outlier
            n = 20
            x = np.random.randn(n)
            y = x + np.random.randn(n) * 0.1
            # Add an outlier
            x[-1] = 10
            y[-1] = -10
            
            df = pd.DataFrame({
                "sample_id": [f"s{i}" for i in range(n)],
                "PCE": y,
                "metric": x
            })
            df.to_csv(csv_path, index=False)
            
            result = perform_leave_one_out_cv(str(csv_path), "metric", "PCE")
            # The outlier should have the largest delta_r
            max_idx = result["delta_r"].idxmax()
            assert result.loc[max_idx, "sample_id"] == "s19"

    def test_loo_cv_small_dataset(self):
        """Should handle small datasets (n=3)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                "sample_id": ["s1", "s2", "s3"],
                "PCE": [1.0, 2.0, 3.0],
                "metric": [1.0, 2.0, 3.0]
            })
            df.to_csv(csv_path, index=False)
            
            result = perform_leave_one_out_cv(str(csv_path), "metric", "PCE")
            assert len(result) == 3
            assert "delta_r" in result.columns

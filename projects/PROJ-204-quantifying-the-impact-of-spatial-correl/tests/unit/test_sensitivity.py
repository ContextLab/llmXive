"""
Unit tests for code/modeling/sensitivity.py.
Tests sensitivity analysis for counter-factual comparisons.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import json

from modeling.sensitivity import (
    load_dataset_safe,
    calculate_correlation,
    run_sensitivity_analysis
)

class TestLoadDatasetSafe:
    def test_load_dataset_safe_success(self):
        """Should load a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                "sample_id": ["s1", "s2"],
                "PCE": [10.0, 15.0]
            })
            df.to_csv(csv_path, index=False)
            
            result = load_dataset_safe(str(csv_path))
            assert result is not None
            assert len(result) == 2

    def test_load_dataset_safe_missing_file(self):
        """Should raise an error for missing file."""
        with pytest.raises(FileNotFoundError):
            load_dataset_safe("nonexistent.csv")

class TestCalculateCorrelation:
    def test_calculate_correlation_basic(self):
        """Should calculate correlation correctly."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        r, p = calculate_correlation(x, y)
        assert np.isclose(r, 1.0)

class TestRunSensitivityAnalysis:
    def test_run_sensitivity_analysis_returns_dict(self):
        """Should return a dictionary with results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create pre-filter dataset
            pre_filter_path = Path(tmpdir) / "pre_filter.csv"
            df_pre = pd.DataFrame({
                "sample_id": [f"s{i}" for i in range(20)],
                "PCE": np.random.randn(20),
                "metric": np.random.randn(20),
                "validation_flag": [0]*15 + [1]*5,
                "depth_flag": [0]*18 + [1]*2
            })
            df_pre.to_csv(pre_filter_path, index=False)
            
            # Create primary dataset (filtered)
            primary_path = Path(tmpdir) / "primary.csv"
            df_primary = df_pre[df_pre["validation_flag"] == 0]
            df_primary = df_primary[df_primary["depth_flag"] == 0]
            df_primary.to_csv(primary_path, index=False)
            
            result = run_sensitivity_analysis(
                str(pre_filter_path),
                str(primary_path),
                "metric",
                "PCE"
            )
            
            assert isinstance(result, dict)
            assert "r_pre" in result
            assert "r_primary" in result
            assert "delta_r" in result
            assert "sensitivity" in result

    def test_run_sensitivity_analysis_delta_r(self):
        """Delta r should be the absolute difference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pre_filter_path = Path(tmpdir) / "pre_filter.csv"
            primary_path = Path(tmpdir) / "primary.csv"
            
            # Create datasets with known correlation difference
            n_pre = 30
            n_primary = 20
            
            # Pre-filter: strong correlation
            x_pre = np.random.randn(n_pre)
            y_pre = x_pre + np.random.randn(n_pre) * 0.1
            
            # Primary: weaker correlation (due to filtering)
            x_primary = x_pre[:n_primary]
            y_primary = y_pre[:n_primary] + np.random.randn(n_primary) * 0.5
            
            df_pre = pd.DataFrame({
                "sample_id": [f"s{i}" for i in range(n_pre)],
                "PCE": y_pre,
                "metric": x_pre,
                "validation_flag": [0]*n_primary + [1]*(n_pre - n_primary),
                "depth_flag": [0]*n_primary + [1]*(n_pre - n_primary)
            })
            df_pre.to_csv(pre_filter_path, index=False)
            
            df_primary = pd.DataFrame({
                "sample_id": [f"s{i}" for i in range(n_primary)],
                "PCE": y_primary,
                "metric": x_primary,
                "validation_flag": [0]*n_primary,
                "depth_flag": [0]*n_primary
            })
            df_primary.to_csv(primary_path, index=False)
            
            result = run_sensitivity_analysis(
                str(pre_filter_path),
                str(primary_path),
                "metric",
                "PCE"
            )
            
            # Delta r should be non-negative
            assert result["delta_r"] >= 0
            # Sensitivity should be "high" or "low"
            assert result["sensitivity"] in ["high", "low"]

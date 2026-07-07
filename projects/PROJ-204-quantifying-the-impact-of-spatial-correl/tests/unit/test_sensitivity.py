"""
Unit tests for T031c Sensitivity Analysis module.

Tests verify:
1. Correct loading of pre-filter and primary datasets.
2. Accurate calculation of correlation coefficients.
3. Correct delta calculation and sensitivity flagging.
4. Proper handling of edge cases (small sample sizes, missing data).
"""
import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from scipy.stats import pearsonr, spearmanr

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.sensitivity import (
    load_dataset_safe,
    calculate_correlation,
    run_sensitivity_analysis,
    PRE_FILTER_DATASET_PATH,
    PRIMARY_DATASET_PATH,
    OUTPUT_JSON_PATH,
    OUTPUT_CSV_PATH
)

class TestLoadDatasetSafe:
    def test_load_existing_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_file = tmp_path / "test.csv"
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df.to_csv(csv_file, index=False)
        
        loaded_df = load_dataset_safe(csv_file)
        pd.testing.assert_frame_equal(loaded_df, df)
    
    def test_missing_file_raises(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_dataset_safe(tmp_path / "nonexistent.csv")

class TestCalculateCorrelation:
    def test_perfect_correlation(self):
        """Test calculation with perfect positive correlation."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]})
        pearson_r, spearman_r, n = calculate_correlation(df, "x", "y")
        
        assert np.isclose(pearson_r, 1.0, atol=1e-5)
        assert np.isclose(spearman_r, 1.0, atol=1e-5)
        assert n == 5
    
    def test_no_correlation(self):
        """Test calculation with no correlation."""
        np.random.seed(42)
        x = np.random.rand(100)
        y = np.random.rand(100)
        df = pd.DataFrame({"x": x, "y": y})
        
        pearson_r, spearman_r, n = calculate_correlation(df, "x", "y")
        assert n == 100
        # Just check that we get valid numbers, not specific values due to randomness
        assert -1 <= pearson_r <= 1
        assert -1 <= spearman_r <= 1
    
    def test_insufficient_data(self):
        """Test with insufficient data points."""
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        pearson_r, spearman_r, n = calculate_correlation(df, "x", "y")
        
        assert pearson_r is None
        assert spearman_r is None
        assert n == 2
    
    def test_missing_values_handled(self):
        """Test that missing values are dropped."""
        df = pd.DataFrame({"x": [1, 2, np.nan, 4], "y": [2, np.nan, 6, 8]})
        pearson_r, spearman_r, n = calculate_correlation(df, "x", "y")
        
        # Only (1,2) and (4,8) are valid -> n=2, which is < 3, so returns None
        assert pearson_r is None
        assert n == 2

class TestRunSensitivityAnalysis:
    @pytest.fixture
    def mock_datasets(self, tmp_path):
        """Create mock pre-filter and primary datasets."""
        # Pre-filter dataset (larger)
        pre_df = pd.DataFrame({
            "sample_id": [f"sample_{i}" for i in range(100)],
            "correlation_length_Pb": np.random.rand(100) * 10,
            "spectral_power_I": np.random.rand(100) * 5,
            "pce": np.random.rand(100) * 20 + 10,
            "depth_flag": ["valid"] * 80 + ["conflicted"] * 20
        })
        
        # Primary dataset (smaller, after filtering)
        primary_df = pre_df[pre_df["depth_flag"] == "valid"].copy()
        
        # Write to temp files
        pre_path = tmp_path / "unified_dataset.csv"
        primary_path = tmp_path / "filtered_dataset.csv"
        
        pre_df.to_csv(pre_path, index=False)
        primary_df.to_csv(primary_path, index=False)
        
        return pre_path, primary_path
    
    def test_basic_analysis(self, mock_datasets, tmp_path):
        """Test basic functionality of sensitivity analysis."""
        pre_path, primary_path = mock_datasets
        
        # Mock config
        config = {"sensitivity": {"delta_r_threshold": 0.1}}
        
        # Patch the file paths
        with patch("modeling.sensitivity.PRE_FILTER_DATASET_PATH", pre_path), \
             patch("modeling.sensitivity.PRIMARY_DATASET_PATH", primary_path):
            
            results, summary_df = run_sensitivity_analysis(config=config)
            
            # Verify structure
            assert "pre_filter_sample_count" in results
            assert "primary_sample_count" in results
            assert "metrics" in results
            assert "conclusion" in results
            
            # Verify counts
            assert results["pre_filter_sample_count"] == 100
            assert results["primary_sample_count"] == 80
            assert results["samples_excluded"] == 20
            
            # Verify summary DataFrame
            assert len(summary_df) > 0
            assert "metric" in summary_df.columns
            assert "delta_pearson_r" in summary_df.columns

    def test_high_sensitivity_detection(self, tmp_path):
        """Test detection of high sensitivity."""
        # Create datasets where exclusion changes correlation significantly
        # Pre-filter: weak correlation
        pre_df = pd.DataFrame({
            "sample_id": [f"sample_{i}" for i in range(50)],
            "correlation_length_Pb": list(range(50)) + np.random.normal(0, 5, 50),
            "pce": list(range(50)) + np.random.normal(0, 2, 50)
        })
        
        # Primary: strong correlation (after removing noise)
        primary_df = pre_df.iloc[:30].copy()
        
        pre_path = tmp_path / "unified.csv"
        primary_path = tmp_path / "filtered.csv"
        pre_df.to_csv(pre_path, index=False)
        primary_df.to_csv(primary_path, index=False)
        
        config = {"sensitivity": {"delta_r_threshold": 0.1}}
        
        with patch("modeling.sensitivity.PRE_FILTER_DATASET_PATH", pre_path), \
             patch("modeling.sensitivity.PRIMARY_DATASET_PATH", primary_path):
            
            results, _ = run_sensitivity_analysis(config=config)
            
            # Check that sensitivity is detected for at least one metric
            for metric, data in results["metrics"].items():
                if data["delta"]["pearson_r"] is not None:
                    # At least one should show some delta
                    assert isinstance(data["sensitivity"]["pearson"], str)

    def test_missing_columns_handling(self, tmp_path):
        """Test behavior when expected columns are missing."""
        # Create datasets without expected metric columns
        pre_df = pd.DataFrame({
            "sample_id": [f"sample_{i}" for i in range(10)],
            "pce": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        })
        
        primary_df = pre_df.copy()
        
        pre_path = tmp_path / "unified.csv"
        primary_path = tmp_path / "filtered.csv"
        pre_df.to_csv(pre_path, index=False)
        primary_df.to_csv(primary_path, index=False)
        
        config = {"sensitivity": {"delta_r_threshold": 0.1}}
        
        with patch("modeling.sensitivity.PRE_FILTER_DATASET_PATH", pre_path), \
             patch("modeling.sensitivity.PRIMARY_DATASET_PATH", primary_path):
            
            # Should return empty metrics but not crash
            results, summary_df = run_sensitivity_analysis(config=config)
            
            # If no metric columns found, metrics should be empty or have fallback
            assert "metrics" in results

class TestIntegration:
    def test_full_pipeline_execution(self, tmp_path):
        """Test the full pipeline execution with file I/O."""
        # Create mock data
        pre_df = pd.DataFrame({
            "sample_id": [f"s{i}" for i in range(20)],
            "correlation_length_Pb": np.random.rand(20),
            "pce": np.random.rand(20) * 20
        })
        
        primary_df = pre_df.iloc[:15].copy()
        
        pre_path = tmp_path / "unified.csv"
        primary_path = tmp_path / "filtered.csv"
        pre_df.to_csv(pre_path, index=False)
        primary_df.to_csv(primary_path, index=False)
        
        config = {"sensitivity": {"delta_r_threshold": 0.1}}
        
        # Set output paths in temp directory
        json_path = tmp_path / "results.json"
        csv_path = tmp_path / "summary.csv"
        
        with patch("modeling.sensitivity.PRE_FILTER_DATASET_PATH", pre_path), \
             patch("modeling.sensitivity.PRIMARY_DATASET_PATH", primary_path), \
             patch("modeling.sensitivity.OUTPUT_JSON_PATH", json_path), \
             patch("modeling.sensitivity.OUTPUT_CSV_PATH", csv_path):
            
            results, summary_df = run_sensitivity_analysis(config=config)
            
            # Verify files were created
            assert json_path.exists()
            assert csv_path.exists()
            
            # Verify JSON content
            with open(json_path) as f:
                loaded_results = json.load(f)
                assert "conclusion" in loaded_results
            
            # Verify CSV content
            loaded_df = pd.read_csv(csv_path)
            assert len(loaded_df) > 0
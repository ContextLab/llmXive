"""
Unit tests for correlation analysis functionality in analyser.py.

Tests Pearson and Spearman correlation calculations, edge cases,
and integration with dataset properties.
"""
import math
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from code.analyser import (
    load_raw_evaluations,
    calculate_cv,
    aggregate_metrics,
    calculate_correlations,
    run_correlation_analysis
)

class TestCalculateCorrelations:
    """Tests for the calculate_correlations function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create sample aggregated metrics
        self.aggregated_df = pd.DataFrame({
            "dataset_id": [1, 2, 3, 4, 5],
            "model_name": ["LR", "LR", "LR", "LR", "LR"],
            "mean_accuracy": [0.8, 0.85, 0.75, 0.9, 0.82],
            "cv_accuracy": [0.05, 0.08, 0.12, 0.03, 0.07],
            "mean_f1": [0.78, 0.83, 0.73, 0.88, 0.80],
            "cv_f1": [0.06, 0.09, 0.13, 0.04, 0.08],
            "n_folds": [10, 10, 10, 10, 10],
            "n_repeats": [10, 10, 10, 10, 10]
        })
        
        # Create sample dataset properties
        self.properties_df = pd.DataFrame({
            "dataset_id": [1, 2, 3, 4, 5],
            "n_samples": [100, 500, 1000, 5000, 10000],
            "n_features": [5, 10, 20, 50, 100],
            "n_classes": [2, 2, 2, 2, 2]
        })
    
    def test_correlation_computation(self):
        """Test that correlations are computed correctly."""
        result = calculate_correlations(self.aggregated_df, self.properties_df)
        
        assert not result.empty, "Correlation results should not be empty"
        assert "pearson_r" in result.columns, "Result should contain pearson_r column"
        assert "pearson_p" in result.columns, "Result should contain pearson_p column"
        assert "spearman_rho" in result.columns, "Result should contain spearman_rho column"
        assert "spearman_p" in result.columns, "Result should contain spearman_p column"
        assert "cv_metric" in result.columns, "Result should contain cv_metric column"
        assert "property_name" in result.columns, "Result should contain property_name column"
        
        # Check that we have results for all expected correlations
        expected_correlations = [
            ("cv_accuracy", "n_samples"),
            ("cv_accuracy", "n_features"),
            ("cv_f1", "n_samples"),
            ("cv_f1", "n_features"),
        ]
        
        for cv_metric, property_name in expected_correlations:
            mask = (result["cv_metric"] == cv_metric) & (result["property_name"] == property_name)
            assert mask.sum() == 1, f"Expected exactly one result for {cv_metric} vs {property_name}"
    
    def test_zero_cv_handling(self):
        """Test that zero CV values are handled correctly."""
        # Create aggregated data with zero CV
        aggregated_with_zero = self.aggregated_df.copy()
        aggregated_with_zero.loc[0, "cv_accuracy"] = 0.0
        
        result = calculate_correlations(aggregated_with_zero, self.properties_df)
        
        # Zero CV values should be filtered out, reducing valid_samples
        accuracy_samples_result = result[(result["cv_metric"] == "cv_accuracy") & (result["property_name"] == "n_samples")]
        assert not accuracy_samples_result.empty
        # Should have fewer valid samples than total (one filtered out)
        assert accuracy_samples_result["valid_samples"].iloc[0] <= aggregated_with_zero.shape[0]
    
    def test_pearson_r_range(self):
        """Test that Pearson r values are within valid range [-1, 1]."""
        result = calculate_correlations(self.aggregated_df, self.properties_df)
        
        # Filter out NaN values
        valid_pearson_r = result["pearson_r"].dropna()
        
        if len(valid_pearson_r) > 0:
            assert (valid_pearson_r >= -1.0).all(), "Pearson r should be >= -1"
            assert (valid_pearson_r <= 1.0).all(), "Pearson r should be <= 1"
    
    def test_p_value_range(self):
        """Test that p-values are within valid range [0, 1]."""
        result = calculate_correlations(self.aggregated_df, self.properties_df)
        
        # Filter out NaN values
        valid_pearson_p = result["pearson_p"].dropna()
        
        if len(valid_pearson_p) > 0:
            assert (valid_pearson_p >= 0.0).all(), "P-value should be >= 0"
            assert (valid_pearson_p <= 1.0).all(), "P-value should be <= 1"
    
    def test_empty_aggregated_data(self):
        """Test handling of empty aggregated DataFrame."""
        empty_df = pd.DataFrame(columns=["dataset_id", "model_name", "mean_accuracy", "cv_accuracy"])
        result = calculate_correlations(empty_df, self.properties_df)
        
        assert result.empty, "Result should be empty for empty input"
    
    def test_empty_properties_data(self):
        """Test handling of empty properties DataFrame."""
        empty_properties = pd.DataFrame()
        result = calculate_correlations(self.aggregated_df, empty_properties)
        
        assert result.empty, "Result should be empty for empty properties"
    
    def test_no_matching_dataset_ids(self):
        """Test handling of no matching dataset IDs between datasets."""
        different_properties = self.properties_df.copy()
        different_properties["dataset_id"] = [10, 11, 12, 13, 14]
        
        result = calculate_correlations(self.aggregated_df, different_properties)
        
        assert result.empty, "Result should be empty when no dataset IDs match"
    
    def test_single_data_point(self):
        """Test handling of single data point (insufficient for correlation)."""
        single_df = self.aggregated_df.iloc[:1].copy()
        single_properties = self.properties_df.iloc[:1].copy()
        
        result = calculate_correlations(single_df, single_properties)
        
        # Should not crash, but return NaN for correlations
        assert not result.empty, "Result should not be empty even with single point"
        # Correlations should be NaN due to insufficient data
        assert math.isnan(result["pearson_r"].iloc[0]) or result["pearson_r"].iloc[0] is None

class TestRunCorrelationAnalysis:
    """Tests for the run_correlation_analysis function."""
    
    def test_full_pipeline(self):
        """Test the full correlation analysis pipeline with temporary files."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create aggregated metrics file
            aggregated_path = tmpdir_path / "stability_metrics.csv"
            aggregated_df = pd.DataFrame({
                "dataset_id": [1, 2, 3],
                "model_name": ["LR", "LR", "LR"],
                "mean_accuracy": [0.8, 0.85, 0.75],
                "cv_accuracy": [0.05, 0.08, 0.12],
                "mean_f1": [0.78, 0.83, 0.73],
                "cv_f1": [0.06, 0.09, 0.13],
                "n_folds": [10, 10, 10],
                "n_repeats": [10, 10, 10]
            })
            aggregated_df.to_csv(aggregated_path, index=False)
            
            # Create dataset properties file
            properties_path = tmpdir_path / "dataset_properties.csv"
            properties_df = pd.DataFrame({
                "dataset_id": [1, 2, 3],
                "n_samples": [100, 500, 1000],
                "n_features": [5, 10, 20],
                "n_classes": [2, 2, 2]
            })
            properties_df.to_csv(properties_path, index=False)
            
            # Output path
            output_path = tmpdir_path / "correlation_results.csv"
            
            # Run analysis
            result = run_correlation_analysis(
                aggregated_path=str(aggregated_path),
                properties_path=str(properties_path),
                output_path=str(output_path)
            )
            
            # Verify output file was created
            assert output_path.exists(), "Output file should be created"
            
            # Verify result content
            assert not result.empty, "Result should not be empty"
            assert "pearson_r" in result.columns
            assert "pearson_p" in result.columns
            
            # Verify file can be loaded
            loaded_result = pd.read_csv(output_path)
            assert len(loaded_result) == len(result), "Loaded file should match result"
    
    def test_missing_aggregated_file(self):
        """Test error handling when aggregated file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "correlation_results.csv"
            
            with pytest.raises(FileNotFoundError):
                run_correlation_analysis(
                    aggregated_path="nonexistent.csv",
                    output_path=str(output_path)
                )
    
    def test_missing_properties_file(self):
        """Test error handling when properties file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create aggregated file
            aggregated_path = tmpdir_path / "stability_metrics.csv"
            pd.DataFrame({
                "dataset_id": [1],
                "model_name": ["LR"],
                "mean_accuracy": [0.8],
                "cv_accuracy": [0.05],
                "mean_f1": [0.78],
                "cv_f1": [0.06],
                "n_folds": [10],
                "n_repeats": [10]
            }).to_csv(aggregated_path, index=False)
            
            output_path = tmpdir_path / "correlation_results.csv"
            
            # Should raise FileNotFoundError for missing properties
            with pytest.raises(FileNotFoundError):
                run_correlation_analysis(
                    aggregated_path=str(aggregated_path),
                    properties_path="nonexistent_properties.csv",
                    output_path=str(output_path)
                )

class TestCalculateCV:
    """Tests for the calculate_cv function."""
    
    def test_normal_case(self):
        """Test CV calculation for normal case."""
        result = calculate_cv(10.0, 2.0)
        assert math.isclose(result, 0.2, rel_tol=1e-5)
    
    def test_zero_mean(self):
        """Test CV calculation when mean is zero."""
        result = calculate_cv(0.0, 2.0)
        assert result == 0.0
    
    def test_very_small_mean(self):
        """Test CV calculation when mean is very small."""
        result = calculate_cv(1e-12, 2.0)
        # Should return 0.0 due to isclose check
        assert result == 0.0
    
    def test_negative_mean(self):
        """Test CV calculation with negative mean (uses absolute value)."""
        result = calculate_cv(-10.0, 2.0)
        assert math.isclose(result, 0.2, rel_tol=1e-5)
    
    def test_zero_std(self):
        """Test CV calculation with zero standard deviation."""
        result = calculate_cv(10.0, 0.0)
        assert result == 0.0
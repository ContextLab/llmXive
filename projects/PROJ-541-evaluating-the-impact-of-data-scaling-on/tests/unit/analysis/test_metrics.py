"""
Unit tests for metrics module, including sensitivity analysis.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import tempfile

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.metrics import (
    load_simulation_results,
    calculate_aggregate_metrics,
    calculate_confidence_interval,
    run_sensitivity_analysis
)

class TestSensitivityAnalysis:
    """Tests for the sensitivity analysis functionality (T057)."""

    def test_run_sensitivity_analysis_produces_all_alpha_levels(self, tmp_path):
        """
        Test that run_sensitivity_analysis produces results for all specified alpha levels.
        """
        # Create a mock results DataFrame
        np.random.seed(42)
        n_rows = 200
        
        data = {
            'config_id': ['c1'] * n_rows,
            'scaling_method': ['standardize'] * n_rows,
            'test_type': ['t_test'] * n_rows,
            'ground_truth': ['null'] * (n_rows // 2) + ['alternative'] * (n_rows // 2),
            'p_value': np.random.uniform(0, 1, n_rows)
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "sensitivity_analysis.csv"
        
        # Run analysis
        result_df = run_sensitivity_analysis(df, output_path=str(output_path))
        
        # Assertions
        assert not result_df.empty, "Result DataFrame should not be empty"
        assert 'alpha_level' in result_df.columns, "Result must contain alpha_level column"
        
        # Check that all default alpha levels are present
        expected_alphas = [0.01, 0.05, 0.10]
        unique_alphas = result_df['alpha_level'].unique().tolist()
        
        for alpha in expected_alphas:
            assert alpha in unique_alphas, f"Alpha level {alpha} is missing from results"
        
        # Verify file was written
        assert output_path.exists(), "Output CSV file should be created"
        
        # Verify schema
        required_cols = ['alpha_level', 'error_rate', 'power', 'scaling_method']
        for col in required_cols:
            assert col in result_df.columns, f"Missing column: {col}"

    def test_run_sensitivity_analysis_custom_alpha_levels(self, tmp_path):
        """
        Test that run_sensitivity_analysis respects custom alpha levels.
        """
        np.random.seed(42)
        n_rows = 100
        data = {
            'config_id': ['c1'] * n_rows,
            'scaling_method': ['min_max'] * n_rows,
            'test_type': ['anova'] * n_rows,
            'ground_truth': ['alternative'] * n_rows,
            'p_value': np.random.uniform(0, 1, n_rows)
        }
        df = pd.DataFrame(data)
        
        custom_alphas = [0.001, 0.025]
        output_path = tmp_path / "custom_sensitivity.csv"
        
        result_df = run_sensitivity_analysis(df, alpha_levels=custom_alphas, output_path=str(output_path))
        
        assert len(result_df['alpha_level'].unique()) == len(custom_alphas)
        for alpha in custom_alphas:
            assert alpha in result_df['alpha_level'].values

    def test_run_sensitivity_analysis_empty_input(self, tmp_path):
        """
        Test handling of empty input DataFrame.
        """
        df = pd.DataFrame()
        output_path = tmp_path / "empty_sensitivity.csv"
        
        result_df = run_sensitivity_analysis(df, output_path=str(output_path))
        
        assert result_df.empty

class TestEmpiricalErrorRate:
    """Tests for error rate calculation."""

    def test_calculate_aggregate_metrics(self):
        """Test that aggregate metrics are calculated correctly."""
        # Create mock data with known properties
        # 100 nulls, 50 rejections at alpha=0.05 -> error_rate = 0.5
        # 100 alts, 80 rejections -> power = 0.8
        data = {
            'config_id': ['c1'] * 200,
            'scaling_method': ['std'] * 200,
            'test_type': ['t'] * 200,
            'ground_truth': (['null'] * 100) + (['alternative'] * 100),
            'p_value': (np.array([0.01] * 50 + [0.1] * 50)) + (np.array([0.01] * 80 + [0.2] * 20))
        }
        df = pd.DataFrame(data)
        
        result = calculate_aggregate_metrics(df, alpha=0.05)
        
        assert not result.empty
        assert 'error_rate' in result.columns
        assert 'power' in result.columns
        
        # Check values
        row = result.iloc[0]
        assert np.isclose(row['error_rate'], 0.5, atol=0.01)
        assert np.isclose(row['power'], 0.8, atol=0.01)

class TestFullPipeline:
    """Tests for the full analysis pipeline."""

    def test_run_full_analysis_pipeline(self, tmp_path):
        """Test the full pipeline execution."""
        # Mock data
        data = {
            'config_id': ['c1'] * 50,
            'scaling_method': ['std'] * 50,
            'test_type': ['t'] * 50,
            'ground_truth': ['null'] * 25 + ['alternative'] * 25,
            'p_value': np.random.uniform(0, 1, 50)
        }
        df = pd.DataFrame(data)
        
        # Mock load function to return our df
        import analysis.metrics as metrics_mod
        original_load = metrics_mod.load_simulation_results
        
        try:
            metrics_mod.load_simulation_results = lambda: df
            result = metrics_mod.run_full_analysis_pipeline()
            
            assert 'aggregate_metrics' in result
            assert 'mixed_effects_model' in result
        finally:
            metrics_mod.load_simulation_results = original_load

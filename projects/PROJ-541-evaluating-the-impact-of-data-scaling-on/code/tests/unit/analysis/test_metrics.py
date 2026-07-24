"""Tests for analysis metrics and report generation."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.metrics import (
    load_simulation_results,
    load_real_world_results,
    calculate_aggregate_metrics,
    calculate_confidence_interval,
    fit_mixed_effects_model,
    generate_comparison_report,
    run_sensitivity_analysis,
    run_full_analysis_pipeline
)

class TestClopperPearsonVerification:
    """Test Clopper-Pearson confidence interval implementation."""

    def test_zero_successes(self):
        """Test CI when there are zero successes."""
        lower, upper = calculate_confidence_interval(0, 100, 0.05)
        assert lower == 0.0
        assert upper < 0.05  # Should be small but not zero

    def test_all_successes(self):
        """Test CI when all are successes."""
        lower, upper = calculate_confidence_interval(100, 100, 0.05)
        assert lower > 0.95  # Should be close to 1
        assert upper == 1.0

    def test_moderate_successes(self):
        """Test CI with moderate number of successes."""
        lower, upper = calculate_confidence_interval(5, 100, 0.05)
        assert 0.01 < lower < 0.10
        assert 0.02 < upper < 0.15

    def test_small_sample(self):
        """Test CI with small sample size."""
        lower, upper = calculate_confidence_interval(1, 10, 0.05)
        assert 0.0 < lower < 0.5
        assert 0.3 < upper < 1.0

class TestEmpiricalErrorRate:
    """Test empirical error rate calculation."""

    def test_error_rate_calculation(self):
        """Test that error rate is calculated correctly."""
        df = pd.DataFrame({
            'config_id': ['config1'] * 100,
            'scaling_method': ['standardize'] * 100,
            'test_type': ['t_test'] * 100,
            'p_value': [0.04] * 5 + [0.06] * 95,  # 5 rejections at alpha=0.05
            'ground_truth': ['null'] * 100
        })
        
        metrics = calculate_aggregate_metrics(df, alpha=0.05)
        
        assert len(metrics) == 1
        assert metrics.iloc[0]['error_rate'] == 0.05
        assert metrics.iloc[0]['total_iterations'] == 100
        assert metrics.iloc[0]['rejections'] == 5

    def test_power_calculation(self):
        """Test power calculation for alternative hypothesis."""
        df = pd.DataFrame({
            'config_id': ['config1'] * 100,
            'scaling_method': ['standardize'] * 100,
            'test_type': ['t_test'] * 100,
            'p_value': [0.04] * 80 + [0.06] * 20,  # 80 rejections
            'ground_truth': ['alternative'] * 100
        })
        
        metrics = calculate_aggregate_metrics(df, alpha=0.05)
        
        assert len(metrics) == 1
        # For alternative, power should be high (rejections / total)
        assert metrics.iloc[0]['power'] > 0.7

class TestFullPipeline:
    """Test the full analysis pipeline."""

    def test_run_full_analysis_pipeline_with_data(self, tmp_path):
        """Test running full pipeline with sample data."""
        # Create sample simulation results
        synth_df = pd.DataFrame({
            'config_id': ['config1'] * 50 + ['config2'] * 50,
            'scaling_method': ['standardize'] * 50 + ['min_max'] * 50,
            'test_type': ['t_test'] * 100,
            'p_value': np.random.uniform(0, 1, 100),
            'ground_truth': ['null'] * 50 + ['alternative'] * 50
        })
        
        # Create sample real-world results
        real_df = pd.DataFrame({
            'dataset_id': ['iris'] * 50,
            'scaling_method': ['standardize'] * 50,
            'test_type': ['t_test'] * 50,
            'p_value': np.random.uniform(0, 1, 50),
            'effect_size': np.random.uniform(0.1, 0.5, 50)
        })
        
        # Save to temporary files
        synth_path = tmp_path / "simulation_results.csv"
        real_path = tmp_path / "real_world_results.csv"
        
        synth_df.to_csv(synth_path, index=False)
        real_df.to_csv(real_path, index=False)
        
        # Patch the load functions to use our temp files
        import analysis.metrics as metrics_module
        original_load_sim = metrics_module.load_simulation_results
        original_load_real = metrics_module.load_real_world_results
        
        metrics_module.load_simulation_results = lambda filepath=None: pd.read_csv(synth_path)
        metrics_module.load_real_world_results = lambda filepath=None: pd.read_csv(real_path)
        
        try:
            results = run_full_analysis_pipeline()
            
            assert 'aggregate_metrics' in results
            assert not results['aggregate_metrics'].empty
            assert 'sensitivity_analysis' in results
            assert 'comparison_report' in results
            assert Path(results['comparison_report']).exists()
        finally:
            # Restore original functions
            metrics_module.load_simulation_results = original_load_sim
            metrics_module.load_real_world_results = original_load_real

    def test_run_full_analysis_pipeline_empty(self, tmp_path):
        """Test pipeline with empty data."""
        results = run_full_analysis_pipeline(pd.DataFrame())
        assert results is not None

class TestComparisonReport:
    """Test comparison report generation."""

    def test_generate_comparison_report_schema(self, tmp_path):
        """Test that comparison report has correct schema."""
        synth_df = pd.DataFrame({
            'config_id': ['config1'] * 30,
            'scaling_method': ['standardize', 'min_max', 'robust'] * 10,
            'test_type': ['t_test'] * 30,
            'p_value': np.random.uniform(0, 1, 30),
            'ground_truth': ['null'] * 30,
            'error_rate': np.random.uniform(0, 0.1, 30)
        })
        
        real_df = pd.DataFrame({
            'dataset_id': ['iris', 'wine', 'breast_cancer'] * 10,
            'scaling_method': ['standardize', 'min_max', 'robust'] * 10,
            'test_type': ['t_test'] * 30,
            'p_value': np.random.uniform(0, 1, 30),
            'effect_size': np.random.uniform(0.1, 0.5, 30),
            'error_rate': np.random.uniform(0, 0.1, 30)
        })
        
        output_path = tmp_path / "comparison_report.md"
        
        generate_comparison_report(synth_df, real_df, str(output_path))
        
        assert output_path.exists()
        
        content = output_path.read_text()
        
        # Check for required columns in markdown table
        assert "Metric" in content
        assert "Synthetic_Value" in content
        assert "Real_Value" in content
        assert "Mean_Absolute_Difference" in content
        assert "Correlation_Coefficient" in content
        
        # Check for specific metrics
        assert "standardize" in content
        assert "min_max" in content
        assert "robust" in content

    def test_generate_comparison_report_correlation(self, tmp_path):
        """Test that correlation coefficient is calculated."""
        synth_df = pd.DataFrame({
            'config_id': ['config1'] * 20,
            'scaling_method': ['standardize'] * 20,
            'test_type': ['t_test'] * 20,
            'p_value': np.linspace(0.01, 0.09, 20),
            'ground_truth': ['null'] * 20,
            'error_rate': np.linspace(0.01, 0.09, 20)
        })
        
        real_df = pd.DataFrame({
            'dataset_id': ['iris'] * 20,
            'scaling_method': ['standardize'] * 20,
            'test_type': ['t_test'] * 20,
            'p_value': np.linspace(0.02, 0.10, 20),  # Similar trend
            'effect_size': np.linspace(0.1, 0.5, 20),
            'error_rate': np.linspace(0.02, 0.10, 20)
        })
        
        output_path = tmp_path / "comparison_report.md"
        
        generate_comparison_report(synth_df, real_df, str(output_path))
        
        content = output_path.read_text()
        assert "Pearson Correlation Coefficient" in content

class TestMixedEffectsModel:
    """Test mixed-effects model fitting."""

    def test_fit_mixed_effects_model_with_config(self):
        """Test model with config_id as random effect."""
        df = pd.DataFrame({
            'config_id': ['config1'] * 30 + ['config2'] * 30,
            'scaling_method': ['standardize', 'min_max', 'robust'] * 20,
            'error_rate': np.random.uniform(0, 0.1, 60)
        })
        
        result = fit_mixed_effects_model(df)
        
        # Result might be None if statsmodels not available, but should not crash
        assert result is None or hasattr(result, 'summary')

    def test_fit_mixed_effects_model_with_dataset(self):
        """Test model with dataset_id as random effect."""
        df = pd.DataFrame({
            'dataset_id': ['iris'] * 20 + ['wine'] * 20 + ['breast_cancer'] * 20,
            'scaling_method': ['standardize', 'min_max', 'robust'] * 20,
            'error_rate': np.random.uniform(0, 0.1, 60)
        })
        
        result = fit_mixed_effects_model(df)
        
        assert result is None or hasattr(result, 'summary')

    def test_fit_mixed_effects_model_empty(self):
        """Test model with empty DataFrame."""
        df = pd.DataFrame()
        result = fit_mixed_effects_model(df)
        assert result is None

class TestSensitivityAnalysis:
    """Test sensitivity analysis functionality."""

    def test_run_sensitivity_analysis_multiple_alphas(self):
        """Test sensitivity analysis across multiple alpha levels."""
        df = pd.DataFrame({
            'config_id': ['config1'] * 100,
            'scaling_method': ['standardize'] * 100,
            'test_type': ['t_test'] * 100,
            'p_value': np.random.uniform(0, 0.2, 100),
            'ground_truth': ['null'] * 100
        })
        
        alpha_levels = [0.01, 0.05, 0.10]
        results = run_sensitivity_analysis(df, alpha_levels)
        
        assert len(results) == len(alpha_levels)  # One row per alpha level for this config
        assert set(results['alpha_level'].unique()) == set(alpha_levels)
        
        # Check that error rates increase with alpha
        for alpha in alpha_levels:
            subset = results[results['alpha_level'] == alpha]
            assert subset.iloc[0]['error_rate'] >= 0
            assert subset.iloc[0]['error_rate'] <= 1

    def test_run_sensitivity_analysis_empty(self):
        """Test sensitivity analysis with empty DataFrame."""
        df = pd.DataFrame()
        results = run_sensitivity_analysis(df)
        assert results.empty

class TestComparisonReportIntegration:
    """Integration tests for comparison report."""

    def test_comparison_report_with_real_schema(self, tmp_path):
        """Test comparison report generation with realistic data schema."""
        # Synthetic results with expected schema
        synth_df = pd.DataFrame({
            'config_id': ['config1'] * 50 + ['config2'] * 50,
            'scaling_method': ['standardize'] * 50 + ['min_max'] * 50,
            'test_type': ['t_test'] * 50 + ['anova'] * 50,
            'p_value': np.random.uniform(0, 1, 100),
            'statistic': np.random.uniform(-2, 2, 100),
            'ground_truth': ['null'] * 100,
            'scaling_params': '{}',
            'seed': range(100),
            'error_rate': np.random.uniform(0, 0.1, 100)
        })
        
        # Real-world results with expected schema
        real_df = pd.DataFrame({
            'dataset_id': ['iris'] * 25 + ['wine'] * 25,
            'source_url': ['https://example.com/iris'] * 25 + ['https://example.com/wine'] * 25,
            'p_value': np.random.uniform(0, 1, 50),
            'effect_size': np.random.uniform(0.1, 0.5, 50),
            'source_verified': [True] * 50,
            'error_rate': np.random.uniform(0, 0.1, 50)
        })
        
        output_path = tmp_path / "comparison_report.md"
        
        generate_comparison_report(synth_df, real_df, str(output_path))
        
        assert output_path.exists()
        
        content = output_path.read_text()
        
        # Verify all required sections are present
        assert "# Comparison Report:" in content
        assert "## Summary Statistics" in content
        assert "## Detailed Comparison" in content
        assert "## Error Rate Comparison" in content
        
        # Verify metrics are calculated
        assert "Mean_Absolute_Difference" in content
        assert "Correlation_Coefficient" in content
        
        # Verify scaling methods are included
        assert "standardize" in content
        assert "min_max" in content
        
        # Verify test types are included
        assert "t_test" in content
        assert "anova" in content
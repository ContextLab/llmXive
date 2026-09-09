"""
Unit tests for regression analysis module.

Tests statistical significance, model selection, and validation logic.
"""
import pytest
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.regression import (
    validate_trial_counts,
    load_ftle_sweep_results,
    load_baseline_results,
    compute_deviations,
    run_ttest_bias,
    select_best_model,
    calculate_scaling_exponent,
    RegressionResult,
    TrialValidationReport
)

class TestTrialValidation:
    """Tests for trial count validation."""
    
    def test_valid_trial_counts(self, tmp_path):
        """Test validation when all required trials exist."""
        # Create mock data files
        for N in [1, 5]:
            for sigma in [0.005, 0.05, 0.5]:
                required_k = 50 if sigma < 0.01 else 30
                for t in range(required_k):
                    filename = f"trajectory_N{N}_sigma{sigma:.4f}_trial{t}.csv"
                    (tmp_path / filename).touch()
        
        report = validate_trial_counts(
            data_dir=tmp_path,
            noise_levels=[0.005, 0.05, 0.5],
            N_values=[1, 5]
        )
        
        assert report.valid is True
        assert len(report.missing_trials) == 0
        assert report.total_found == report.total_expected
    
    def test_missing_trials(self, tmp_path):
        """Test validation when some trials are missing."""
        # Create fewer files than required
        for N in [1]:
            for sigma in [0.005]:  # Requires 50
                for t in range(30):  # Only create 30
                    filename = f"trajectory_N{N}_sigma{sigma:.4f}_trial{t}.csv"
                    (tmp_path / filename).touch()
        
        report = validate_trial_counts(
            data_dir=tmp_path,
            noise_levels=[0.005],
            N_values=[1]
        )
        
        assert report.valid is False
        assert 'N1_sigma0.0050' in report.missing_trials
        assert report.missing_trials['N1_sigma0.0050'] == 20

class TestFTLELoading:
    """Tests for FTLE data loading."""
    
    def test_load_valid_ftle_sweep(self, tmp_path):
        """Test loading valid FTLE sweep results."""
        # Create mock FTLE data
        mock_data = [
            {'trial_id': 1, 'N': 1, 'sigma': 0.01, 'T': 500, 'lambda_ftle': 0.85},
            {'trial_id': 2, 'N': 1, 'sigma': 0.01, 'T': 500, 'lambda_ftle': 0.87},
            {'trial_id': 3, 'N': 1, 'sigma': 0.01, 'T': 1000, 'lambda_ftle': 0.86}
        ]
        
        ftle_file = tmp_path / 'ftle_sweep.json'
        with open(ftle_file, 'w') as f:
            json.dump(mock_data, f)
        
        df = load_ftle_sweep_results(ftle_file)
        
        assert len(df) == 3
        assert 'trial_id' in df.columns
        assert 'lambda_ftle' in df.columns
        assert df['lambda_ftle'].mean() == pytest.approx(0.86, abs=0.01)
    
    def test_load_missing_file(self, tmp_path):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_ftle_sweep_results(tmp_path / 'nonexistent.json')
    
    def test_load_missing_columns(self, tmp_path):
        """Test loading data with missing required columns."""
        mock_data = [
            {'trial_id': 1, 'N': 1}  # Missing sigma, T, lambda_ftle
        ]
        
        ftle_file = tmp_path / 'ftle_sweep.json'
        with open(ftle_file, 'w') as f:
            json.dump(mock_data, f)
        
        with pytest.raises(ValueError):
            load_ftle_sweep_results(ftle_file)

class TestBaselineLoading:
    """Tests for baseline data loading."""
    
    def test_load_valid_baselines(self, tmp_path):
        """Test loading valid baseline results."""
        # Create mock baseline files
        for N in [1, 5]:
            baseline_data = {
                'lambda_max': 0.9 + N * 0.1,
                'error_estimate': 1e-6,
                'convergence_check': True
            }
            baseline_file = tmp_path / f'baseline_{N}.json'
            with open(baseline_file, 'w') as f:
                json.dump(baseline_data, f)
        
        baselines = load_baseline_results(tmp_path, [1, 5])
        
        assert len(baselines) == 2
        assert baselines[1] == pytest.approx(0.9, abs=0.01)
        assert baselines[5] == pytest.approx(1.4, abs=0.01)
    
    def test_load_missing_baseline(self, tmp_path):
        """Test loading when baseline file is missing."""
        with pytest.raises(FileNotFoundError):
            load_baseline_results(tmp_path, [1])

class TestDeviationComputation:
    """Tests for deviation calculation."""
    
    def test_compute_deviations(self):
        """Test deviation computation from baseline."""
        # Create mock data
        df = pd.DataFrame({
            'N': [1, 1, 5, 5],
            'sigma': [0.01, 0.01, 0.01, 0.01],
            'T': [500, 1000, 500, 1000],
            'lambda_ftle': [0.85, 0.87, 1.35, 1.38],
            'trial_id': [1, 2, 3, 4]
        })
        
        baselines = {1: 0.9, 5: 1.4}
        
        df_with_dev = compute_deviations(df, baselines)
        
        assert 'deviation' in df_with_dev.columns
        assert df_with_dev.loc[0, 'deviation'] == pytest.approx(-0.05, abs=0.01)
        assert df_with_dev.loc[1, 'deviation'] == pytest.approx(-0.03, abs=0.01)
        assert df_with_dev.loc[2, 'deviation'] == pytest.approx(-0.05, abs=0.01)
        assert df_with_dev.loc[3, 'deviation'] == pytest.approx(-0.02, abs=0.01)

class TestStatisticalTests:
    """Tests for statistical significance testing."""
    
    def test_ttest_bias_significance(self):
        """Test t-test on bias term with known significant difference."""
        # Create data with known bias
        np.random.seed(42)
        deviations = np.random.normal(loc=0.5, scale=0.1, size=100)
        baseline = 0.0
        
        p_value, effect_size = run_ttest_bias(deviations, baseline)
        
        # Should be highly significant
        assert p_value < 0.05
        assert effect_size > 0.5  # Large effect size
    
    def test_ttest_bias_non_significant(self):
        """Test t-test when no significant difference exists."""
        # Create data centered at baseline
        np.random.seed(42)
        deviations = np.random.normal(loc=0.0, scale=0.1, size=100)
        baseline = 0.0
        
        p_value, effect_size = run_ttest_bias(deviations, baseline)
        
        # Should not be significant (or barely)
        assert effect_size < 0.5  # Small effect size
    
    def test_ttest_insufficient_samples(self):
        """Test t-test with insufficient samples."""
        with pytest.raises(ValueError):
            run_ttest_bias(np.array([0.5]), 0.0)

class TestModelSelection:
    """Tests for regression model selection."""
    
    def test_select_best_model(self):
        """Test model selection with known data."""
        # Create synthetic data with linear relationship
        np.random.seed(42)
        n = 100
        sigma = np.random.uniform(0.01, 1.0, n)
        deviation = 0.5 * sigma + np.random.normal(0, 0.1, n)
        
        df = pd.DataFrame({
            'sigma': sigma,
            'deviation': deviation,
            'N': np.random.choice([1, 5], n),
            'T': np.random.choice([500, 1000, 5000], n),
            'lambda_ftle': np.random.normal(1.0, 0.1, n),
            'trial_id': range(n)
        })
        
        model_name, results = select_best_model(df)
        
        assert model_name in ['linear', 'log_linear', 'quadratic', 'power_law']
        assert results.rsquared > 0.5  # Reasonable fit
        assert results.aic > 0

class TestScalingExponent:
    """Tests for scaling exponent calculation."""
    
    def test_calculate_scaling_exponent(self):
        """Test scaling exponent calculation."""
        # Create data with known scaling
        np.random.seed(42)
        N_values = [1, 2, 4, 8, 16]
        deviations = [0.1 * N**0.5 for N in N_values]  # sqrt scaling
        
        df = pd.DataFrame({
            'N': N_values,
            'deviation': deviations,
            'sigma': 0.1,
            'T': 1000,
            'lambda_ftle': 1.0,
            'trial_id': range(len(N_values))
        })
        
        exp = calculate_scaling_exponent(df, N_values)
        
        # Should be close to 0.5 (sqrt scaling)
        assert exp is not None
        assert abs(exp - 0.5) < 0.2  # Within 20% tolerance

class TestIntegration:
    """Integration tests for full regression pipeline."""
    
    def test_full_scaling_analysis(self, tmp_path):
        """Test full scaling analysis pipeline."""
        # Create mock FTLE data
        mock_ftle = []
        for N in [1, 5]:
            for sigma in [0.01, 0.1, 0.5]:
                baseline = 0.9 + N * 0.1
                for t in range(30):
                    mock_ftle.append({
                        'trial_id': len(mock_ftle) + 1,
                        'N': N,
                        'sigma': sigma,
                        'T': 500,
                        'lambda_ftle': baseline + 0.1 * sigma + np.random.normal(0, 0.02)
                    })
        
        ftle_file = tmp_path / 'ftle_sweep.json'
        with open(ftle_file, 'w') as f:
            json.dump(mock_ftle, f)
        
        # Create baseline files
        for N in [1, 5]:
            baseline_data = {
                'lambda_max': 0.9 + N * 0.1,
                'error_estimate': 1e-6,
                'convergence_check': True
            }
            baseline_file = tmp_path / f'baseline_{N}.json'
            with open(baseline_file, 'w') as f:
                json.dump(baseline_data, f)
        
        # Run analysis
        results_path = tmp_path / 'results.json'
        plot_path = tmp_path / 'plot_deviation_vs_noise.png'
        
        from analysis.regression import run_full_regression_analysis
        results = run_full_regression_analysis(
            ftle_file=ftle_file,
            baseline_dir=tmp_path,
            output_dir=tmp_path,
            N_values=[1, 5]
        )
        
        # Verify results
        assert 'p_value_raw' in results['statistical_tests']
        assert 'effect_size_raw' in results['statistical_tests']
        assert 'p_value_model' in results['statistical_tests']
        assert 'effect_size_model' in results['statistical_tests']
        assert results['statistical_tests']['p_value_raw'] < 0.05  # Should be significant
        
        # Verify plot was created
        assert plot_path.exists()
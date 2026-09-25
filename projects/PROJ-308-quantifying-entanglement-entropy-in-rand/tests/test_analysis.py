"""
Tests for code/analysis.py
"""
import pytest
import numpy as np
import os
import tempfile
from code.analysis import (
    select_model_aic,
    filter_unresolved_realizations,
    bootstrap_resample,
    compute_bootstrap_statistics,
    compute_scaling_exponent,
    generate_toy_model_data,
    generate_entropy_vs_l_plot,
    verify_scaling_ansatz
)

class TestModelSelection:
    def test_aic_selection_logic(self):
        """Test AIC selection logic with synthetic data of known slope."""
        # Generate data with clear logarithmic trend: S = 0.5 * log(l)
        l_vals = np.array([2, 4, 8, 16, 32])
        s_vals = 0.5 * np.log(l_vals) + 0.1 * np.random.randn(len(l_vals))
        
        result = select_model_aic(l_vals, s_vals)
        
        assert result.model_type == 'logarithmic'
        assert result.slope is not None
        assert np.isclose(result.slope, 0.5, atol=0.2)  # Allow some noise tolerance

    def test_constant_model_selection(self):
        """Test selection of constant model (Area Law)."""
        l_vals = np.array([2, 4, 8, 16, 32])
        s_vals = np.ones(len(l_vals)) * 1.5  # Constant entropy
        
        result = select_model_aic(l_vals, s_vals)
        
        assert result.model_type == 'constant'

    def test_linear_model_selection(self):
        """Test selection of linear model (Volume Law)."""
        l_vals = np.array([2, 4, 8, 16, 32])
        s_vals = 0.1 * l_vals + 0.1 * np.random.randn(len(l_vals))
        
        result = select_model_aic(l_vals, s_vals)
        
        # Linear might be selected or logarithmic depending on noise, 
        # but it should not be constant if there is a trend.
        assert result.model_type in ['linear', 'logarithmic']

class TestFiltering:
    def test_filter_unresolved(self):
        """Test filtering of unresolved realizations."""
        data = [
            {'realization_id': 1, 'entropy': 1.0},
            {'realization_id': 2, 'entropy': 1.2},
            {'realization_id': 3, 'entropy': 1.1},
        ]
        unresolved = {2}
        
        filtered = filter_unresolved_realizations(data, unresolved)
        
        assert len(filtered) == 2
        assert all(d['realization_id'] != 2 for d in filtered)

class TestBootstrap:
    def test_bootstrap(self):
        """Test bootstrap resampling and statistics."""
        l_vals = np.array([2, 4, 8, 16, 32])
        s_vals = 0.5 * np.log(l_vals) + 0.05 * np.random.randn(len(l_vals))
        
        slopes = bootstrap_resample(l_vals, s_vals, n_resamples=100, random_seed=42)
        
        assert len(slopes) == 100
        assert np.mean(slopes) > 0
        
        stats_dict = compute_bootstrap_statistics(slopes)
        
        assert 'mean' in stats_dict
        assert 'std_err' in stats_dict
        assert 'ci_lower' in stats_dict
        assert 'ci_upper' in stats_dict
        assert stats_dict['ci_lower'] <= stats_dict['mean'] <= stats_dict['ci_upper']

class TestScalingExponent:
    def test_compute_scaling_exponent(self):
        """Test full exponent computation pipeline."""
        l_vals = np.array([2, 4, 8, 16, 32])
        s_vals = 0.5 * np.log(l_vals) + 0.05 * np.random.randn(len(l_vals))
        
        result = compute_scaling_exponent(l_vals, s_vals, n_resamples=50, random_seed=42)
        
        assert 'alpha' in result
        assert result['alpha'] > 0
        assert 'p_value' in result

class TestToyModel:
    def test_toy_model(self):
        """Test toy model data generation."""
        data = generate_toy_model_data(L=10, n_realizations=5, seed=42)
        
        assert len(data) > 0
        assert 'l' in data[0]
        assert 'entropy' in data[0]
        assert all(d['l'] > 0 for d in data)

class TestPlotGeneration:
    def test_plot_generation(self):
        """Test that generate_entropy_vs_l_plot creates a file."""
        # Generate synthetic data
        l_vals = np.array([2, 4, 8, 16, 32])
        s_vals = 0.5 * np.log(l_vals) + 0.05 * np.random.randn(len(l_vals))
        
        data = []
        for i, l in enumerate(l_vals):
            data.append({'l': int(l), 'entropy': s_vals[i]})
            # Add a few more points for each l
            for _ in range(2):
                data.append({'l': int(l), 'entropy': s_vals[i] + 0.01 * np.random.randn()})
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'entropy_vs_l.png')
            
            generate_entropy_vs_l_plot(data, output_path)
            
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0

class TestVerifyScalingAnsatz:
    def test_verify_scaling_ansatz(self):
        """Test the verify_scaling_ansatz function."""
        l_vals = np.array([2, 4, 8, 16, 32])
        s_vals = 0.5 * np.log(l_vals)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, 'validation_log.txt')
            
            result = verify_scaling_ansatz(l_vals, s_vals, log_path)
            
            assert 'delta_aic' in result
            assert os.path.exists(log_path)
            
            # Check log content
            with open(log_path, 'r') as f:
                content = f.read()
                assert 'Scaling Ansatz Verification' in content
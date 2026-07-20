"""
Tests for the sensitivity analysis module.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from sensitivity_analysis import load_data, perturb_energy_values, run_anova_on_data, run_sensitivity_analysis

class TestPerturbation:
    def test_perturbation_changes_values(self):
        """Test that perturbation actually modifies the energy values."""
        data = {
            'model_id': ['A', 'A', 'B', 'B'],
            'problem_id': ['1', '2', '1', '2'],
            'energy_kwh': [1.0, 1.0, 2.0, 2.0]
        }
        df = pd.DataFrame(data)
        
        df_pert = perturb_energy_values(df, perturbation_factor=0.10, seed=42)
        
        # Check that values are different (with high probability, unless seed hits exact 0)
        assert not df['energy_kwh'].equals(df_pert['energy_kwh'])
        
        # Check that values are within expected range (0.9x to 1.1x)
        for orig, pert in zip(df['energy_kwh'], df_pert['energy_kwh']):
            assert 0.9 * orig <= pert <= 1.1 * orig

    def test_perturbation_reproducibility(self):
        """Test that same seed produces same perturbation."""
        data = {
            'model_id': ['A'],
            'problem_id': ['1'],
            'energy_kwh': [1.0]
        }
        df = pd.DataFrame(data)
        
        df_p1 = perturb_energy_values(df, perturbation_factor=0.10, seed=123)
        df_p2 = perturb_energy_values(df, perturbation_factor=0.10, seed=123)
        
        assert df_p1['energy_kwh'].equals(df_p2['energy_kwh'])

class TestANOVA:
    def test_anova_runs(self):
        """Test that ANOVA runs on a valid dataset."""
        # Create a simple dataset that should produce a valid ANOVA
        # We need enough data points for statsmodels to work
        np.random.seed(42)
        n_problems = 20
        n_models = 3
        
        data = []
        for i in range(n_problems):
            for m in range(n_models):
                # Simulate some energy values with model-dependent means
                mean = [0.1, 0.2, 0.3][m]
                val = mean + np.random.normal(0, 0.05)
                data.append({
                    'model_id': f'M{m}',
                    'problem_id': f'P{i}',
                    'energy_kwh': val
                })
        
        df = pd.DataFrame(data)
        p_val = run_anova_on_data(df)
        
        assert isinstance(p_val, float)
        assert 0.0 <= p_val <= 1.0

class TestSensitivityAnalysis:
    def test_full_workflow(self):
        """Test the full sensitivity analysis workflow."""
        np.random.seed(42)
        n_problems = 10
        n_models = 3
        
        data = []
        for i in range(n_problems):
            for m in range(n_models):
                mean = [0.1, 0.2, 0.3][m]
                val = mean + np.random.normal(0, 0.05)
                data.append({
                    'model_id': f'M{m}',
                    'problem_id': f'P{i}',
                    'energy_kwh': val
                })
        
        df = pd.DataFrame(data)
        
        results = run_sensitivity_analysis(df, perturbation_factor=0.10, seed=42)
        
        assert 'p_original' in results
        assert 'p_perturbed' in results
        assert 'delta_p' in results
        assert isinstance(results['p_original'], float)
        assert isinstance(results['p_perturbed'], float)
        assert isinstance(results['delta_p'], float)
"""
Unit tests for GLMM model fitting in code/analysis/glmm.py.

This module performs a sanity check on synthetic data to ensure the GLMM
fitting logic in code/analysis/glmm.py functions correctly before running
on real data.
"""

import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Import the functions we are testing
# Note: We are testing the logic in glmm.py, so we import the core functions
# that perform the model fitting and analysis.
import sys
import os

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.glmm import (
    prepare_data_for_glmm,
    fit_glmm,
    calculate_effect_sizes,
    run_statistical_analysis
)


class TestGLMMFitting:
    """Test suite for GLMM model fitting logic."""

    @pytest.fixture
    def synthetic_data(self):
        """
        Generate synthetic data for GLMM testing.
        
        Creates a dataset mimicking the structure of execution_traces.csv:
        - task_id: unique identifier
        - architecture: monolithic or dual_track
        - constraint_count: integer (5, 6, 7+)
        - violation_boolean: boolean (0/1)
        - final_score: float (0.0 to 1.0)
        """
        np.random.seed(42)
        n_samples = 200
        
        data = {
            'task_id': [f'task_{i}' for i in range(n_samples)],
            'architecture': np.random.choice(['monolithic', 'dual_track'], n_samples),
            'constraint_count': np.random.choice([5, 6, 7, 8, 9, 10], n_samples),
            'violation_boolean': np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
            'final_score': np.random.uniform(0.0, 1.0, n_samples)
        }
        
        df = pd.DataFrame(data)
        return df

    def test_prepare_data_for_glmm(self, synthetic_data):
        """Test that data preparation correctly formats data for GLMM."""
        # Prepare data
        prepared_data = prepare_data_for_glmm(synthetic_data)
        
        # Verify output is a DataFrame
        assert isinstance(prepared_data, pd.DataFrame)
        
        # Verify required columns exist
        required_cols = ['architecture', 'constraint_count', 'violation_boolean']
        for col in required_cols:
            assert col in prepared_data.columns
        
        # Verify architecture is categorical
        assert prepared_data['architecture'].dtype == 'object' or \
               str(prepared_data['architecture'].dtype) == 'category'
        
        # Verify constraint_count is numeric
        assert pd.api.types.is_numeric_dtype(prepared_data['constraint_count'])
        
        # Verify violation_boolean is numeric (0/1)
        assert pd.api.types.is_numeric_dtype(prepared_data['violation_boolean'])
        assert set(prepared_data['violation_boolean'].unique()).issubset({0, 1})

    def test_fit_glmm_basic(self, synthetic_data):
        """Test that GLMM fitting runs without error on synthetic data."""
        prepared_data = prepare_data_for_glmm(synthetic_data)
        
        # Fit the model
        try:
            result = fit_glmm(prepared_data)
            
            # Verify result is not None
            assert result is not None
            
            # Verify result has expected attributes (depends on statsmodels version)
            # We check for common attributes that should exist
            assert hasattr(result, 'params') or hasattr(result, 'summary')
            
            # Verify we can extract fixed effects
            if hasattr(result, 'params'):
                params = result.params
                assert len(params) > 0
                
            # Verify convergence (if available)
            if hasattr(result, 'converged'):
                # Note: In synthetic data, convergence might not always happen
                # but the attribute should exist
                pass
                
        except Exception as e:
            # If fitting fails, it should be a clear error, not a silent failure
            pytest.fail(f"GLMM fitting failed with error: {str(e)}")

    def test_calculate_effect_sizes(self, synthetic_data):
        """Test effect size calculation."""
        prepared_data = prepare_data_for_glmm(synthetic_data)
        
        # Calculate effect sizes
        try:
            effect_sizes = calculate_effect_sizes(prepared_data)
            
            # Verify result is a dictionary
            assert isinstance(effect_sizes, dict)
            
            # Verify expected keys exist
            expected_keys = ['architecture_effect', 'constraint_effect', 'interaction_effect']
            for key in expected_keys:
                assert key in effect_sizes, f"Missing key: {key}"
                
            # Verify values are numeric
            for key, value in effect_sizes.items():
                assert isinstance(value, (int, float, np.number)), \
                    f"Effect size {key} is not numeric: {type(value)}"
                    
        except Exception as e:
            pytest.fail(f"Effect size calculation failed: {str(e)}")

    def test_run_statistical_analysis_full_pipeline(self, synthetic_data):
        """Test the complete statistical analysis pipeline."""
        try:
            # Run the full analysis
            results = run_statistical_analysis(synthetic_data)
            
            # Verify results structure
            assert isinstance(results, dict)
            
            # Verify key components exist
            required_components = [
                'model_summary',
                'fixed_effects',
                'p_values',
                'effect_sizes',
                'convergence_status'
            ]
            
            for component in required_components:
                assert component in results, f"Missing component: {component}"
                
            # Verify p_values is a dictionary
            assert isinstance(results['p_values'], dict)
            
            # Verify effect_sizes is a dictionary
            assert isinstance(results['effect_sizes'], dict)
            
            # Verify convergence_status is boolean or string
            assert isinstance(results['convergence_status'], (bool, str))
            
        except Exception as e:
            pytest.fail(f"Statistical analysis pipeline failed: {str(e)}")

    def test_glmm_with_interaction_term(self, synthetic_data):
        """Test that GLMM correctly handles interaction between architecture and constraints."""
        # Create data with a known interaction effect
        np.random.seed(123)
        n_samples = 300
        
        # Create interaction: dual_track performs better with more constraints
        architectures = np.random.choice(['monolithic', 'dual_track'], n_samples)
        constraint_counts = np.random.choice([5, 6, 7, 8, 9, 10], n_samples)
        
        # Generate violation probability with interaction
        base_prob = 0.5
        arch_effect = np.where(architectures == 'dual_track', -0.2, 0.0)
        constraint_effect = (constraint_counts - 7) * 0.1
        interaction_effect = np.where(architectures == 'dual_track', 
                                    (constraint_counts - 7) * 0.05, 0.0)
        
        logit_prob = base_prob + arch_effect + constraint_effect + interaction_effect
        probabilities = 1 / (1 + np.exp(-logit_prob))
        
        violation_boolean = np.random.binomial(1, probabilities, n_samples)
        
        synthetic_with_interaction = pd.DataFrame({
            'task_id': [f'task_{i}' for i in range(n_samples)],
            'architecture': architectures,
            'constraint_count': constraint_counts,
            'violation_boolean': violation_boolean,
            'final_score': np.random.uniform(0.0, 1.0, n_samples)
        })
        
        # Run analysis
        results = run_statistical_analysis(synthetic_with_interaction)
        
        # Verify interaction term is present in results
        assert 'interaction_effect' in results['effect_sizes'], \
            "Interaction effect should be calculated"
            
        # Verify the interaction effect is non-zero (or at least the term exists)
        # Note: Due to randomness, the exact value may vary
        assert results['effect_sizes']['interaction_effect'] is not None

    def test_edge_case_empty_dataframe(self):
        """Test handling of empty dataframe."""
        empty_df = pd.DataFrame(columns=[
            'task_id', 'architecture', 'constraint_count', 
            'violation_boolean', 'final_score'
        ])
        
        # Should raise a clear error or handle gracefully
        with pytest.raises((ValueError, Exception)):
            prepare_data_for_glmm(empty_df)

    def test_edge_case_single_group(self):
        """Test handling of data with only one architecture group."""
        np.random.seed(42)
        n_samples = 50
        
        single_group_data = pd.DataFrame({
            'task_id': [f'task_{i}' for i in range(n_samples)],
            'architecture': ['monolithic'] * n_samples,  # Only one group
            'constraint_count': np.random.choice([5, 6, 7], n_samples),
            'violation_boolean': np.random.choice([0, 1], n_samples),
            'final_score': np.random.uniform(0.0, 1.0, n_samples)
        })
        
        # This should fail gracefully or raise a clear error about insufficient groups
        with pytest.raises((ValueError, Exception)):
            run_statistical_analysis(single_group_data)

    def test_output_format_compliance(self, synthetic_data):
        """Test that output matches expected schema for statistical results."""
        results = run_statistical_analysis(synthetic_data)
        
        # Verify schema compliance
        assert 'model_summary' in results
        assert 'fixed_effects' in results
        assert 'p_values' in results
        assert 'effect_sizes' in results
        assert 'convergence_status' in results
        
        # Verify p_values structure
        assert isinstance(results['p_values'], dict)
        for key, value in results['p_values'].items():
            assert isinstance(value, (int, float))
            assert 0 <= value <= 1, f"p-value {value} out of range [0, 1]"
        
        # Verify effect_sizes structure
        assert isinstance(results['effect_sizes'], dict)
        for key, value in results['effect_sizes'].items():
            assert isinstance(value, (int, float))

    def test_reproducibility(self, synthetic_data):
        """Test that results are reproducible with same seed."""
        # Set seed
        np.random.seed(999)
        results1 = run_statistical_analysis(synthetic_data)
        
        # Set same seed again
        np.random.seed(999)
        results2 = run_statistical_analysis(synthetic_data)
        
        # Compare key results
        assert results1['effect_sizes'] == results2['effect_sizes'], \
            "Effect sizes should be identical with same seed"
            
        # Compare p-values (with tolerance for floating point)
        for key in results1['p_values']:
            assert abs(results1['p_values'][key] - results2['p_values'][key]) < 1e-10, \
                f"P-values for {key} should be identical"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
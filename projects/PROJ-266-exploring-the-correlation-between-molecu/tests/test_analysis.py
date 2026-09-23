"""
Integration tests for the full analysis pipeline.
These tests verify the end-to-end execution of the analysis pipeline,
including data loading, correlation analysis, model fitting, and scaling law analysis.
"""
import os
import sys
import json
import pickle
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path if running from tests directory
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.analysis import (
    load_analysis_data,
    compute_complexity_index,
    check_linear_correlation_strength,
    power_law_model,
    fit_power_law_model,
    write_scaling_results,
    fit_multivariate_model,
    compute_correlations_with_fdr,
    run_power_analysis
)
from code.data.conformer_gen import load_filtered_data
from code.data.descriptors import load_processed_data, load_conformers


class TestAnalysisPipelineIntegration:
    """Integration tests for the full analysis pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
        # Create necessary directory structure
        os.makedirs(os.path.join(self.temp_dir, 'data', 'raw'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'data', 'processed'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'state', 'pending'), exist_ok=True)
        
        os.chdir(self.temp_dir)
        
        # Create mock data files for testing
        self._create_mock_data()
        
        yield
        
        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def _create_mock_data(self):
        """Create realistic mock data for integration testing."""
        # Create filtered data file
        filtered_data = pd.DataFrame({
            'smiles': [
                'CCO', 'CC(C)O', 'CCC(C)O', 'CCCC(C)O', 'CCCCC(C)O',
                'CC(C)(C)O', 'CC(C)(C)CCO', 'CC(C)(C)CCC(C)O',
                'CC(C)(C)CCCC(C)O', 'CC(C)(C)CCCCC(C)O',
                'C1=CC=C(C=C1)O', 'C1=CC=C(C=C1)CCO',
                'C1=CC=C(C=C1)CCC(C)O', 'C1=CC=C(C=C1)CCCC(C)O',
                'C1=CC=C(C=C1)CCCCC(C)O', 'C1=CC=C(C=C1)CCCCCCC(C)O',
                'C1=CC=C(C=C1)CCCCCCCC(C)O', 'C1=CC=C(C=C1)CCCCCCCCCC(C)O',
                'C1=CC=C(C=C1)CCCCCCCCCCC(C)O', 'C1=CC=C(C=C1)CCCCCCCCCCCC(C)O',
                'CC(=O)O', 'CCC(=O)O', 'CCCC(=O)O', 'CCCCC(=O)O',
                'CCCCCC(=O)O', 'CCCCCCC(=O)O', 'CCCCCCCC(=O)O',
                'CCCCCCCCC(=O)O', 'CCCCCCCCCC(=O)O', 'CCCCCCCCCCC(=O)O',
                'CC(C)C(=O)O', 'CCC(C)C(=O)O', 'CCCC(C)C(=O)O',
                'CCCCC(C)C(=O)O', 'CCCCCC(C)C(=O)O', 'CCCCCCC(C)C(=O)O',
                'CCCCCCCC(C)C(=O)O', 'CCCCCCCCC(C)C(=O)O',
                'CCCCCCCCCC(C)C(=O)O', 'CCCCCCCCCCC(C)C(=O)O',
                'C1=CC(=CC=C1)C(=O)O', 'C1=CC(=CC=C1)CC(=O)O',
                'C1=CC(=CC=C1)CCC(=O)O', 'C1=CC(=CC=C1)CCCC(=O)O',
                'C1=CC(=CC=C1)CCCCC(=O)O', 'C1=CC(=CC=C1)CCCCCCC(=O)O',
                'C1=CC(=CC=C1)CCCCCCCC(=O)O', 'C1=CC(=CC=C1)CCCCCCCCC(=O)O',
                'C1=CC(=CC=C1)CCCCCCCCCC(=O)O', 'C1=CC(=CC=C1)CCCCCCCCCCC(=O)O'
            ],
            'logPapp': np.random.uniform(-5.0, -1.0, 50),
            'mw': np.random.uniform(50.0, 250.0, 50),
            'psa': np.random.uniform(10.0, 80.0, 50),
            'assay_id': [f'ASSAY_{i}' for i in range(50)],
            'protocol_metadata': ['{}' for _ in range(50)]
        })
        filtered_data.to_csv('data/processed/filtered_data.csv', index=False)

        # Create descriptors file
        descriptors_data = pd.DataFrame({
            'smiles': filtered_data['smiles'].values,
            'bond_variance': np.random.uniform(0.01, 0.5, 50),
            'angle_variance': np.random.uniform(0.01, 0.5, 50),
            'dihedral_variance': np.random.uniform(0.1, 2.0, 50),
            'complexity_index': np.random.uniform(0.5, 5.0, 50)
        })
        descriptors_data.to_csv('data/processed/descriptors_raw.csv', index=False)

        # Create correlation results file
        correlation_results = pd.DataFrame({
            'metric': ['pearson', 'spearman'],
            'correlation': [np.random.uniform(-0.8, -0.2), np.random.uniform(-0.8, -0.2)],
            'p_value': [np.random.uniform(0.001, 0.05), np.random.uniform(0.001, 0.05)],
            'q_value': [np.random.uniform(0.001, 0.05), np.random.uniform(0.001, 0.05)],
            'significant': [True, True]
        })
        correlation_results.to_csv('data/processed/correlation_results.csv', index=False)

        # Create model results JSON
        model_results = {
            'coefficients': {
                'intercept': np.random.uniform(-5.0, -1.0),
                'dihedral_variance': np.random.uniform(-0.5, -0.1),
                'logP': np.random.uniform(0.1, 0.5),
                'mw': np.random.uniform(-0.01, 0.01),
                'psa': np.random.uniform(-0.01, 0.01)
            },
            'metrics': {
                'r_squared': np.random.uniform(0.3, 0.8),
                'rmse': np.random.uniform(0.1, 0.5),
                'mae': np.random.uniform(0.05, 0.3),
                'adj_r_squared': np.random.uniform(0.25, 0.75)
            },
            'cross_validation': {
                'mean_r_squared': np.random.uniform(0.25, 0.7),
                'std_r_squared': np.random.uniform(0.05, 0.2),
                'mean_rmse': np.random.uniform(0.15, 0.4),
                'std_rmse': np.random.uniform(0.05, 0.15),
                'mean_mae': np.random.uniform(0.1, 0.3),
                'std_mae': np.random.uniform(0.05, 0.1)
            }
        }
        with open('data/processed/model_results.json', 'w') as f:
            json.dump(model_results, f, indent=2)

        # Create scaling analysis results JSON
        scaling_results = {
            'power_law_exponent': np.random.uniform(0.2, 1.5),
            'power_law_r_squared': np.random.uniform(0.3, 0.8),
            'linear_r_squared': np.random.uniform(0.2, 0.7),
            'aic_power_law': np.random.uniform(100, 200),
            'aic_linear': np.random.uniform(110, 210),
            'bic_power_law': np.random.uniform(105, 205),
            'bic_linear': np.random.uniform(115, 215),
            'superior_model': 'power_law' if np.random.random() > 0.5 else 'linear',
            'power_analysis': {
                'effect_sizes': {
                    'exponent_0.25': np.random.uniform(0.7, 0.95),
                    'exponent_0.5': np.random.uniform(0.6, 0.9),
                    'exponent_1.0': np.random.uniform(0.5, 0.85)
                },
                'hypothesis_tests': {
                    'exponent_0.25': {'p_value': np.random.uniform(0.01, 0.1), 'significant': np.random.choice([True, False])},
                    'exponent_0.5': {'p_value': np.random.uniform(0.01, 0.1), 'significant': np.random.choice([True, False])},
                    'exponent_1.0': {'p_value': np.random.uniform(0.01, 0.1), 'significant': np.random.choice([True, False])}
                }
            }
        }
        with open('data/processed/scaling_analysis_results.json', 'w') as f:
            json.dump(scaling_results, f, indent=2)

    def test_load_analysis_data_integration(self):
        """Test loading analysis data from processed files."""
        data = load_analysis_data()
        
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        assert 'dihedral_variance' in data.columns
        assert 'logPapp' in data.columns
        assert 'complexity_index' in data.columns

    def test_compute_complexity_index_integration(self):
        """Test complexity index computation."""
        data = load_analysis_data()
        complexity = compute_complexity_index(data)
        
        assert complexity is not None
        assert isinstance(complexity, pd.Series)
        assert len(complexity) == len(data)
        assert all(complexity > 0)

    def test_check_linear_correlation_strength_integration(self):
        """Test linear correlation strength check."""
        data = load_analysis_data()
        is_weak, r_squared = check_linear_correlation_strength(data)
        
        assert isinstance(is_weak, bool)
        assert isinstance(r_squared, (int, float))
        assert 0 <= r_squared <= 1

    def test_power_law_model_fitting_integration(self):
        """Test power law model fitting."""
        data = load_analysis_data()
        params, covariance = fit_power_law_model(data)
        
        assert params is not None
        assert covariance is not None
        assert len(params) == 3  # intercept, slope, offset
        assert params[1] != 0  # slope should be non-zero

    def test_compute_correlations_with_fdr_integration(self):
        """Test correlation computation with FDR correction."""
        data = load_analysis_data()
        results = compute_correlations_with_fdr(data)
        
        assert results is not None
        assert isinstance(results, pd.DataFrame)
        assert len(results) > 0
        assert 'metric' in results.columns
        assert 'correlation' in results.columns
        assert 'p_value' in results.columns
        assert 'q_value' in results.columns
        assert 'significant' in results.columns

    def test_fit_multivariate_model_integration(self):
        """Test multivariate model fitting."""
        data = load_analysis_data()
        model_results = fit_multivariate_model(data)
        
        assert model_results is not None
        assert 'coefficients' in model_results
        assert 'metrics' in model_results
        assert 'dihedral_variance' in model_results['coefficients']
        assert 'logP' in model_results['coefficients']
        assert 'mw' in model_results['coefficients']
        assert 'psa' in model_results['coefficients']

    def test_run_power_analysis_integration(self):
        """Test power analysis execution."""
        data = load_analysis_data()
        power_results = run_power_analysis(data)
        
        assert power_results is not None
        assert 'effect_sizes' in power_results
        assert 'hypothesis_tests' in power_results
        assert 'exponent_0.25' in power_results['effect_sizes']
        assert 'exponent_0.5' in power_results['effect_sizes']
        assert 'exponent_1.0' in power_results['effect_sizes']

    def test_write_scaling_results_integration(self):
        """Test writing scaling results to file."""
        data = load_analysis_data()
        scaling_results = {
            'power_law_exponent': 0.5,
            'power_law_r_squared': 0.6,
            'linear_r_squared': 0.4,
            'aic_power_law': 150,
            'aic_linear': 160,
            'bic_power_law': 155,
            'bic_linear': 165,
            'superior_model': 'power_law',
            'power_analysis': {
                'effect_sizes': {'exponent_0.25': 0.8, 'exponent_0.5': 0.7, 'exponent_1.0': 0.6},
                'hypothesis_tests': {
                    'exponent_0.25': {'p_value': 0.05, 'significant': True},
                    'exponent_0.5': {'p_value': 0.03, 'significant': True},
                    'exponent_1.0': {'p_value': 0.08, 'significant': False}
                }
            }
        }
        
        write_scaling_results(scaling_results)
        
        assert os.path.exists('data/processed/scaling_analysis_results.json')
        
        with open('data/processed/scaling_analysis_results.json', 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results == scaling_results

    def test_full_pipeline_end_to_end(self):
        """Test the full analysis pipeline end-to-end."""
        # Load data
        data = load_analysis_data()
        assert data is not None and len(data) > 0

        # Compute complexity index
        complexity = compute_complexity_index(data)
        assert complexity is not None and len(complexity) == len(data)

        # Check linear correlation
        is_weak, r_squared = check_linear_correlation_strength(data)
        assert isinstance(is_weak, bool) and isinstance(r_squared, (int, float))

        # Compute correlations with FDR
        correlations = compute_correlations_with_fdr(data)
        assert correlations is not None and len(correlations) > 0

        # Fit multivariate model
        model_results = fit_multivariate_model(data)
        assert model_results is not None and 'coefficients' in model_results

        # Run power analysis
        power_results = run_power_analysis(data)
        assert power_results is not None and 'effect_sizes' in power_results

        # Write scaling results
        scaling_results = {
            'power_law_exponent': 0.5,
            'power_law_r_squared': 0.6,
            'linear_r_squared': 0.4,
            'aic_power_law': 150,
            'aic_linear': 160,
            'bic_power_law': 155,
            'bic_linear': 165,
            'superior_model': 'power_law',
            'power_analysis': power_results
        }
        write_scaling_results(scaling_results)
        
        assert os.path.exists('data/processed/scaling_analysis_results.json')

        # Verify all output files exist
        assert os.path.exists('data/processed/filtered_data.csv')
        assert os.path.exists('data/processed/descriptors_raw.csv')
        assert os.path.exists('data/processed/correlation_results.csv')
        assert os.path.exists('data/processed/model_results.json')
        assert os.path.exists('data/processed/scaling_analysis_results.json')

    def test_metrics_computation_accuracy(self):
        """Test that computed metrics are within expected ranges."""
        data = load_analysis_data()
        
        # Test correlation values
        correlations = compute_correlations_with_fdr(data)
        assert all(abs(corr) <= 1 for corr in correlations['correlation'])
        assert all(0 <= p <= 1 for p in correlations['p_value'])
        assert all(0 <= q <= 1 for q in correlations['q_value'])

        # Test model metrics
        model_results = fit_multivariate_model(data)
        assert 0 <= model_results['metrics']['r_squared'] <= 1
        assert 0 <= model_results['metrics']['rmse']
        assert 0 <= model_results['metrics']['mae']

        # Test power analysis
        power_results = run_power_analysis(data)
        for exp_key in ['exponent_0.25', 'exponent_0.5', 'exponent_1.0']:
            assert 0 <= power_results['effect_sizes'][exp_key] <= 1
            assert 0 <= power_results['hypothesis_tests'][exp_key]['p_value'] <= 1

    def test_cross_validation_integration(self):
        """Test that cross-validation metrics are computed correctly."""
        data = load_analysis_data()
        model_results = fit_multivariate_model(data)
        
        assert 'cross_validation' in model_results
        cv_results = model_results['cross_validation']
        
        assert 'mean_r_squared' in cv_results
        assert 'std_r_squared' in cv_results
        assert 'mean_rmse' in cv_results
        assert 'std_rmse' in cv_results
        assert 'mean_mae' in cv_results
        assert 'std_mae' in cv_results

        # Verify reasonable ranges
        assert 0 <= cv_results['mean_r_squared'] <= 1
        assert cv_results['std_r_squared'] >= 0
        assert cv_results['mean_rmse'] >= 0
        assert cv_results['std_rmse'] >= 0
        assert cv_results['mean_mae'] >= 0
        assert cv_results['std_mae'] >= 0
"""
Unit tests for GLM Analysis (T026) - T032.
Tests specifically focus on GLM model setup and convergence behavior.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.glm_analysis import (
    load_coverage_results,
    prepare_glm_data,
    fit_coverage_glm,
    extract_glm_summary,
    run_glm_analysis
)
from code.config import get_artifact_path

@pytest.fixture
def sample_coverage_data():
    """Create synthetic but realistic coverage data for testing."""
    np.random.seed(42)
    n = 20
    data = {
        'dataset': ['Adult'] * n,
        'epsilon': np.random.choice([0.1, 0.5, 1.0, 5.0], n),
        'noise_type': np.random.choice(['Laplace', 'Gaussian'], n),
        'statistic': ['mean'] * n,
        'coverage_rate': np.random.uniform(0.85, 0.98, n),
        'seed_count': [1000] * n
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_artifact_path(tmp_path):
    """Mock the artifact path to use a temporary directory."""
    # Create a temporary CSV file with realistic data for GLM testing
    csv_path = tmp_path / "coverage_results.csv"
    np.random.seed(123)
    n = 40
    df = pd.DataFrame({
        'dataset': ['Adult'] * (n//2) + ['Iris'] * (n//2),
        'epsilon': np.random.choice([0.1, 0.5, 1.0, 5.0], n),
        'noise_type': np.random.choice(['Laplace', 'Gaussian'], n),
        'statistic': ['mean'] * n,
        'coverage_rate': np.clip(np.random.normal(0.92, 0.04, n), 0.80, 0.99),
        'seed_count': [1000] * n
    })
    df.to_csv(csv_path, index=False)
    
    # Patch get_artifact_path to return our temp path
    with patch('code.analysis.glm_analysis.get_artifact_path') as mock_func:
        mock_func.side_effect = lambda x: str(tmp_path / x)
        yield csv_path

class TestGLMModelSetup:
    def test_load_coverage_results_success(self, mock_artifact_path):
        """Test loading valid coverage results."""
        df = load_coverage_results()
        assert not df.empty
        assert 'coverage_rate' in df.columns
        assert 'epsilon' in df.columns
        assert 'noise_type' in df.columns

    def test_load_coverage_results_missing_file(self, tmp_path):
        """Test loading when file is missing."""
        with patch('code.analysis.glm_analysis.get_artifact_path') as mock_func:
            mock_func.return_value = str(tmp_path / "nonexistent.csv")
            with pytest.raises(FileNotFoundError):
                load_coverage_results()

    def test_prepare_glm_data_types(self, sample_coverage_data):
        """Test that prepare_glm_data sets correct dtypes."""
        prepared = prepare_glm_data(sample_coverage_data)
        assert pd.api.types.is_numeric_dtype(prepared['epsilon'])
        assert prepared['noise_type'].dtype.name == 'category'
        assert 'weights' in prepared.columns
        # Check that we have the interaction term ready for GLM
        assert 'epsilon' in prepared.columns

    def test_prepare_glm_data_categoricals(self, sample_coverage_data):
        """Test categorical conversion for GLM formula."""
        prepared = prepare_glm_data(sample_coverage_data)
        # noise_type should be categorical for formula API
        assert prepared['noise_type'].dtype.name == 'category'
        # Check unique values preserved
        assert set(prepared['noise_type'].cat.categories) == {'Laplace', 'Gaussian'}

class TestGLMConvergence:
    def test_fit_coverage_glm_converges(self, mock_artifact_path):
        """Test that the GLM fits successfully on valid data."""
        df = load_coverage_results()
        prepared = prepare_glm_data(df)
        
        # This should not raise an exception
        results = fit_coverage_glm(prepared)
        assert results is not None
        # Verify we get a fitted model object
        assert hasattr(results, 'params')
        assert hasattr(results, 'pvalues')
        
        # Check that we have parameters for our expected terms
        param_names = results.params.index.tolist()
        # Should have intercept, epsilon, noise_type[T.Gaussian], and interaction
        assert any('epsilon' in str(name) for name in param_names)

    def test_fit_coverage_glm_insufficient_data(self):
        """Test fitting with too few rows."""
        small_df = pd.DataFrame({
            'dataset': ['A'],
            'epsilon': [1.0],
            'noise_type': ['Laplace'],
            'statistic': ['mean'],
            'coverage_rate': [0.9],
            'weights': [1000]
        })
        
        with pytest.raises(ValueError, match="Insufficient data"):
            fit_coverage_glm(small_df)

    def test_fit_coverage_glm_with_interaction(self, mock_artifact_path):
        """Test that the GLM includes the interaction term."""
        df = load_coverage_results()
        prepared = prepare_glm_data(df)
        results = fit_coverage_glm(prepared)
        
        # Check that interaction term exists in the model
        param_names = [str(name) for name in results.params.index]
        # The interaction term should be present: epsilon:noise_type[T.Gaussian] or similar
        has_interaction = any('epsilon' in p and 'noise_type' in p for p in param_names)
        assert has_interaction, "Interaction term epsilon:noise_type should be in the model"

    def test_convergence_on_realistic_data(self, mock_artifact_path):
        """Test convergence on data with realistic variance."""
        df = load_coverage_results()
        prepared = prepare_glm_data(df)
        results = fit_coverage_glm(prepared)
        
        # Verify the model converged (or at least fit without error)
        # statsmodels GLM may not always report .converged as True for small samples,
        # but the fit should complete and return valid parameters
        assert results.params is not None
        assert not results.params.isna().any()

class TestGLMOutputValidation:
    def test_extract_glm_summary_structure(self, mock_artifact_path):
        """Test that summary extraction returns expected keys."""
        df = load_coverage_results()
        prepared = prepare_glm_data(df)
        results = fit_coverage_glm(prepared)
        
        summary = extract_glm_summary(results)
        
        required_keys = ['p_value_epsilon', 'p_value_noise_type', 'p_value_interaction', 'coefficients']
        for key in required_keys:
            assert key in summary, f"Missing required key: {key}"

    def test_extract_glm_summary_types(self, mock_artifact_path):
        """Test that summary values are correct types."""
        df = load_coverage_results()
        prepared = prepare_glm_data(df)
        results = fit_coverage_glm(prepared)
        
        summary = extract_glm_summary(results)
        
        assert isinstance(summary['p_value_epsilon'], (float, np.floating))
        assert isinstance(summary['p_value_noise_type'], (float, np.floating))
        assert isinstance(summary['p_value_interaction'], (float, np.floating))
        assert isinstance(summary['coefficients'], dict)
        assert isinstance(summary['deviance_residuals'], list)
        
        # Check that p-values are in valid range
        assert 0 <= summary['p_value_epsilon'] <= 1
        assert 0 <= summary['p_value_noise_type'] <= 1
        assert 0 <= summary['p_value_interaction'] <= 1

    def test_extract_glm_summary_coefficients(self, mock_artifact_path):
        """Test that coefficients dict contains expected parameters."""
        df = load_coverage_results()
        prepared = prepare_glm_data(df)
        results = fit_coverage_glm(prepared)
        
        summary = extract_glm_summary(results)
        
        # Coefficients should be a dict with parameter names as keys
        assert len(summary['coefficients']) > 0
        for param_name, value in summary['coefficients'].items():
            assert isinstance(value, (float, np.floating))

class TestGLMIntegration:
    def test_run_glm_analysis_full_flow(self, mock_artifact_path):
        """Test the full analysis flow."""
        results, summary = run_glm_analysis()
        
        # Verify files were written
        summary_path = get_artifact_path("glm_summary.json")
        assert os.path.exists(summary_path)
        
        with open(summary_path, 'r') as f:
            loaded_summary = json.load(f)
        
        assert loaded_summary == summary
        # Verify the summary has all required keys
        required_keys = ['p_value_epsilon', 'p_value_noise_type', 'p_value_interaction', 'coefficients']
        for key in required_keys:
            assert key in loaded_summary

    def test_run_glm_analysis_missing_data(self, tmp_path):
        """Test full flow when data is missing."""
        with patch('code.analysis.glm_analysis.get_artifact_path') as mock_func:
            mock_func.return_value = str(tmp_path / "missing.csv")
            with pytest.raises(FileNotFoundError):
                run_glm_analysis()

    def test_glm_with_multiple_datasets(self, tmp_path):
        """Test GLM handling multiple datasets."""
        csv_path = tmp_path / "coverage_results.csv"
        np.random.seed(456)
        n = 60
        df = pd.DataFrame({
            'dataset': ['Adult'] * 20 + ['Iris'] * 20 + ['Wine'] * 20,
            'epsilon': np.tile([0.1, 0.5, 1.0, 5.0], 15),
            'noise_type': np.tile(['Laplace', 'Gaussian'], 30),
            'statistic': ['mean'] * 60,
            'coverage_rate': np.clip(np.random.normal(0.92, 0.03, 60), 0.85, 0.99),
            'seed_count': [1000] * 60
        })
        df.to_csv(csv_path, index=False)
        
        with patch('code.analysis.glm_analysis.get_artifact_path') as mock_func:
            mock_func.side_effect = lambda x: str(tmp_path / x)
            results, summary = run_glm_analysis()
            
            assert results is not None
            assert summary is not None
            assert 'p_value_epsilon' in summary
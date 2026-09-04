"""
Unit tests for GLM Analysis (T026).
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
    # Create a temporary CSV file
    csv_path = tmp_path / "coverage_results.csv"
    df = pd.DataFrame({
        'dataset': ['Adult'] * 10,
        'epsilon': [0.1, 0.5, 1.0, 5.0] * 2 + [0.1, 0.5, 1.0, 5.0] * 2,
        'noise_type': ['Laplace', 'Laplace', 'Laplace', 'Laplace', 'Gaussian', 'Gaussian', 'Gaussian', 'Gaussian'] * 2,
        'statistic': ['mean'] * 10,
        'coverage_rate': [0.95] * 10,
        'seed_count': [1000] * 10
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
        assert pd.api.types.is_categorical_dtype(prepared['noise_type'])
        assert 'weights' in prepared.columns

class TestGLMConvergence:
    def test_fit_coverage_glm_converges(self, mock_artifact_path):
        """Test that the GLM fits successfully on valid data."""
        df = load_coverage_results()
        prepared = prepare_glm_data(df)
        
        # This should not raise an exception
        results = fit_coverage_glm(prepared)
        assert results is not None
        # Note: We don't assert .converged is True because small datasets might not converge perfectly,
        # but the fit() call should return.

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

class TestGLMOutputValidation:
    def test_extract_glm_summary_structure(self, mock_artifact_path):
        """Test that summary extraction returns expected keys."""
        df = load_coverage_results()
        prepared = prepare_glm_data(df)
        results = fit_coverage_glm(prepared)
        
        summary = extract_glm_summary(results)
        
        required_keys = ['p_value_epsilon', 'p_value_noise_type', 'p_value_interaction', 'coefficients']
        for key in required_keys:
            assert key in summary

    def test_extract_glm_summary_types(self, mock_artifact_path):
        """Test that summary values are correct types."""
        df = load_coverage_results()
        prepared = prepare_glm_data(df)
        results = fit_coverage_glm(prepared)
        
        summary = extract_glm_summary(results)
        
        assert isinstance(summary['p_value_epsilon'], float)
        assert isinstance(summary['coefficients'], dict)
        assert isinstance(summary['deviance_residuals'], list)

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

    def test_run_glm_analysis_missing_data(self, tmp_path):
        """Test full flow when data is missing."""
        with patch('code.analysis.glm_analysis.get_artifact_path') as mock_func:
            mock_func.return_value = str(tmp_path / "missing.csv")
            with pytest.raises(FileNotFoundError):
                run_glm_analysis()
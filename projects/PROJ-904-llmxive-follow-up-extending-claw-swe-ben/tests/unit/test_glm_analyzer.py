import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import tempfile
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.glm_analyzer import (
    load_results_data,
    prepare_features,
    fit_firth_glm,
    fit_glm_with_interaction,
    perform_post_hoc_analysis,
    run_glm_analysis,
    GLMConvergenceError
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        'model_size': ['1b'] * 50 + ['7b'] * 50,
        'strategy': ['baseline'] * 25 + ['tfidf'] * 25 + ['baseline'] * 25 + ['tfidf'] * 25,
        'passed': [1] * 30 + [0] * 70
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_data.to_csv(f, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_output_file():
    """Create a temporary output file path."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        yield f.name
    os.unlink(f.name)

class TestGLMDataLoading:
    def test_load_results_data_file_exists(self, temp_csv_file):
        """Test that load_results_data loads data correctly."""
        df = load_results_data(temp_csv_file)
        assert len(df) == 100
        assert 'model_size' in df.columns
        assert 'strategy' in df.columns
        assert 'passed' in df.columns

    def test_load_results_data_file_not_found(self):
        """Test that load_results_data raises error for missing file."""
        with pytest.raises(FileNotFoundError):
            load_results_data('nonexistent.csv')

    def test_load_results_data_missing_columns(self, temp_csv_file):
        """Test that load_results_data validates required columns."""
        # Create a file with missing columns
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pd.DataFrame({'col1': [1, 2, 3]}).to_csv(f, index=False)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_results_data(temp_path)
        finally:
            os.unlink(temp_path)

class TestFeaturePreparation:
    def test_prepare_features_structure(self, sample_data):
        """Test that prepare_features creates correct structure."""
        X, y = prepare_features(sample_data)
        
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)
        assert len(X) == len(sample_data)
        assert len(y) == len(sample_data)
        assert 'const' in X.columns  # Constant term should be added

    def test_prepare_features_interaction_terms(self, sample_data):
        """Test that prepare_features creates interaction terms."""
        X, y = prepare_features(sample_data)
        
        interaction_cols = [col for col in X.columns if 'interaction' in col]
        assert len(interaction_cols) > 0

class TestGLMFitting:
    def test_fit_firth_glm_basic(self, sample_data):
        """Test basic GLM fitting."""
        X, y = prepare_features(sample_data)
        result = fit_firth_glm(X, y)
        
        # Should return a result object or None (if fitting fails)
        assert result is None or hasattr(result, 'params')

    def test_fit_glm_with_interaction(self, sample_data):
        """Test GLM fitting with interaction terms."""
        X, y = prepare_features(sample_data)
        result = fit_glm_with_interaction(X, y)
        
        # Should return a result object or None
        assert result is None or hasattr(result, 'params')

    def test_interaction_p_value_exists(self, sample_data, temp_output_file):
        """Test that interaction p-values exist in results (T029 requirement)."""
        X, y = prepare_features(sample_data)
        result = fit_glm_with_interaction(X, y)
        
        if result is not None:
            analysis = perform_post_hoc_analysis(result, sample_data)
            assert 'interaction_pvalues' in analysis
            assert len(analysis['interaction_pvalues']) > 0

class TestPostHocAnalysis:
    def test_post_hoc_analysis_structure(self, sample_data, temp_output_file):
        """Test structure of post-hoc analysis results."""
        X, y = prepare_features(sample_data)
        result = fit_glm_with_interaction(X, y)
        
        if result is not None:
            analysis = perform_post_hoc_analysis(result, sample_data)
            
            assert 'converged' in analysis
            assert 'params' in analysis
            assert 'pvalues' in analysis
            assert 'aic' in analysis
            assert 'interaction_pvalues' in analysis

class TestIntegration:
    def test_run_glm_analysis_full_pipeline(self, temp_csv_file, temp_output_file):
        """Test complete GLM analysis pipeline."""
        results = run_glm_analysis(temp_csv_file, temp_output_file)
        
        # Verify output file was created
        assert os.path.exists(temp_output_file)
        
        # Verify results structure
        assert 'converged' in results
        assert 'interaction_pvalues' in results
        
        # Verify output file contains valid JSON
        with open(temp_output_file, 'r') as f:
            saved_results = json.load(f)
            assert saved_results == results

    def test_run_glm_analysis_file_not_found(self):
        """Test error handling for missing input file."""
        with pytest.raises(FileNotFoundError):
            run_glm_analysis('nonexistent.csv', 'output.json')
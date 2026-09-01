"""
Unit tests for GLM Analysis module (T026).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.glm_analysis import fit_coverage_glm, run_glm_analysis
import statsmodels.api as sm


def create_synthetic_coverage_data():
    """
    Create a synthetic DataFrame that mimics the structure of artifacts/coverage_results.csv
    with binary 'covered' outcomes.
    """
    np.random.seed(42)
    n = 200
    
    data = {
        'epsilon': np.repeat([0.1, 0.5, 1.0, 5.0], n // 4),
        'noise_type': np.tile(['Laplace', 'Gaussian'], n // 2),
        'dataset': np.random.choice(['Adult', 'Iris', 'Wine'], n),
        'statistic': np.random.choice(['Mean', 'Regression'], n),
        'covered': np.random.choice([0, 1], n, p=[0.05, 0.95]) # Mostly covered
    }
    
    # Add some noise to epsilon to avoid perfect separation issues if any
    data['epsilon'] = data['epsilon'] + np.random.normal(0, 0.01, n)
    
    return pd.DataFrame(data)


class TestGLMModelSetup:
    def test_fit_glm_basic(self):
        """Test that GLM fits successfully on valid data."""
        df = create_synthetic_coverage_data()
        model, result = fit_coverage_glm(df)
        
        assert model is not None
        assert result is not None
        assert isinstance(result, sm.genmod.generalized_linear_model.GLMResultsWrapper)
        assert result.converged


class TestGLMConvergence:
    def test_convergence_check(self):
        """Test that the model converges on reasonable data."""
        df = create_synthetic_coverage_data()
        model, result = fit_coverage_glm(df)
        
        # GLM with binomial family should converge on this data
        assert result.converged, "GLM did not converge on synthetic data"


class TestGLMOutputValidation:
    def test_coefficients_shape(self):
        """Test that coefficients are returned correctly."""
        df = create_synthetic_coverage_data()
        model, result = fit_coverage_glm(df)
        
        assert len(result.params) > 0
        assert len(result.pvalues) > 0
        assert 'epsilon' in result.params.index or any('epsilon' in idx for idx in result.params.index)
        
    def test_formula_correctness(self):
        """Test that the formula includes the interaction term."""
        df = create_synthetic_coverage_data()
        formula = "covered ~ epsilon * noise_type"
        model, result = fit_coverage_glm(df, formula=formula)
        
        # Check that the formula was set correctly
        assert model.formula == formula
        
        # Check that interaction terms exist in the model matrix
        # The formula 'epsilon * noise_type' expands to 'epsilon + noise_type + epsilon:noise_type'
        assert 'epsilon:noise_type' in str(model.model.exog_names) or any('epsilon' in name and 'noise_type' in name for name in model.model.exog_names)


class TestGLMRobustness:
    def test_missing_columns(self):
        """Test that missing columns raise an error."""
        df = pd.DataFrame({'epsilon': [1, 2], 'noise_type': ['A', 'B']})
        with pytest.raises(ValueError, match="Input DataFrame must contain a 'covered' column"):
            fit_coverage_glm(df)
            
    def test_empty_data(self):
        """Test that empty data raises an error."""
        df = pd.DataFrame(columns=['covered', 'epsilon', 'noise_type'])
        with pytest.raises(ValueError, match="DataFrame is empty after dropping NaNs"):
            fit_coverage_glm(df)
            
    def test_non_binary_covered(self):
        """Test behavior with non-binary covered values (should warn or handle)."""
        df = create_synthetic_coverage_data()
        df['covered'] = df['covered'].astype(float) + 0.5 # Make it 0.5 or 1.5
        # This might cause issues with Binomial family if not handled, 
        # but the function attempts to coerce. We expect it to either work or raise a specific error.
        # For now, we just check it doesn't crash silently with wrong results.
        with pytest.raises(Exception):
            # Binomial GLM expects 0/1 or counts/trials. 0.5/1.5 is invalid.
            fit_coverage_glm(df)


class TestGLMIntegration:
    def test_run_glm_analysis_file_exists(self, tmp_path):
        """Test run_glm_analysis with a temporary file."""
        # Create a temporary CSV
        df = create_synthetic_coverage_data()
        csv_path = tmp_path / "coverage_results.csv"
        df.to_csv(csv_path, index=False)
        
        # Temporarily change the working directory or mock the path
        # Since run_glm_analysis hardcodes "artifacts/coverage_results.csv",
        # we will test the core logic by calling fit_coverage_glm directly on loaded data
        # to avoid file system dependency in unit tests, OR we can create the artifacts dir.
        
        # Let's create the artifacts directory in tmp and run
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "coverage_results.csv").write_text(df.to_csv(index=False))
        
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # This should work now
            result = run_glm_analysis()
            assert result is not None
            assert (tmp_path / "artifacts" / "glm_summary.json").exists()
        finally:
            os.chdir(original_cwd)

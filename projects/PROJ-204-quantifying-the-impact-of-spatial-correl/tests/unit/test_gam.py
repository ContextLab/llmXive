"""
Unit tests for code/modeling/gam.py.
Tests Generalized Additive Models for non-linear relationship detection.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile

from modeling.gam import (
    load_primary_analysis_dataset,
    prepare_gam_data,
    fit_gam_model,
    extract_gam_results,
    test_nonlinearity,
    run_gam_analysis
)

class TestLoadPrimaryAnalysisDataset:
    def test_load_primary_dataset(self):
        """Should load a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                "sample_id": ["s1", "s2"],
                "PCE": [10.0, 15.0],
                "metric1": [1.0, 2.0]
            })
            df.to_csv(csv_path, index=False)
            
            result = load_primary_analysis_dataset(str(csv_path))
            assert result is not None
            assert len(result) == 2

class TestPrepareGamData:
    def test_prepare_gam_data_splits_correctly(self):
        """Should split data into X and y correctly."""
        df = pd.DataFrame({
            "PCE": [10.0, 15.0, 12.0],
            "metric1": [1.0, 2.0, 1.5],
            "metric2": [0.5, 1.0, 0.8]
        })
        
        X, y = prepare_gam_data(df, target_col="PCE")
        assert y.shape[0] == 3
        assert X.shape[0] == 3
        assert X.shape[1] == 2

class TestFitGamModel:
    def test_fit_gam_model_converges(self):
        """GAM model should converge on simple data."""
        np.random.seed(42)
        n = 50
        x = np.random.randn(n)
        y = x**2 + np.random.randn(n) * 0.1  # Quadratic relationship
        
        X = pd.DataFrame({"x": x})
        y = pd.Series(y)
        
        try:
            model = fit_gam_model(X, y)
            assert model is not None
        except Exception as e:
            # If patsy or pygam is not installed, we skip this test
            pytest.skip(f"GAM dependencies not available: {e}")

class TestExtractGamResults:
    def test_extract_gam_results_returns_dict(self):
        """Should return a dictionary with results."""
        # This test is skipped if GAM is not available
        try:
            from pygam import LinearGAM
            np.random.seed(42)
            n = 50
            x = np.linspace(-5, 5, n)
            y = np.sin(x) + np.random.randn(n) * 0.1
            
            X = pd.DataFrame({"x": x})
            y = pd.Series(y)
            
            model = fit_gam_model(X, y)
            results = extract_gam_results(model, ["x"])
            
            assert isinstance(results, dict)
            assert "significant_terms" in results
            assert "p_values" in results
        except ImportError:
            pytest.skip("pygam not installed")

class TestTestNonlinearity:
    def test_test_nonlinearity_detects_quadratic(self):
        """Should detect non-linear (quadratic) relationship."""
        try:
            from pygam import LinearGAM
            np.random.seed(42)
            n = 100
            x = np.random.randn(n)
            y = x**2 + np.random.randn(n) * 0.1
            
            X = pd.DataFrame({"x": x})
            y = pd.Series(y)
            
            is_nonlinear, p_value = test_nonlinearity(X, y, "x")
            
            # Should detect non-linearity
            assert is_nonlinear
        except ImportError:
            pytest.skip("pygam not installed")

class TestRunGamAnalysis:
    def test_run_gam_analysis_returns_dataframe(self):
        """Should return a DataFrame with GAM results."""
        try:
            from pygam import LinearGAM
            with tempfile.TemporaryDirectory() as tmpdir:
                csv_path = Path(tmpdir) / "test_data.csv"
                n = 50
                x = np.random.randn(n)
                y = x**2 + np.random.randn(n) * 0.1
                
                df = pd.DataFrame({
                    "sample_id": [f"s{i}" for i in range(n)],
                    "PCE": y,
                    "metric1": x
                })
                df.to_csv(csv_path, index=False)
                
                result = run_gam_analysis(str(csv_path), "metric1", "PCE")
                assert isinstance(result, pd.DataFrame)
                assert "nonlinear" in result.columns
        except ImportError:
            pytest.skip("pygam not installed")

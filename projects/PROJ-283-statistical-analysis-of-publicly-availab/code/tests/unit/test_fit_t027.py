import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import tempfile
from src.models.fit import save_model_metrics, fit_beta_regression, fit_gaussian_glm, fit_ridge_regression, prepare_features_for_modeling

class TestT027ModelMetrics:
    @pytest.fixture
    def sample_data(self):
        # Create a small synthetic dataset for testing the pipeline logic
        data = {
            'material_imbalance_move5': np.random.randn(100),
            'eco_code': ['A', 'B', 'C', 'D'] * 25,
            'outcome_deviation': np.random.randn(100) * 0.5
        }
        df = pd.DataFrame(data)
        return df

    @pytest.fixture
    def temp_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            processed_path = Path(tmpdir) / "games.parquet"
            output_path = Path(tmpdir) / "model_metrics.json"
            yield processed_path, output_path

    def test_prepare_features(self, sample_data):
        X, y = prepare_features_for_modeling(sample_data)
        assert X.shape[0] == 100
        assert 'material_imbalance_move5' in X.columns
        assert len(y) == 100

    def test_fit_beta_regression(self, sample_data):
        X, y = prepare_features_for_modeling(sample_data)
        result = fit_beta_regression(X, y)
        assert result['model_type'] == "Beta Regression"
        assert 'coefficients' in result
        assert 'r_squared' in result
        assert result['fitted'] is True

    def test_fit_gaussian_glm(self, sample_data):
        X, y = prepare_features_for_modeling(sample_data)
        result = fit_gaussian_glm(X, y)
        assert result['model_type'] == "Gaussian GLM"
        assert result['fitted'] is True

    def test_fit_ridge_regression(self, sample_data):
        X, y = prepare_features_for_modeling(sample_data)
        result = fit_ridge_regression(X, y)
        assert result['model_type'] == "Ridge Regression"
        assert result['fitted'] is True

    def test_save_model_metrics(self, sample_data, temp_dirs):
        processed_path, output_path = temp_dirs
        # Save sample data as parquet
        sample_data.to_parquet(processed_path)
        
        # Run the main function
        result = save_model_metrics(processed_path, output_path)
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify JSON content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'models' in data
        assert len(data['models']) == 3
        assert 'significant_predictors' in data
        assert 'cv_summary' in data
        assert 'mean_r2' in data['cv_summary']
        assert 'std_r2' in data['cv_summary']
        
        # Check schema compliance (basic)
        for model in data['models']:
            assert 'model_type' in model
            assert 'coefficients' in model
            assert 'p_values' in model
            assert 'r_squared' in model
            assert 'aic' in model
            assert 'cross_validation_scores' in model
            assert len(model['cross_validation_scores']) > 0
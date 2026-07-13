import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.linear_trainer import LinearRegressionTrainer, main
from utils.error_handlers import ModelTrainingError


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        'Cu': [0.6, 0.7, 0.5, 0.8, 0.65],
        'Ag': [0.2, 0.15, 0.25, 0.1, 0.2],
        'Sn': [0.2, 0.15, 0.25, 0.1, 0.15],
        'hardness_hv': [45.0, 50.0, 42.0, 55.0, 48.0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestLinearRegressionTrainer:
    """Tests for LinearRegressionTrainer class."""

    def test_init(self):
        """Test trainer initialization."""
        trainer = LinearRegressionTrainer(seed=42)
        assert trainer.seed == 42
        assert trainer.model is not None
        assert trainer.metrics == {}
        assert trainer.cv_scores is None
        assert trainer.feature_names is None
        assert trainer.target_name == "hardness_hv"

    def test_load_data_missing_file(self):
        """Test loading non-existent data file raises error."""
        trainer = LinearRegressionTrainer()
        with pytest.raises(ModelTrainingError, match="Validated data file not found"):
            trainer.load_data(Path("/nonexistent/path.csv"))

    def test_load_data_missing_target(self, sample_data, temp_output_dir):
        """Test loading data without target column raises error."""
        # Save sample data without target
        path = temp_output_dir / "test.csv"
        sample_data.drop(columns=['hardness_hv']).to_csv(path, index=False)
        
        trainer = LinearRegressionTrainer()
        with pytest.raises(ModelTrainingError, match="Target column"):
            trainer.load_data(path)

    def test_load_data_success(self, sample_data, temp_output_dir):
        """Test successful data loading."""
        path = temp_output_dir / "test.csv"
        sample_data.to_csv(path, index=False)
        
        trainer = LinearRegressionTrainer()
        df = trainer.load_data(path)
        
        assert len(df) == 5
        assert 'hardness_hv' in df.columns
        assert 'Cu' in df.columns
        assert trainer.feature_names == ['Cu', 'Ag', 'Sn']

    def test_train(self, sample_data, temp_output_dir):
        """Test model training."""
        path = temp_output_dir / "test.csv"
        sample_data.to_csv(path, index=False)
        
        trainer = LinearRegressionTrainer()
        df = trainer.load_data(path)
        trainer.train(df)
        
        assert trainer.model.coef_ is not None
        assert len(trainer.model.coef_) == 3
        assert trainer.model.intercept_ is not None

    def test_evaluate_cv(self, sample_data, temp_output_dir):
        """Test cross-validation evaluation."""
        path = temp_output_dir / "test.csv"
        sample_data.to_csv(path, index=False)
        
        trainer = LinearRegressionTrainer()
        df = trainer.load_data(path)
        trainer.train(df)
        
        metrics = trainer.evaluate_cv(df, cv_folds=3)
        
        assert 'cv_r2_mean' in metrics
        assert 'cv_r2_std' in metrics
        assert 'cv_rmse_mean' in metrics
        assert 'cv_rmse_std' in metrics
        assert metrics['cv_folds'] == 3
        assert len(metrics['r2_scores']) == 3

    def test_evaluate_test(self, sample_data, temp_output_dir):
        """Test test set evaluation."""
        path = temp_output_dir / "test.csv"
        sample_data.to_csv(path, index=False)
        
        trainer = LinearRegressionTrainer()
        df = trainer.load_data(path)
        trainer.train(df)
        
        metrics = trainer.evaluate_test(df)
        
        assert 'test_r2' in metrics
        assert 'test_rmse' in metrics
        assert 'test_mae' in metrics
        assert metrics['n_samples'] == 5

    def test_get_coefficients(self, sample_data, temp_output_dir):
        """Test getting model coefficients."""
        path = temp_output_dir / "test.csv"
        sample_data.to_csv(path, index=False)
        
        trainer = LinearRegressionTrainer()
        df = trainer.load_data(path)
        trainer.train(df)
        
        coeffs = trainer.get_coefficients()
        
        assert isinstance(coeffs, dict)
        assert 'Cu' in coeffs
        assert 'Ag' in coeffs
        assert 'Sn' in coeffs
        assert len(coeffs) == 3

    def test_get_intercept(self, sample_data, temp_output_dir):
        """Test getting model intercept."""
        path = temp_output_dir / "test.csv"
        sample_data.to_csv(path, index=False)
        
        trainer = LinearRegressionTrainer()
        df = trainer.load_data(path)
        trainer.train(df)
        
        intercept = trainer.get_intercept()
        
        assert isinstance(intercept, float)

    def test_save_artifacts(self, sample_data, temp_output_dir):
        """Test saving model artifacts."""
        path = temp_output_dir / "test.csv"
        sample_data.to_csv(path, index=False)
        
        trainer = LinearRegressionTrainer()
        df = trainer.load_data(path)
        trainer.train(df)
        trainer.metrics = {"test_r2": 0.85}
        trainer.cv_scores = np.array([0.8, 0.85, 0.9])
        
        output_dir = trainer.save_artifacts(temp_output_dir)
        
        model_path = output_dir / "linear_regression_model.json"
        assert model_path.exists()
        
        with open(model_path, 'r') as f:
            model_info = json.load(f)
        
        assert model_info['model_type'] == 'LinearRegression'
        assert model_info['seed'] == 42
        assert 'coefficients' in model_info
        assert 'intercept' in model_info
        assert 'metrics' in model_info

    def test_run_full_pipeline(self, sample_data, temp_output_dir):
        """Test complete training pipeline."""
        path = temp_output_dir / "test.csv"
        sample_data.to_csv(path, index=False)
        
        # Mock config functions to use temp directory
        with patch('models.linear_trainer.get_data_processed_dir', return_value=str(temp_output_dir)):
            with patch('models.linear_trainer.get_models_dir', return_value=str(temp_output_dir)):
                with patch('models.linear_trainer.get_cv_folds', return_value=3):
                    trainer = LinearRegressionTrainer()
                    results = trainer.run_full_pipeline(path)
                    
                    assert 'metrics' in results
                    assert 'output_dir' in results
                    assert 'model_path' in results
                    assert 'cv_r2_mean' in results['metrics']
                    assert 'test_r2' in results['metrics']
                    assert os.path.exists(results['model_path'])


class TestMainFunction:
    """Tests for the main() function."""

    def test_main_success(self, sample_data, temp_output_dir, caplog):
        """Test main function with valid data."""
        path = temp_output_dir / "test.csv"
        sample_data.to_csv(path, index=False)
        
        with patch('models.linear_trainer.get_data_processed_dir', return_value=str(temp_output_dir)):
            with patch('models.linear_trainer.get_models_dir', return_value=str(temp_output_dir)):
                with patch('models.linear_trainer.get_cv_folds', return_value=3):
                    with patch('models.linear_trainer.setup_logging'):
                        with patch('models.linear_trainer.get_log_level', return_value='INFO'):
                            with patch('models.linear_trainer.get_log_format', return_value='%(message)s'):
                                result = main()
                                
                                assert 'metrics' in result
                                assert 'model_path' in result
                                assert os.path.exists(result['model_path'])

    def test_main_missing_data(self, temp_output_dir, caplog):
        """Test main function with missing data file."""
        with patch('models.linear_trainer.get_data_processed_dir', return_value=str(temp_output_dir)):
            with patch('models.linear_trainer.setup_logging'):
                with patch('models.linear_trainer.get_log_level', return_value='INFO'):
                    with patch('models.linear_trainer.get_log_format', return_value='%(message)s'):
                        with pytest.raises(ModelTrainingError):
                            main()

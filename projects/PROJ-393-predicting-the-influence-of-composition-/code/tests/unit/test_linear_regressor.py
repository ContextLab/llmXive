"""
Unit tests for the Linear Regression Model module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.models.linear_regressor import (
    load_features_data,
    prepare_data,
    create_model_pipeline,
    evaluate_model,
    run_linear_regression
)


class TestLoadFeaturesData:
    def test_load_valid_data(self):
        """Test loading a valid features CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("average_electronegativity,valence_electron_concentration,atomic_radii_variance,average_d_electrons,atomic_size_mismatch,coercivity_normalized\n")
            f.write("1.5,8.5,0.1,5.2,0.05,100.0\n")
            f.write("1.6,8.6,0.12,5.3,0.06,120.0\n")
            temp_path = Path(f.name)

        try:
            df = load_features_data(temp_path)
            assert len(df) == 2
            assert 'coercivity_normalized' in df.columns
        finally:
            temp_path.unlink()

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_features_data(Path("nonexistent_file.csv"))

    def test_missing_required_columns(self):
        """Test that ValueError is raised for missing columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("col1,col2\n")
            f.write("1,2\n")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_features_data(temp_path)
            assert "Missing required columns" in str(exc_info.value)
        finally:
            temp_path.unlink()


class TestPrepareData:
    def test_prepare_data_basic(self):
        """Test basic data preparation."""
        df = pd.DataFrame({
            'average_electronegativity': [1.5, 1.6],
            'valence_electron_concentration': [8.5, 8.6],
            'atomic_radii_variance': [0.1, 0.12],
            'average_d_electrons': [5.2, 5.3],
            'atomic_size_mismatch': [0.05, 0.06],
            'coercivity_normalized': [100.0, 120.0]
        })

        X, y = prepare_data(df, 'coercivity_normalized')

        assert X.shape == (2, 5)
        assert y.shape == (2,)
        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)

    def test_handle_nan_values(self):
        """Test that NaN values are handled correctly."""
        df = pd.DataFrame({
            'average_electronegativity': [1.5, np.nan, 1.7],
            'valence_electron_concentration': [8.5, 8.6, 8.7],
            'atomic_radii_variance': [0.1, 0.12, 0.13],
            'average_d_electrons': [5.2, 5.3, 5.4],
            'atomic_size_mismatch': [0.05, 0.06, 0.07],
            'coercivity_normalized': [100.0, 120.0, np.nan]
        })

        X, y = prepare_data(df, 'coercivity_normalized')

        # Should have dropped the row with NaN
        assert X.shape[0] == 1
        assert y.shape[0] == 1


class TestCreateModelPipeline:
    def test_linear_pipeline(self):
        """Test creation of linear regression pipeline."""
        pipeline = create_model_pipeline('linear')
        assert len(pipeline.steps) == 2
        assert pipeline.steps[0][0] == 'scaler'
        assert pipeline.steps[1][0] == 'regressor'
        assert pipeline.steps[1][1].__class__.__name__ == 'LinearRegression'

    def test_ridge_pipeline(self):
        """Test creation of Ridge regression pipeline."""
        pipeline = create_model_pipeline('ridge')
        assert pipeline.steps[1][1].__class__.__name__ == 'Ridge'

    def test_lasso_pipeline(self):
        """Test creation of Lasso regression pipeline."""
        pipeline = create_model_pipeline('lasso')
        assert pipeline.steps[1][1].__class__.__name__ == 'Lasso'

    def test_invalid_model_type(self):
        """Test that ValueError is raised for invalid model type."""
        with pytest.raises(ValueError):
            create_model_pipeline('invalid_type')


class TestEvaluateModel:
    def test_evaluate_model(self):
        """Test model evaluation returns correct metrics."""
        # Create a simple model and data
        pipeline = create_model_pipeline('linear')
        X = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0],
                      [5.0, 6.0], [6.0, 7.0], [7.0, 8.0], [8.0, 9.0],
                      [9.0, 10.0], [10.0, 11.0], [11.0, 12.0], [12.0, 13.0]])
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0])

        # Fit the model first
        pipeline.fit(X, y)

        metrics = evaluate_model(pipeline, X, y)

        assert 'cv_r2_mean' in metrics
        assert 'test_rmse' in metrics
        assert 'test_mae' in metrics
        assert 'test_r2' in metrics
        assert metrics['test_r2'] > 0.9  # Should be very high for perfect linear data


class TestRunLinearRegression:
    def test_run_full_pipeline(self):
        """Test running the full linear regression pipeline."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create input data
            input_df = pd.DataFrame({
                'average_electronegativity': [1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4],
                'valence_electron_concentration': [8.5, 8.6, 8.7, 8.8, 8.9, 9.0, 9.1, 9.2, 9.3, 9.4],
                'atomic_radii_variance': [0.1, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20],
                'average_d_electrons': [5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 6.0, 6.1],
                'atomic_size_mismatch': [0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14],
                'coercivity_normalized': [100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0]
            })

            input_path = tmp_path / "test_features.csv"
            input_df.to_csv(input_path, index=False)

            output_dir = tmp_path / "models"
            metrics_path = tmp_path / "metrics.json"

            result = run_linear_regression(
                input_path=input_path,
                output_dir=output_dir,
                metrics_path=metrics_path,
                model_type='ridge',
                cv_folds=3
            )

            assert 'model' in result
            assert 'metrics' in result
            assert 'model_path' in result
            assert 'metrics_path' in result
            assert Path(result['model_path']).exists()
            assert Path(result['metrics_path']).exists()
            assert result['metrics']['test_r2'] > 0.0

    def test_insufficient_data(self):
        """Test that error is raised for insufficient data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create insufficient data (less than 10 samples)
            input_df = pd.DataFrame({
                'average_electronegativity': [1.5, 1.6],
                'valence_electron_concentration': [8.5, 8.6],
                'atomic_radii_variance': [0.1, 0.12],
                'average_d_electrons': [5.2, 5.3],
                'atomic_size_mismatch': [0.05, 0.06],
                'coercivity_normalized': [100.0, 120.0]
            })

            input_path = tmp_path / "test_features.csv"
            input_df.to_csv(input_path, index=False)

            with pytest.raises(ValueError) as exc_info:
                run_linear_regression(input_path=input_path, model_type='ridge')

            assert "Insufficient data" in str(exc_info.value)
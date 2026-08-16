"""Tests for the modeling metrics and MAE flagging logic."""
import pytest
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from modeling import run_modeling_pipeline, save_model_metrics

class TestModelMetrics:
    """Test suite for model metrics generation and MAE flagging."""

    @pytest.fixture
    def mock_data(self, tmp_path):
        """Create mock cleaned data for testing."""
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a mock parquet file with ILR features and poisson_ratio
        mock_df = pd.DataFrame({
            'ilr_Cu': np.random.rand(100),
            'ilr_Mg': np.random.rand(100),
            'ilr_Si': np.random.rand(100),
            'ilr_Zn': np.random.rand(100),
            'ilr_Mn': np.random.rand(100),
            'poisson_ratio': np.random.rand(100) * 0.5 + 0.2  # Range ~0.2 to 0.7
        })
        
        parquet_path = data_dir / "alloys_clean.parquet"
        mock_df.to_parquet(parquet_path)
        
        return data_dir, mock_df

    @pytest.fixture
    def mock_config(self, mock_data):
        """Mock the config to point to temporary data."""
        data_dir, _ = mock_data
        with patch('modeling.config') as mock_config:
            mock_config.data_processed_dir = data_dir
            yield mock_config

    def test_mae_flagging_high_mae(self, mock_data, mock_config, tmp_path):
        """Test that mae_flag is True when cv_mae > 0.05."""
        # We need to mock the cross_val_score to return high MAE values
        with patch('modeling.cross_val_score') as mock_cv:
            # Return negative MAE values that are high (e.g., -0.1, -0.15)
            mock_cv.return_value = np.array([-0.1, -0.15, -0.12, -0.11, -0.13])
            
            with patch('modeling.train_test_split') as mock_split:
                # Mock train_test_split to return subsets of our mock data
                X_train = mock_data[1].iloc[:80].drop(columns=['poisson_ratio'])
                y_train = mock_data[1].iloc[:80]['poisson_ratio']
                X_test = mock_data[1].iloc[80:].drop(columns=['poisson_ratio'])
                y_test = mock_data[1].iloc[80:]['poisson_ratio']
                
                mock_split.return_value = (X_train, X_test, y_train, y_test)
                
                with patch('modeling.joblib.dump'):
                    with patch('modeling.os.makedirs'):
                        result = run_modeling_pipeline()
                        
                        # Check that mae_flag is True
                        assert result['metrics']['mae_flag'] is True
                        assert result['metrics']['cv_mae'] > 0.05
                        assert result['metrics']['threshold'] == 0.05

    def test_mae_flagging_low_mae(self, mock_data, mock_config, tmp_path):
        """Test that mae_flag is False when cv_mae <= 0.05."""
        with patch('modeling.cross_val_score') as mock_cv:
            # Return negative MAE values that are low (e.g., -0.02, -0.03)
            mock_cv.return_value = np.array([-0.02, -0.03, -0.025, -0.028, -0.022])
            
            with patch('modeling.train_test_split') as mock_split:
                X_train = mock_data[1].iloc[:80].drop(columns=['poisson_ratio'])
                y_train = mock_data[1].iloc[:80]['poisson_ratio']
                X_test = mock_data[1].iloc[80:].drop(columns=['poisson_ratio'])
                y_test = mock_data[1].iloc[80:]['poisson_ratio']
                
                mock_split.return_value = (X_train, X_test, y_train, y_test)
                
                with patch('modeling.joblib.dump'):
                    with patch('modeling.os.makedirs'):
                        result = run_modeling_pipeline()
                        
                        # Check that mae_flag is False
                        assert result['metrics']['mae_flag'] is False
                        assert result['metrics']['cv_mae'] <= 0.05

    def test_metrics_schema(self, mock_data, mock_config, tmp_path):
        """Test that the metrics dictionary has the correct schema."""
        with patch('modeling.cross_val_score') as mock_cv:
            mock_cv.return_value = np.array([-0.05, -0.06, -0.055, -0.052, -0.058])
            
            with patch('modeling.train_test_split') as mock_split:
                X_train = mock_data[1].iloc[:80].drop(columns=['poisson_ratio'])
                y_train = mock_data[1].iloc[:80]['poisson_ratio']
                X_test = mock_data[1].iloc[80:].drop(columns=['poisson_ratio'])
                y_test = mock_data[1].iloc[80:]['poisson_ratio']
                
                mock_split.return_value = (X_train, X_test, y_train, y_test)
                
                with patch('modeling.joblib.dump'):
                    with patch('modeling.os.makedirs'):
                        result = run_modeling_pipeline()
                        
                        metrics = result['metrics']
                        
                        # Check schema
                        assert 'cv_mae' in metrics
                        assert 'test_mae' in metrics
                        assert 'std_dev' in metrics
                        assert 'mae_flag' in metrics
                        assert 'threshold' in metrics
                        
                        # Check types
                        assert isinstance(metrics['cv_mae'], float)
                        assert isinstance(metrics['test_mae'], float)
                        assert isinstance(metrics['std_dev'], float)
                        assert isinstance(metrics['mae_flag'], bool)
                        assert isinstance(metrics['threshold'], float)

    def test_metrics_file_created(self, mock_data, mock_config, tmp_path):
        """Test that model_metrics.json is created with correct content."""
        metrics_path = tmp_path / "data" / "processed" / "model_metrics.json"
        
        with patch('modeling.cross_val_score') as mock_cv:
            mock_cv.return_value = np.array([-0.05, -0.06, -0.055, -0.052, -0.058])
            
            with patch('modeling.train_test_split') as mock_split:
                X_train = mock_data[1].iloc[:80].drop(columns=['poisson_ratio'])
                y_train = mock_data[1].iloc[:80]['poisson_ratio']
                X_test = mock_data[1].iloc[80:].drop(columns=['poisson_ratio'])
                y_test = mock_data[1].iloc[80:]['poisson_ratio']
                
                mock_split.return_value = (X_train, X_test, y_train, y_test)
                
                with patch('modeling.joblib.dump'):
                    with patch('modeling.os.makedirs'):
                        with patch('modeling.config.data_processed_dir', tmp_path / "data" / "processed"):
                            result = run_modeling_pipeline()
                            
                            # Check that the file exists
                            assert metrics_path.exists()
                            
                            # Check content
                            with open(metrics_path, 'r') as f:
                                saved_metrics = json.load(f)
                            
                            assert saved_metrics['mae_flag'] == result['metrics']['mae_flag']
                            assert saved_metrics['cv_mae'] == result['metrics']['cv_mae']
                            assert saved_metrics['threshold'] == 0.05
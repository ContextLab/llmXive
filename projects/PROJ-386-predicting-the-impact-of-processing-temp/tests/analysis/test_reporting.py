import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.reporting import (
    generate_partial_dependence_plots,
    run_reporting_pipeline,
    get_median_compositions
)
from config import get_config

class TestReportingModule:
    @pytest.fixture
    def mock_data_and_model(self, tmp_path):
        """Create mock data and model artifacts for testing."""
        # Create mock processed data
        data = {
            'Temperature': np.random.uniform(300, 600, 100),
            'Mg': np.random.uniform(0.1, 1.0, 100),
            'Si': np.random.uniform(0.1, 1.0, 100),
            'Temp_Mg': np.random.uniform(100, 300, 100),
            'Grain_Size': np.random.uniform(10, 50, 100)
        }
        df = pd.DataFrame(data)
        
        # Mock model artifact path
        mock_model_path = tmp_path / "model_artifact.json"
        mock_model_data = {
            "model_type": "RandomForestRegressor",
            "feature_names": ["Temperature", "Mg", "Si", "Temp_Mg"],
            "params": {"n_estimators": 100}
        }
        with open(mock_model_path, 'w') as f:
            json.dump(mock_model_data, f)
        
        # Mock processed data path
        mock_data_path = tmp_path / "preprocessed_data.csv"
        df.to_csv(mock_data_path, index=False)

        return df, mock_model_path, mock_data_path

    @patch('analysis.reporting.load_rf_model_artifact')
    @patch('analysis.reporting.load_processed_data')
    def test_run_reporting_pipeline(self, mock_load_data, mock_load_model, mock_data_and_model, tmp_path):
        """Test the full reporting pipeline execution."""
        df, model_path, data_path = mock_data_and_model
        
        # Mock return values
        mock_load_data.return_value = df
        mock_load_model.return_value = (MagicMock(), ["Temperature", "Mg", "Si", "Temp_Mg"])
        
        # Configure paths
        config = get_config()
        original_artifacts = config['paths']['artifacts']
        config['paths']['artifacts'] = str(tmp_path / "artifacts")
        Path(config['paths']['artifacts']).mkdir(parents=True, exist_ok=True)

        try:
            result = run_reporting_pipeline()
            
            assert result['status'] == 'completed'
            assert 'partial_dependence_temp.png' in result['plot_path']
            assert os.path.exists(result['plot_path'])
        finally:
            config['paths']['artifacts'] = original_artifacts

    @patch('analysis.reporting.load_rf_model_artifact')
    @patch('analysis.reporting.load_processed_data')
    def test_missing_model(self, mock_load_data, mock_load_model, mock_data_and_model, tmp_path):
        """Test pipeline fails gracefully when model is missing."""
        df, _, data_path = mock_data_and_model
        mock_load_data.return_value = df
        mock_load_model.return_value = (None, [])
        
        config = get_config()
        config['paths']['artifacts'] = str(tmp_path / "artifacts")
        
        with pytest.raises(RuntimeError, match="Failed to load RF model"):
            run_reporting_pipeline()

    @patch('analysis.reporting.load_rf_model_artifact')
    @patch('analysis.reporting.load_processed_data')
    def test_missing_data(self, mock_load_data, mock_load_model, mock_data_and_model, tmp_path):
        """Test pipeline fails gracefully when data is missing."""
        mock_load_data.side_effect = FileNotFoundError("Processed data not found")
        mock_load_model.return_value = (MagicMock(), ["Temperature"])
        
        config = get_config()
        config['paths']['artifacts'] = str(tmp_path / "artifacts")
        
        with pytest.raises(FileNotFoundError):
            run_reporting_pipeline()

    def test_get_median_compositions(self):
        """Test median composition calculation."""
        data = {
            'Mg': [0.1, 0.2, 0.3, 0.4, 0.5],
            'Si': [1.0, 2.0, 3.0, 4.0, 5.0],
            'Cu': [0.0, 0.1, 0.2, 0.3, 0.4]
        }
        df = pd.DataFrame(data)
        
        result = get_median_compositions(df, ['Mg', 'Si', 'Cu', 'Zn'])
        
        assert abs(result['Mg'] - 0.3) < 0.01
        assert abs(result['Si'] - 3.0) < 0.01
        assert abs(result['Cu'] - 0.2) < 0.01
        assert result['Zn'] == 0.0 # Missing element defaults to 0

    def test_generate_partial_dependence_plots_no_features(self):
        """Test PDP generation fails when no features provided."""
        model = MagicMock()
        X = pd.DataFrame({'A': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="At least one feature must be provided"):
            generate_partial_dependence_plots(model, [], X, "output.png")
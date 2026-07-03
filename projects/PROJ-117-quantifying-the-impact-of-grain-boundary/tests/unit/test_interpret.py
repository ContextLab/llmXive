"""
Unit tests for code/interpret.py
"""
import pytest
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from interpret import (
    load_training_data_and_features,
    perform_sensitivity_analysis,
    R2_THRESHOLD_JUSTIFICATION
)


class TestLoadTrainingData:
    def test_load_data_success(self, tmp_path):
        """Test loading a valid parquet file."""
        # Create dummy data
        data = {
            'misorientation': [10.0, 20.0, 30.0],
            'boundary_plane': [1, 2, 3],
            'diffusivity': [0.1, 0.2, 0.3],
            'temp': [300, 400, 500]
        }
        df = pd.DataFrame(data)
        parquet_path = tmp_path / "test.parquet"
        df.to_parquet(parquet_path)

        loaded_df, features = load_training_data_and_features(parquet_path)

        assert len(loaded_df) == 3
        assert 'misorientation' in features
        assert 'boundary_plane' in features
        assert 'diffusivity' not in features  # Target excluded
        assert 'temp' in features

    def test_load_data_missing_file(self, tmp_path):
        """Test error handling for missing file."""
        missing_path = tmp_path / "nonexistent.parquet"
        with pytest.raises(SystemExit):
            load_training_data_and_features(missing_path)


class TestSensitivityAnalysis:
    def test_sensitivity_calculation(self):
        """Test that sensitivity analysis calculates pass rates correctly."""
        # Mock model
        mock_model = MagicMock()
        
        # Mock data
        X = np.random.rand(20, 5)
        y = np.random.rand(20)
        
        thresholds = [0.1, 0.9]
        
        with patch('interpret.KFold') as mock_kf:
            # Mock the KFold iterator to return fixed indices
            mock_kf.return_value.split.return_value = [
                (np.arange(10), np.arange(10, 20)),
                (np.arange(10), np.arange(10, 20)),
                (np.arange(10), np.arange(10, 20)),
                (np.arange(10), np.arange(10, 20)),
                (np.arange(10), np.arange(10, 20))
            ]
            
            # Mock the model fit and predict to return fixed R2 scores
            # We mock the internal XGBRegressor creation and fit
            with patch('interpret.xgb.XGBRegressor') as MockXGB:
                mock_instance = MagicMock()
                MockXGB.return_value = mock_instance
                mock_instance.predict.return_value = np.random.rand(10)
                
                # Mock r2_score to return specific values for testing
                with patch('interpret.r2_score') as mock_r2:
                    # Simulate 5 folds: 4 pass 0.1, 1 pass 0.9
                    mock_r2.side_effect = [0.5, 0.5, 0.5, 0.5, 0.95]
                    
                    results = perform_sensitivity_analysis(mock_model, X, y, thresholds, Path("/tmp"))
                    
                    # Check results structure
                    assert len(results) == 2
                    assert results.iloc[0]['threshold'] == 0.1
                    assert results.iloc[0]['pass_rate'] == 1.0 # All 5 >= 0.1
                    assert results.iloc[1]['threshold'] == 0.9
                    assert results.iloc[1]['pass_rate'] == 0.2 # 1/5 >= 0.9


class TestConstants:
    def test_justification_exists(self):
        """Ensure the R2 threshold justification is not empty."""
        assert len(R2_THRESHOLD_JUSTIFICATION) > 50
        assert "0.7" in R2_THRESHOLD_JUSTIFICATION
        assert "benchmark" in R2_THRESHOLD_JUSTIFICATION.lower()

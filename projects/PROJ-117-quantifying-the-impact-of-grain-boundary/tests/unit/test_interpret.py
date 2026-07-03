"""
Unit tests for SHAP value extraction and interpretability logic in code/interpret.py.

These tests verify that the SHAP analysis functions correctly extract values,
generate summaries, and handle edge cases without requiring full model training.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# Add project root to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from interpret import generate_shap_analysis, load_model_and_data, perform_sensitivity_analysis


class MockXGBModel:
    """Mock XGBoost model for testing without full training."""
    def __init__(self):
        self.feature_names = [
            'misorientation_angle',
            'sigma_value',
            'boundary_plane_normal_h',
            'boundary_plane_normal_k',
            'boundary_plane_normal_l',
            'temperature',
            'boundary_width',
            'excess_volume',
            'simulation_method',
            'potential_id'
        ]

    def predict(self, X):
        return np.ones(X.shape[0]) * 0.85  # Mock prediction

    def get_booster(self):
        return self


@pytest.fixture
def mock_data():
    """Create mock feature data and model."""
    data = pd.DataFrame({
        'misorientation_angle': np.random.uniform(0, 60, 100),
        'sigma_value': np.random.choice([1, 3, 5, 7, 9, 11, 13, 15, 17, 19], 100),
        'boundary_plane_normal_h': np.random.randint(-5, 6, 100),
        'boundary_plane_normal_k': np.random.randint(-5, 6, 100),
        'boundary_plane_normal_l': np.random.randint(-5, 6, 100),
        'temperature': np.random.uniform(300, 1500, 100),
        'boundary_width': np.random.uniform(5, 50, 100),
        'excess_volume': np.random.uniform(0, 5, 100),
        'simulation_method': np.random.choice(['DFT', 'MD', 'KMC'], 100),
        'potential_id': np.random.choice(['EAM', 'MEAM', 'ReaxFF'], 100),
        'diffusivity': np.random.uniform(1e-12, 1e-6, 100)
    })
    
    model = MockXGBModel()
    return model, data


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_generate_shap_analysis_returns_dict(mock_data, temp_dir):
    """Test that generate_shap_analysis returns a dictionary with expected keys."""
    model, data = mock_data
    
    # Mock SHAP to avoid heavy computation
    with patch('shap.TreeExplainer') as mock_explainer_class:
        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = np.random.rand(100, len(model.feature_names))
        mock_explainer_class.return_value = mock_explainer
        
        with patch('shap.summary_plot'):
            result = generate_shap_analysis(model, data, temp_dir / "shap_output")
            
            assert isinstance(result, dict)
            assert 'shap_values' in result
            assert 'feature_importance' in result
            assert 'mean_abs_shap' in result
            assert 'feature_names' in result


def test_generate_shap_analysis_creates_files(mock_data, temp_dir):
    """Test that generate_shap_analysis creates expected output files."""
    model, data = mock_data
    
    with patch('shap.TreeExplainer') as mock_explainer_class:
        mock_explainer = MagicMock()
        mock_shap_values = np.random.rand(100, len(model.feature_names))
        mock_explainer.shap_values.return_value = mock_shap_values
        mock_explainer_class.return_value = mock_explainer
        
        with patch('shap.summary_plot') as mock_summary_plot:
            result = generate_shap_analysis(model, data, temp_dir)
            
            # Check that summary plot was called
            assert mock_summary_plot.called
            
            # Check that result contains expected data
            assert result['shap_values'].shape == (100, len(model.feature_names))
            assert len(result['feature_importance']) == len(model.feature_names)
            assert len(result['mean_abs_shap']) == len(model.feature_names)


def test_generate_shap_analysis_handles_empty_data():
    """Test that generate_shap_analysis handles empty datasets gracefully."""
    model = MockXGBModel()
    empty_data = pd.DataFrame(columns=model.feature_names)
    
    with patch('shap.TreeExplainer') as mock_explainer_class:
        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = np.array([]).reshape(0, len(model.feature_names))
        mock_explainer_class.return_value = mock_explainer
        
        with patch('shap.summary_plot'):
            with pytest.raises(ValueError, match="No data provided"):
                generate_shap_analysis(model, empty_data, tempfile.mkdtemp())


def test_generate_shap_analysis_calculates_correct_importance(mock_data, temp_dir):
    """Test that SHAP-based feature importance is calculated correctly."""
    model, data = mock_data
    
    # Create mock SHAP values with known pattern
    shap_values = np.random.rand(100, len(model.feature_names))
    shap_values[:, 0] = 10.0  # Make first feature have high impact
    
    with patch('shap.TreeExplainer') as mock_explainer_class:
        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = shap_values
        mock_explainer_class.return_value = mock_explainer
        
        with patch('shap.summary_plot'):
            result = generate_shap_analysis(model, data, temp_dir)
            
            # First feature should have highest mean absolute SHAP value
            assert result['mean_abs_shap'][0] > result['mean_abs_shap'][1]
            
            # Feature importance should be sorted by mean absolute SHAP
            assert result['feature_importance'][0]['rank'] == 1


def test_load_model_and_data_raises_on_missing_files(temp_dir):
    """Test that load_model_and_data raises appropriate errors for missing files."""
    with pytest.raises(FileNotFoundError):
        load_model_and_data(
            model_path=temp_dir / "nonexistent_model.json",
            data_path=temp_dir / "nonexistent_data.parquet"
        )


def test_perform_sensitivity_analysis_returns_expected_structure(mock_data, temp_dir):
    """Test that perform_sensitivity_analysis returns expected structure."""
    model, data = mock_data
    
    # Mock the model evaluation to return fixed metrics
    with patch('xgboost.XGBRegressor') as mock_xgb:
        mock_xgb_instance = MagicMock()
        mock_xgb_instance.score.return_value = 0.85
        mock_xgb.return_value = mock_xgb_instance
        
        thresholds = [0.5, 0.6, 0.7, 0.8]
        result = perform_sensitivity_analysis(model, data, thresholds, temp_dir)
        
        assert isinstance(result, list)
        assert len(result) == len(thresholds)
        
        for item in result:
            assert 'threshold' in item
            assert 'pass_rate' in item
            assert 'num_pass' in item
            assert 'num_total' in item


def test_perform_sensitivity_analysis_handles_thresholds_correctly(mock_data, temp_dir):
    """Test that sensitivity analysis correctly handles different R2 thresholds."""
    model, data = mock_data
    
    with patch('xgboost.XGBRegressor') as mock_xgb:
        mock_xgb_instance = MagicMock()
        # Simulate R2 scores that are above some thresholds and below others
        mock_xgb_instance.score.side_effect = [0.75, 0.75, 0.75, 0.75]
        mock_xgb.return_value = mock_xgb_instance
        
        thresholds = [0.5, 0.7, 0.8, 0.9]
        result = perform_sensitivity_analysis(model, data, thresholds, temp_dir)
        
        # Thresholds 0.5 and 0.7 should pass, 0.8 and 0.9 should fail
        assert result[0]['pass_rate'] == 1.0  # 0.5 threshold
        assert result[1]['pass_rate'] == 1.0  # 0.7 threshold
        assert result[2]['pass_rate'] == 0.0  # 0.8 threshold
        assert result[3]['pass_rate'] == 0.0  # 0.9 threshold


def test_perform_sensitivity_analysis_creates_csv_file(mock_data, temp_dir):
    """Test that perform_sensitivity_analysis creates the expected CSV file."""
    model, data = mock_data
    
    with patch('xgboost.XGBRegressor') as mock_xgb:
        mock_xgb_instance = MagicMock()
        mock_xgb_instance.score.return_value = 0.85
        mock_xgb.return_value = mock_xgb_instance
        
        thresholds = [0.5, 0.7, 0.9]
        perform_sensitivity_analysis(model, data, thresholds, temp_dir)
        
        csv_path = temp_dir / "threshold-variation-table.csv"
        assert csv_path.exists()
        
        # Verify CSV content
        df = pd.read_csv(csv_path)
        assert 'threshold' in df.columns
        assert 'pass_rate' in df.columns
        assert len(df) == len(thresholds)


def test_shap_explainer_initialization(mock_data, temp_dir):
    """Test that SHAP TreeExplainer is initialized correctly."""
    model, data = mock_data
    
    with patch('shap.TreeExplainer') as mock_explainer_class:
        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = np.random.rand(100, len(model.feature_names))
        mock_explainer_class.return_value = mock_explainer
        
        with patch('shap.summary_plot'):
            generate_shap_analysis(model, data, temp_dir)
            
            # Verify TreeExplainer was called with correct model
            mock_explainer_class.assert_called_once_with(model)


def test_feature_names_match_model(mock_data, temp_dir):
    """Test that extracted feature names match model's feature names."""
    model, data = mock_data
    
    with patch('shap.TreeExplainer') as mock_explainer_class:
        mock_explainer = MagicMock()
        mock_explainer.shap_values.return_value = np.random.rand(100, len(model.feature_names))
        mock_explainer_class.return_value = mock_explainer
        
        with patch('shap.summary_plot'):
            result = generate_shap_analysis(model, data, temp_dir)
            
            assert result['feature_names'] == model.feature_names
            assert len(result['feature_names']) == len(model.feature_names)
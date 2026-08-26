"""
Unit tests for T032: save_results module.

Tests the logic of assembling final metrics and validating against schema.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.save_results import (
    validate_output_against_schema,
    assemble_final_metrics,
    write_output_json
)
from config import CONFIG

class TestValidateOutputAgainstSchema:
    def test_validate_with_all_required_fields(self):
        """Test validation passes when all required fields are present."""
        schema = {
            "required_fields": ["r2_baseline", "mae_baseline", "r2_dft", "mae_dft", "p_value_ttest"]
        }
        output_data = {
            "r2_baseline": 0.5,
            "mae_baseline": 10.0,
            "r2_dft": 0.7,
            "mae_dft": 8.0,
            "p_value_ttest": 0.03
        }
        
        result = validate_output_against_schema(output_data, schema)
        assert result is True

    def test_validate_missing_fields(self):
        """Test validation fails when required fields are missing."""
        schema = {
            "required_fields": ["r2_baseline", "mae_baseline", "r2_dft", "mae_dft", "p_value_ttest"]
        }
        output_data = {
            "r2_baseline": 0.5,
            "mae_baseline": 10.0
            # Missing r2_dft, mae_dft, p_value_ttest
        }
        
        result = validate_output_against_schema(output_data, schema)
        assert result is False

    def test_validate_none_critical_field(self):
        """Test validation fails when critical field is None."""
        schema = {
            "required_fields": ["r2_baseline", "mae_baseline", "r2_dft", "mae_dft", "p_value_ttest"]
        }
        output_data = {
            "r2_baseline": None,
            "mae_baseline": 10.0,
            "r2_dft": 0.7,
            "mae_dft": 8.0,
            "p_value_ttest": 0.03
        }
        
        result = validate_output_against_schema(output_data, schema)
        assert result is False

class TestWriteOutputJson:
    def test_write_output_json_creates_file(self):
        """Test that write_output_json creates the file correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            test_data = {
                "r2_baseline": 0.5,
                "mae_baseline": 10.0,
                "test_field": "value"
            }
            
            write_output_json(test_data, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == test_data

    def test_write_output_json_creates_parent_dirs(self):
        """Test that write_output_json creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "subsubdir" / "test_output.json"
            test_data = {"key": "value"}
            
            write_output_json(test_data, output_path)
            
            assert output_path.exists()

class TestAssembleFinalMetrics:
    @patch('modeling.save_results.load_cv_results')
    @patch('modeling.save_results.load_models')
    @patch('modeling.save_results.calculate_metrics')
    @patch('modeling.save_results.perform_paired_ttest')
    @patch('modeling.save_results.calculate_statistical_power')
    @patch('modeling.save_results.calculate_shear_yield_correlation')
    @patch('modeling.save_results.pd.read_csv')
    def test_assemble_final_metrics_success(
        self, mock_read_csv, mock_corr, mock_power, mock_ttest, mock_calc_metrics,
        mock_load_models, mock_load_cv_results
    ):
        """Test successful assembly of final metrics."""
        # Mock data
        mock_cv_results = {
            'timestamp': '2024-01-01',
            'model_config': {'n_estimators': 100, 'max_depth': None, 'random_state': 42}
        }
        mock_load_cv_results.return_value = mock_cv_results
        mock_load_models.return_value = {}
        
        mock_metrics = {
            'r2_baseline': 0.5,
            'mae_baseline': 10.0,
            'r2_dft': 0.7,
            'mae_dft': 8.0
        }
        mock_calc_metrics.return_value = mock_metrics
        
        mock_ttest_result = {'p_value': 0.03}
        mock_ttest.return_value = mock_ttest_result
        
        mock_power_value = 0.85
        mock_power.return_value = mock_power_value
        
        mock_corr_result = {'pearson_r': 0.65}
        mock_corr.return_value = mock_corr_result
        
        mock_df = pd.DataFrame({'yield_strength_MPa': [100, 200], 'shear_modulus_GPa': [50, 80]})
        mock_read_csv.return_value = mock_df
        
        # Call function
        result = assemble_final_metrics()
        
        # Verify results
        assert result['r2_baseline'] == 0.5
        assert result['mae_baseline'] == 10.0
        assert result['r2_dft'] == 0.7
        assert result['mae_dft'] == 8.0
        assert result['p_value_ttest'] == 0.03
        assert result['statistical_power'] == 0.85
        assert result['pearson_correlation'] == 0.65
        assert result['dataset_rows'] == 2
        assert result['model_config']['n_estimators'] == 100

    @patch('modeling.save_results.pd.read_csv')
    def test_assemble_final_metrics_missing_cv_results(self, mock_read_csv):
        """Test that assemble_final_metrics raises FileNotFoundError if CV results missing."""
        with patch('modeling.save_results.load_cv_results') as mock_load_cv:
            mock_load_cv.side_effect = FileNotFoundError("CV results not found")
            
            with pytest.raises(FileNotFoundError):
                assemble_final_metrics()

    @patch('modeling.save_results.pd.read_csv')
    def test_assemble_final_metrics_missing_merged_data(self, mock_read_csv):
        """Test that assemble_final_metrics raises FileNotFoundError if merged data missing."""
        mock_read_csv.side_effect = FileNotFoundError("Merged dataset not found")
        
        with patch('modeling.save_results.load_cv_results') as mock_load_cv:
            mock_load_cv.return_value = {'timestamp': '2024-01-01', 'model_config': {}}
            
            with patch('modeling.save_results.calculate_metrics') as mock_calc_metrics:
                mock_calc_metrics.return_value = {}
                
                with patch('modeling.save_results.perform_paired_ttest') as mock_ttest:
                    mock_ttest.return_value = {'p_value': 0.05}
                    
                    with patch('modeling.save_results.calculate_statistical_power') as mock_power:
                        mock_power.return_value = 0.8
                        
                        with patch('modeling.save_results.calculate_shear_yield_correlation') as mock_corr:
                            mock_corr.return_value = {'pearson_r': 0.5}
                            
                            with pytest.raises(FileNotFoundError):
                                assemble_final_metrics()
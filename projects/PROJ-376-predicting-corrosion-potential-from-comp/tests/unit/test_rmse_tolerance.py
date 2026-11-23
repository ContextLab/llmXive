"""
Unit tests for the RMSE Tolerance Comparator (T023b).

These tests verify:
1. RMSE conversion logic (V -> mV, mV -> mV).
2. Comparison logic (within vs exceeds tolerance).
3. Handling of missing data (simulated via mocks).
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from models.rmse_tolerance_comparator import (
    convert_rmse_to_mv,
    compare_rmse_against_tolerance,
    load_model_results,
    main
)
from utils.exceptions import CorrosionPipelineError


class TestConvertRmseToMv:
    def test_convert_volts_to_mv(self):
        """Test conversion from Volts to millivolts."""
        assert convert_rmse_to_mv(0.001, 'V') == 1.0
        assert convert_rmse_to_mv(1.0, 'V') == 1000.0
        assert convert_rmse_to_mv(0.0, 'V') == 0.0
    
    def test_convert_mv_to_mv(self):
        """Test that mV input remains unchanged."""
        assert convert_rmse_to_mv(50.0, 'mV') == 50.0
        assert convert_rmse_to_mv(100.5, 'mV') == 100.5
    
    def test_convert_case_insensitive(self):
        """Test that unit conversion is case-insensitive."""
        assert convert_rmse_to_mv(0.1, 'v') == 100.0
        assert convert_rmse_to_mv(0.1, 'V') == 100.0
    
    def test_invalid_unit_raises_error(self):
        """Test that an unrecognized unit raises CorrosionPipelineError."""
        with pytest.raises(CorrosionPipelineError):
            convert_rmse_to_mv(10.0, 'kV')

class TestCompareRmseAgainstTolerance:
    def test_within_tolerance(self):
        """Test when RMSE is less than or equal to tolerance."""
        result = compare_rmse_against_tolerance(10.0, 20.0, "Test Source")
        assert result['is_within_tolerance'] is True
        assert result['status'] == 'PASS'
    
    def test_exceeds_tolerance(self):
        """Test when RMSE is greater than tolerance."""
        result = compare_rmse_against_tolerance(25.0, 20.0, "Test Source")
        assert result['is_within_tolerance'] is False
        assert result['status'] == 'FAIL'
    
    def test_exact_match(self):
        """Test when RMSE equals tolerance exactly."""
        result = compare_rmse_against_tolerance(20.0, 20.0, "Test Source")
        assert result['is_within_tolerance'] is True
        assert result['status'] == 'PASS'

class TestLoadModelResults:
    @patch('models.rmse_tolerance_comparator.get_model_results_path')
    def test_file_not_found(self, mock_path):
        """Test error when results file is missing."""
        mock_path.return_value = Path("/nonexistent/path/results.json")
        with pytest.raises(CorrosionPipelineError):
            load_model_results()
    
    @patch('models.rmse_tolerance_comparator.get_model_results_path')
    @patch('builtins.open', new_callable=MagicMock)
    def test_missing_metrics_key(self, mock_open, mock_path):
        """Test error when 'metrics' key is missing."""
        mock_path.return_value = Path("/tmp/results.json")
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({"other_key": 1})
        mock_open.return_value.__enter__.return_value.__iter__ = lambda self: iter([json.dumps({"other_key": 1})])
        
        # Simulate json.load returning the dict
        with patch('json.load', return_value={"other_key": 1}):
            with pytest.raises(CorrosionPipelineError):
                load_model_results()

class TestMainIntegration:
    @patch('models.rmse_tolerance_comparator.get_model_results_path')
    @patch('models.rmse_tolerance_comparator.load_astm_tolerance_config')
    @patch('models.rmse_tolerance_comparator.get_tolerance_value')
    @patch('models.rmse_tolerance_comparator.get_logger')
    def test_main_success_path(self, mock_logger, mock_get_tol, mock_load_config, mock_get_path):
        """Test main function with valid data."""
        # Setup mocks
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path
        
        # Mock file content
        mock_file = MagicMock()
        mock_file.__enter__ = lambda s: s
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.read.return_value = json.dumps({
            "metrics": {
                "rmse": 0.005,
                "rmse_unit": "V"
            }
        })
        
        with patch('builtins.open', return_value=mock_file):
            with patch('json.load', return_value={
                "metrics": {
                    "rmse": 0.005,
                    "rmse_unit": "V"
                }
            }):
                mock_load_config.return_value = {
                    "tolerance_mV": 100.0,
                    "source": "ASTM G59",
                    "used_default": False
                }
                mock_get_tol.return_value = 100.0
                
                # Run main
                result = main()
                
                # Verify result
                assert result['is_within_tolerance'] is True
                assert result['status'] == 'PASS'
                assert result['rmse_mV'] == 5.0  # 0.005 V * 1000
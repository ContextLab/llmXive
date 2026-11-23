"""
Unit tests for T023b: RMSE Tolerance Comparator.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from models.rmse_tolerance_comparator import (
    load_model_results,
    convert_rmse_to_mv,
    compare_rmse_against_tolerance,
    main
)
from utils.exceptions import DataInsufficientError


class TestConvertRmseToMv:
    """Tests for the unit conversion function."""

    def test_convert_volts_to_mv(self):
        """Test basic conversion from Volts to mV."""
        assert convert_rmse_to_mv(1.0) == 1000.0
        assert convert_rmse_to_mv(0.001) == 1.0
        assert convert_rmse_to_mv(0.0005) == 0.5

    def test_convert_zero(self):
        """Test conversion of zero."""
        assert convert_rmse_to_mv(0.0) == 0.0


class TestCompareRmseAgainstTolerance:
    """Tests for the comparison logic."""

    def test_within_tolerance(self):
        """Test case where RMSE is within tolerance."""
        result = compare_rmse_against_tolerance(10.0, 20.0, "TestModel")
        assert result["is_within_tolerance"] is True
        assert result["status"] == "PASS"
        assert result["difference_mv"] == -10.0

    def test_exceeds_tolerance(self):
        """Test case where RMSE exceeds tolerance."""
        result = compare_rmse_against_tolerance(25.0, 20.0, "TestModel")
        assert result["is_within_tolerance"] is False
        assert result["status"] == "FAIL"
        assert result["difference_mv"] == 5.0

    def test_exact_tolerance(self):
        """Test case where RMSE equals tolerance exactly."""
        result = compare_rmse_against_tolerance(20.0, 20.0, "TestModel")
        assert result["is_within_tolerance"] is True
        assert result["status"] == "PASS"
        assert result["difference_mv"] == 0.0


class TestLoadModelResults:
    """Tests for loading model results."""

    def test_load_valid_json(self):
        """Test loading a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"models": {"RF": {"rmse_volts": 0.01}}}, f)
            f.flush()
            path = Path(f.name)

        try:
            data = load_model_results(path)
            assert "models" in data
            assert "RF" in data["models"]
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_model_results(Path("/nonexistent/path/file.json"))

    def test_invalid_json(self):
        """Test that JSONDecodeError is raised for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            f.flush()
            path = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                load_model_results(path)
        finally:
            os.unlink(path)


class TestMainIntegration:
    """Integration tests for the main function."""

    @patch('models.rmse_tolerance_comparator.load_astm_tolerance_config')
    @patch('models.rmse_tolerance_comparator.get_tolerance_value')
    @patch('models.rmse_tolerance_comparator.load_model_results')
    def test_main_success(self, mock_load_results, mock_get_tol, mock_load_config):
        """Test main function executes successfully."""
        # Setup mocks
        mock_load_results.return_value = {"models": {"RF": {"rmse_volts": 0.01}}}
        mock_load_config.return_value = {"tolerance": 0.02, "source": "ASTM"}
        mock_get_tol.return_value = 20.0  # 20 mV

        # Run main
        with patch('sys.stdout'):
            result = main()

        assert result is not None
        assert "comparisons" in result
        assert len(result["comparisons"]) == 1

    @patch('models.rmse_tolerance_comparator.load_astm_tolerance_config')
    def test_main_missing_tolerance(self, mock_load_config):
        """Test that main raises DataInsufficientError if tolerance is missing."""
        mock_load_config.side_effect = DataInsufficientError("Tolerance not defined")

        with patch('models.rmse_tolerance_comparator.load_model_results') as mock_load_results:
            mock_load_results.return_value = {"models": {"RF": {"rmse_volts": 0.01}}}

            with pytest.raises(DataInsufficientError):
                main()
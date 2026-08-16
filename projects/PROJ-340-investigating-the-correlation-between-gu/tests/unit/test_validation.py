"""
Unit tests for validation logic in code/ingest.py.

This module tests the variable validation logic defined in T021 and T022.
It verifies that:
1. The correct variables are detected as present/missing.
2. The validation metrics are calculated correctly.
3. The failure report is generated with the correct schema on failure.
4. The system halts execution as expected on missing variables.
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingest import validate_variables, load_required_variables, RealDataFetchError
from ingest import load_data, save_outlier_report, filter_outliers, save_filtered_data

# Mock the required variables config content
MOCK_REQUIRED_PREDICTORS = ["taxon_A", "taxon_B", "taxon_C"]
MOCK_REQUIRED_OUTCOMES = ["REM_duration", "SWS_duration"]
MOCK_REQUIRED_VARIABLES = MOCK_REQUIRED_PREDICTORS + MOCK_REQUIRED_OUTCOMES

class TestValidateVariables:
    """Tests for the validate_variables function."""

    def test_validate_all_present(self, tmp_path):
        """Test validation when all required variables are present."""
        # Setup config file
        config_file = tmp_path / "required_variables.yaml"
        config_content = f"""
        required_predictors:
          - taxon_A
          - taxon_B
          - taxon_C
        required_outcomes:
          - REM_duration
          - SWS_duration
        """
        config_file.write_text(config_content)

        # Create mock data with all variables
        data_file = tmp_path / "mock_data.csv"
        data = {
            "taxon_A": [1.0, 2.0, 3.0],
            "taxon_B": [4.0, 5.0, 6.0],
            "taxon_C": [7.0, 8.0, 9.0],
            "REM_duration": [10.0, 20.0, 30.0],
            "SWS_duration": [40.0, 50.0, 60.0]
        }
        pd.DataFrame(data).to_csv(data_file, index=False)

        # Run validation
        with patch('code.ingest.load_required_variables', return_value=(MOCK_REQUIRED_PREDICTORS, MOCK_REQUIRED_OUTCOMES)):
            result = validate_variables(data_file, str(config_file))

        assert result["status"] == "PASS"
        assert result["percentage_loaded"] == 100.0
        assert len(result["missing_variables"]) == 0
        assert result["total_required"] == 5

    def test_validate_missing_outcome(self, tmp_path):
        """Test validation when an outcome variable is missing."""
        # Setup config file
        config_file = tmp_path / "required_variables.yaml"
        config_content = f"""
        required_predictors:
          - taxon_A
          - taxon_B
          - taxon_C
        required_outcomes:
          - REM_duration
          - SWS_duration
        """
        config_file.write_text(config_content)

        # Create mock data missing SWS_duration
        data_file = tmp_path / "mock_data.csv"
        data = {
            "taxon_A": [1.0, 2.0, 3.0],
            "taxon_B": [4.0, 5.0, 6.0],
            "taxon_C": [7.0, 8.0, 9.0],
            "REM_duration": [10.0, 20.0, 30.0]
            # SWS_duration is missing
        }
        pd.DataFrame(data).to_csv(data_file, index=False)

        # Run validation
        with patch('code.ingest.load_required_variables', return_value=(MOCK_REQUIRED_PREDICTORS, MOCK_REQUIRED_OUTCOMES)):
            result = validate_variables(data_file, str(config_file))

        assert result["status"] == "FAIL"
        assert result["percentage_loaded"] == 80.0  # 4/5
        assert "SWS_duration" in result["missing_variables"]
        assert result["total_required"] == 5

    def test_validate_missing_predictor(self, tmp_path):
        """Test validation when a predictor variable is missing."""
        # Setup config file
        config_file = tmp_path / "required_variables.yaml"
        config_content = f"""
        required_predictors:
          - taxon_A
          - taxon_B
          - taxon_C
        required_outcomes:
          - REM_duration
          - SWS_duration
        """
        config_file.write_text(config_content)

        # Create mock data missing taxon_B
        data_file = tmp_path / "mock_data.csv"
        data = {
            "taxon_A": [1.0, 2.0, 3.0],
            # taxon_B is missing
            "taxon_C": [7.0, 8.0, 9.0],
            "REM_duration": [10.0, 20.0, 30.0],
            "SWS_duration": [40.0, 50.0, 60.0]
        }
        pd.DataFrame(data).to_csv(data_file, index=False)

        # Run validation
        with patch('code.ingest.load_required_variables', return_value=(MOCK_REQUIRED_PREDICTORS, MOCK_REQUIRED_OUTCOMES)):
            result = validate_variables(data_file, str(config_file))

        assert result["status"] == "FAIL"
        assert result["percentage_loaded"] == 80.0  # 4/5
        assert "taxon_B" in result["missing_variables"]
        assert result["total_required"] == 5

    def test_validate_all_missing(self, tmp_path):
        """Test validation when all required variables are missing."""
        # Setup config file
        config_file = tmp_path / "required_variables.yaml"
        config_content = f"""
        required_predictors:
          - taxon_A
          - taxon_B
          - taxon_C
        required_outcomes:
          - REM_duration
          - SWS_duration
        """
        config_file.write_text(config_content)

        # Create mock data with no required variables
        data_file = tmp_path / "mock_data.csv"
        data = {
            "other_var": [1.0, 2.0, 3.0],
            "another_var": [4.0, 5.0, 6.0]
        }
        pd.DataFrame(data).to_csv(data_file, index=False)

        # Run validation
        with patch('code.ingest.load_required_variables', return_value=(MOCK_REQUIRED_PREDICTORS, MOCK_REQUIRED_OUTCOMES)):
            result = validate_variables(data_file, str(config_file))

        assert result["status"] == "FAIL"
        assert result["percentage_loaded"] == 0.0
        assert len(result["missing_variables"]) == 5
        assert result["total_required"] == 5

    def test_metrics_persistence(self, tmp_path):
        """Test that validation metrics are written to disk."""
        # Setup config file
        config_file = tmp_path / "required_variables.yaml"
        config_content = f"""
        required_predictors:
          - taxon_A
          - taxon_B
          - taxon_C
        required_outcomes:
          - REM_duration
          - SWS_duration
        """
        config_file.write_text(config_content)

        # Create mock data with missing variable
        data_file = tmp_path / "mock_data.csv"
        data = {
            "taxon_A": [1.0, 2.0, 3.0],
            "taxon_B": [4.0, 5.0, 6.0],
            "taxon_C": [7.0, 8.0, 9.0],
            "REM_duration": [10.0, 20.0, 30.0]
            # SWS_duration is missing
        }
        pd.DataFrame(data).to_csv(data_file, index=False)

        # Setup results directory
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # Run validation
        with patch('code.ingest.load_required_variables', return_value=(MOCK_REQUIRED_PREDICTORS, MOCK_REQUIRED_OUTCOMES)):
            result = validate_variables(data_file, str(config_file), results_dir=str(results_dir))

        # Check that metrics file was written
        metrics_file = results_dir / "variable_load_metrics.json"
        assert metrics_file.exists()
        
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        assert metrics["status"] == "FAIL"
        assert "SWS_duration" in metrics["missing_variables"]

class TestLoadDataFailureHandling:
    """Tests for the load_data function failure handling (T022)."""

    def test_load_data_halts_on_missing_variable(self, tmp_path):
        """Test that load_data halts execution when variables are missing."""
        # Setup config file
        config_file = tmp_path / "required_variables.yaml"
        config_content = f"""
        required_predictors:
          - taxon_A
          - taxon_B
          - taxon_C
        required_outcomes:
          - REM_duration
          - SWS_duration
        """
        config_file.write_text(config_content)

        # Create mock data missing SWS_duration
        data_file = tmp_path / "mock_data.csv"
        data = {
            "taxon_A": [1.0, 2.0, 3.0],
            "taxon_B": [4.0, 5.0, 6.0],
            "taxon_C": [7.0, 8.0, 9.0],
            "REM_duration": [10.0, 20.0, 30.0]
        }
        pd.DataFrame(data).to_csv(data_file, index=False)

        # Setup directories
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # Mock sys.exit to capture the exit code
        with patch('code.ingest.load_required_variables', return_value=(MOCK_REQUIRED_PREDICTORS, MOCK_REQUIRED_OUTCOMES)):
            with patch('sys.exit') as mock_exit:
                try:
                    load_data(data_file, str(config_file), results_dir=str(results_dir))
                except SystemExit:
                    pass  # Expected

        # Verify sys.exit was called with code 1
        mock_exit.assert_called_once_with(1)

        # Verify failure report was written
        failure_report_file = results_dir / "validation_failure_report.json"
        assert failure_report_file.exists()
        
        with open(failure_report_file, 'r') as f:
            report = json.load(f)
        
        assert report["status"] == "FAIL"
        assert report["error_code"] == "MISSING_VARIABLES"
        assert "SWS_duration" in report["missing_variables"]
        assert "timestamp" in report
        assert "message" in report

    def test_load_data_proceeds_on_pass(self, tmp_path):
        """Test that load_data proceeds normally when all variables are present."""
        # Setup config file
        config_file = tmp_path / "required_variables.yaml"
        config_content = f"""
        required_predictors:
          - taxon_A
          - taxon_B
          - taxon_C
        required_outcomes:
          - REM_duration
          - SWS_duration
        """
        config_file.write_text(config_content)

        # Create mock data with all variables
        data_file = tmp_path / "mock_data.csv"
        data = {
            "taxon_A": [1.0, 2.0, 3.0],
            "taxon_B": [4.0, 5.0, 6.0],
            "taxon_C": [7.0, 8.0, 9.0],
            "REM_duration": [10.0, 20.0, 30.0],
            "SWS_duration": [40.0, 50.0, 60.0]
        }
        pd.DataFrame(data).to_csv(data_file, index=False)

        # Setup directories
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # Mock sys.exit to ensure it's not called
        with patch('code.ingest.load_required_variables', return_value=(MOCK_REQUIRED_PREDICTORS, MOCK_REQUIRED_OUTCOMES)):
            with patch('sys.exit') as mock_exit:
                try:
                    result = load_data(data_file, str(config_file), results_dir=str(results_dir))
                except SystemExit:
                    pytest.fail("load_data should not exit on valid data")

        # Verify sys.exit was not called
        mock_exit.assert_not_called()
        
        # Verify result is not None
        assert result is not None

class TestLoadRequiredVariables:
    """Tests for the load_required_variables function."""

    def test_load_variables_from_yaml(self, tmp_path):
        """Test loading variables from a valid YAML config file."""
        config_file = tmp_path / "required_variables.yaml"
        config_content = f"""
        required_predictors:
          - taxon_A
          - taxon_B
          - taxon_C
        required_outcomes:
          - REM_duration
          - SWS_duration
        """
        config_file.write_text(config_content)

        predictors, outcomes = load_required_variables(str(config_file))

        assert set(predictors) == set(MOCK_REQUIRED_PREDICTORS)
        assert set(outcomes) == set(MOCK_REQUIRED_OUTCOMES)

    def test_load_variables_missing_file(self, tmp_path):
        """Test that load_required_variables raises an error for missing file."""
        with pytest.raises(FileNotFoundError):
            load_required_variables(str(tmp_path / "nonexistent.yaml"))

    def test_load_variables_empty_list(self, tmp_path):
        """Test loading variables from an empty config."""
        config_file = tmp_path / "empty.yaml"
        config_content = """
        required_predictors: []
        required_outcomes: []
        """
        config_file.write_text(config_content)

        predictors, outcomes = load_required_variables(str(config_file))

        assert len(predictors) == 0
        assert len(outcomes) == 0
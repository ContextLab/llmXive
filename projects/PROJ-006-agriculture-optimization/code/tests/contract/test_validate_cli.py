"""
Contract tests for the CLI validation tool (src/cli/validate.py).
Validates that the CLI correctly enforces schema contracts on ingestion and output artifacts.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import yaml

from src.cli.validate import main as validate_main, validate_csv_artifact, validate_json_artifact
from src.config.schemas import AnalysisDatasetRecord, RegressionOutput


class TestCSVValidation:
    """Tests for CSV dataset validation."""

    @pytest.fixture
    def valid_csv_path(self, tmp_path):
        """Create a valid CSV file matching the dataset schema."""
        data = {
            "household_id": [1, 2, 3],
            "latitude": [-12.5, -12.6, -12.7],
            "longitude": [34.2, 34.3, 34.4],
            "land_size": [1.5, 2.0, 0.8],
            "education_level": [4, 5, 3],
            "finance_access": [True, False, True],
            "practice_mixed_farming": [True, True, False],
            "practice_terracing": [False, True, True],
            "practice_conservation_tillage": [True, False, True],
            "practice_agroforestry": [False, True, True],
            "extension_visits": [2, 3, 1],
            "hlias": [10, 15, 8],
            "CSA_Index": [2.0, 3.0, 2.0],
            "Stability_Score": [0.85, 0.92, 0.78],
            "HFIAS": [5.0, 8.0, 4.0],
            "village_id": ["-12_34", "-12_34", "-12_34"]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "valid_dataset.csv"
        df.to_csv(file_path, index=False)
        return file_path

    @pytest.fixture
    def invalid_csv_path(self, tmp_path):
        """Create an invalid CSV file (missing required column)."""
        data = {
            "household_id": [1, 2],
            "latitude": [-12.5, -12.6],
            # Missing 'longitude' and other required columns
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "invalid_dataset.csv"
        df.to_csv(file_path, index=False)
        return file_path

    def test_valid_csv_passes(self, valid_csv_path):
        """Test that a valid CSV passes validation."""
        result = validate_csv_artifact(valid_csv_path, "dataset", log_level="ERROR")
        assert result is True

    def test_invalid_csv_fails(self, invalid_csv_path):
        """Test that an invalid CSV fails validation."""
        result = validate_csv_artifact(invalid_csv_path, "dataset", log_level="ERROR")
        assert result is False

    def test_missing_file_fails(self, tmp_path):
        """Test that a missing file fails validation."""
        missing_path = tmp_path / "nonexistent.csv"
        result = validate_csv_artifact(missing_path, "dataset", log_level="ERROR")
        assert result is False


class TestJSONValidation:
    """Tests for JSON output validation."""

    @pytest.fixture
    def valid_regression_json_path(self, tmp_path):
        """Create a valid regression results JSON file."""
        data = {
            "coefficients": {
                "CSA_Index": 0.45,
                "Access_to_Finance": 0.12,
                "land_size": 0.08
            },
            "p_values": {
                "CSA_Index": 0.001,
                "Access_to_Finance": 0.045,
                "land_size": 0.12
            },
            "vif_scores": {
                "CSA_Index": 1.2,
                "Access_to_Finance": 1.5,
                "land_size": 1.1
            },
            "model_type": "aggregated",
            "collinearity_warning": False,
            "adjusted_alpha": 0.0167,
            "bonferroni_corrected_p_values": {
                "CSA_Index": 0.003,
                "Access_to_Finance": 0.135,
                "land_size": 0.36
            }
        }
        file_path = tmp_path / "regression_results.json"
        with open(file_path, "w") as f:
            json.dump(data, f)
        return file_path

    @pytest.fixture
    def invalid_regression_json_path(self, tmp_path):
        """Create an invalid regression results JSON file (missing required key)."""
        data = {
            "coefficients": {"CSA_Index": 0.45},
            # Missing 'p_values', 'vif_scores', etc.
        }
        file_path = tmp_path / "invalid_regression.json"
        with open(file_path, "w") as f:
            json.dump(data, f)
        return file_path

    def test_valid_regression_json_passes(self, valid_regression_json_path):
        """Test that valid regression JSON passes validation."""
        result = validate_json_artifact(valid_regression_json_path, "regression", log_level="ERROR")
        assert result is True

    def test_invalid_regression_json_fails(self, invalid_regression_json_path):
        """Test that invalid regression JSON fails validation."""
        result = validate_json_artifact(invalid_regression_json_path, "regression", log_level="ERROR")
        assert result is False

    def test_missing_file_fails(self, tmp_path):
        """Test that a missing JSON file fails validation."""
        missing_path = tmp_path / "nonexistent.json"
        result = validate_json_artifact(missing_path, "regression", log_level="ERROR")
        assert result is False


class TestIntegration:
    """Integration tests for the validate.py CLI entry point."""

    def test_cli_validates_csv_success(self, valid_csv_path, capsys):
        """Test CLI invocation with a valid CSV."""
        # Note: We need to patch sys.argv to simulate CLI args
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["validate.py", str(valid_csv_path), "--schema-type", "dataset"]
            exit_code = validate_main()
            assert exit_code == 0
        finally:
            sys.argv = original_argv

    def test_cli_validates_json_success(self, valid_regression_json_path, capsys):
        """Test CLI invocation with a valid JSON."""
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["validate.py", str(valid_regression_json_path), "--schema-type", "regression"]
            exit_code = validate_main()
            assert exit_code == 0
        finally:
            sys.argv = original_argv

    def test_cli_fails_with_missing_args(self, valid_csv_path, capsys):
        """Test CLI invocation without required --schema-type argument."""
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["validate.py", str(valid_csv_path)]
            with pytest.raises(SystemExit) as excinfo:
                validate_main()
            assert excinfo.value.code == 2  # argparse error code
        finally:
            sys.argv = original_argv

    def test_cli_fails_with_wrong_schema_type_for_csv(self, valid_csv_path, capsys):
        """Test CLI invocation with wrong schema type for CSV."""
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["validate.py", str(valid_csv_path), "--schema-type", "regression"]
            exit_code = validate_main()
            assert exit_code == 1
        finally:
            sys.argv = original_argv

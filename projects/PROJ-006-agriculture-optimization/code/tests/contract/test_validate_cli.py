"""
Contract tests for the CLI validation module (T012).
These tests verify that validate.py correctly enforces schema contracts.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from src.cli.validate import validate_csv_artifact, validate_json_artifact, FatalError
from src.config.schemas import validate_dataset_schema, validate_regression_output


class TestCSVValidation:
    """Tests for CSV artifact validation."""

    def test_valid_dataset_csv(self, tmp_path):
        """Test that a valid dataset CSV passes validation."""
        # Create a valid CSV matching the schema
        valid_data = {
            "household_id": [1, 2],
            "latitude": [34.0, 35.0],
            "longitude": [12.0, 13.0],
            "CSA_Index": [5, 4],
            "Stability_Score": [0.85, 0.90],
            "HFIAS": [12, 10],
            "finance_access": [True, False],
            "village_id": ["V1", "V1"]
        }
        df = pd.DataFrame(valid_data)
        csv_path = tmp_path / "valid_dataset.csv"
        df.to_csv(csv_path, index=False)

        # Assert validation passes
        assert validate_csv_artifact(csv_path, "dataset") is True

    def test_missing_columns_csv(self, tmp_path):
        """Test that a CSV with missing required columns fails."""
        invalid_data = {
            "household_id": [1],
            "latitude": [34.0]
            # Missing other required columns
        }
        df = pd.DataFrame(invalid_data)
        csv_path = tmp_path / "invalid_missing_cols.csv"
        df.to_csv(csv_path, index=False)

        # Assert validation fails
        assert validate_csv_artifact(csv_path, "dataset") is False

    def test_nonexistent_file(self, tmp_path):
        """Test that a nonexistent file raises FatalError."""
        csv_path = tmp_path / "nonexistent.csv"

        with pytest.raises(FatalError, match="Artifact not found"):
            validate_csv_artifact(csv_path, "dataset")

    def test_invalid_csv_format(self, tmp_path):
        """Test that a malformed CSV raises FatalError."""
        csv_path = tmp_path / "malformed.csv"
        with open(csv_path, "w") as f:
            f.write("col1,col2\nval1\nval2,val3") # Malformed row

        with pytest.raises(FatalError):
            validate_csv_artifact(csv_path, "dataset")


class TestJSONValidation:
    """Tests for JSON artifact validation."""

    def test_valid_regression_json(self, tmp_path):
        """Test that a valid regression JSON passes validation."""
        valid_data = {
            "model_type": "clustered",
            "adjusted_alpha": 0.0167,
            "coefficients": {
                "CSA_Index": 0.5,
                "finance_access": 0.2
            },
            "vif_scores": {
                "CSA_Index": 1.2,
                "finance_access": 1.1
            },
            "collinearity_warning": False
        }
        json_path = tmp_path / "valid_regression.json"
        with open(json_path, "w") as f:
            json.dump(valid_data, f)

        # Assert validation passes
        assert validate_json_artifact(json_path, "regression") is True

    def test_missing_fields_json(self, tmp_path):
        """Test that a JSON with missing required fields fails."""
        invalid_data = {
            "model_type": "clustered"
            # Missing coefficients, vif_scores, etc.
        }
        json_path = tmp_path / "invalid_missing_fields.json"
        with open(json_path, "w") as f:
            json.dump(invalid_data, f)

        # Assert validation fails
        assert validate_json_artifact(json_path, "regression") is False

    def test_nonexistent_json_file(self, tmp_path):
        """Test that a nonexistent JSON file raises FatalError."""
        json_path = tmp_path / "nonexistent.json"

        with pytest.raises(FatalError, match="Artifact not found"):
            validate_json_artifact(json_path, "regression")

    def test_invalid_json_format(self, tmp_path):
        """Test that a malformed JSON raises FatalError."""
        json_path = tmp_path / "malformed.json"
        with open(json_path, "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(FatalError):
            validate_json_artifact(json_path, "regression")


class TestIntegration:
    """Integration tests for the validation pipeline."""

    def test_end_to_end_valid_flow(self, tmp_path):
        """Simulate a full pipeline flow with valid artifacts."""
        # 1. Create valid dataset
        df = pd.DataFrame({
            "household_id": range(10),
            "latitude": [34.0] * 10,
            "longitude": [12.0] * 10,
            "CSA_Index": [5] * 10,
            "Stability_Score": [0.9] * 10,
            "HFIAS": [10] * 10,
            "finance_access": [True] * 10,
            "village_id": ["V1"] * 10
        })
        csv_path = tmp_path / "analysis_dataset.csv"
        df.to_csv(csv_path, index=False)

        # 2. Validate it
        assert validate_csv_artifact(csv_path, "dataset") is True

        # 3. Create valid regression output
        reg_data = {
            "model_type": "clustered",
            "adjusted_alpha": 0.0167,
            "coefficients": {"CSA_Index": 0.5},
            "vif_scores": {"CSA_Index": 1.2},
            "collinearity_warning": False
        }
        json_path = tmp_path / "regression_results.json"
        with open(json_path, "w") as f:
            json.dump(reg_data, f)

        # 4. Validate it
        assert validate_json_artifact(json_path, "regression") is True
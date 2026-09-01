"""
Contract tests for the CLI validation tool.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from src.cli.validate import validate_csv_artifact, validate_json_artifact
from src.config.schemas import AnalysisDatasetRecord

class TestCSVValidation:
    def test_valid_dataset_csv(self, tmp_path):
        """Test that a valid dataset CSV passes validation."""
        # Create a valid CSV matching AnalysisDatasetRecord
        data = {
            "household_id": [1, 2],
            "latitude": [-12.34, -12.35],
            "longitude": [34.56, 34.57],
            "land_size": [1.5, 2.0],
            "education_level": [3, 4],
            "finance_access": [True, False],
            "practice_mixed_farming": [True, True],
            "practice_terracing": [False, True],
            "practice_conservation_tillage": [True, False],
            "practice_agroforestry": [False, False],
            "extension_visits": [2, 5],
            "hlias": [10, 15],
            "CSA_Index": [1.0, 2.0],
            "Stability_Score": [0.8, 0.9],
            "HFIAS": [5.0, 6.0],
            "village_id": ["v1", "v2"]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "valid_dataset.csv"
        df.to_csv(csv_path, index=False)

        assert validate_csv_artifact(csv_path, "dataset") is True

    def test_invalid_dataset_csv_missing_column(self, tmp_path):
        """Test that a CSV missing a required column fails."""
        data = {
            "household_id": [1],
            "latitude": [-12.34],
            # Missing many columns
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "invalid_missing.csv"
        df.to_csv(csv_path, index=False)

        assert validate_csv_artifact(csv_path, "dataset") is False

    def test_invalid_dataset_csv_wrong_type(self, tmp_path):
        """Test that a CSV with wrong data types fails."""
        data = {
            "household_id": ["not_an_int"], # Should be int
            "latitude": [-12.34],
            "longitude": [34.56],
            "land_size": [1.5],
            "education_level": [3],
            "finance_access": [True],
            "practice_mixed_farming": [True],
            "practice_terracing": [False],
            "practice_conservation_tillage": [True],
            "practice_agroforestry": [False],
            "extension_visits": [2],
            "hlias": [10],
            "CSA_Index": [1.0],
            "Stability_Score": [0.8],
            "HFIAS": [5.0],
            "village_id": ["v1"]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "invalid_type.csv"
        df.to_csv(csv_path, index=False)

        # Pydantic validation should catch the type error
        assert validate_csv_artifact(csv_path, "dataset") is False

class TestJSONValidation:
    def test_valid_regression_json(self, tmp_path):
        """Test that a valid regression JSON passes."""
        data = {
            "adjusted_alpha": 0.005,
            "bonferroni_corrected_p_values": {"var1": 0.01, "var2": 0.03},
            "coefficients": {"var1": 0.5, "var2": -0.2},
            "vif_scores": {"var1": 1.2, "var2": 1.1},
            "model_type": "clustered",
            "collinearity_warning": False,
            "aggregation_warning": False
        }
        json_path = tmp_path / "valid_regression.json"
        with open(json_path, 'w') as f:
            json.dump(data, f)

        assert validate_json_artifact(json_path, "regression") is True

    def test_invalid_regression_json_missing_field(self, tmp_path):
        """Test that a JSON missing a required field fails."""
        data = {
            "coefficients": {"var1": 0.5},
            # Missing other required fields
        }
        json_path = tmp_path / "invalid_missing.json"
        with open(json_path, 'w') as f:
            json.dump(data, f)

        assert validate_json_artifact(json_path, "regression") is False

class TestIntegration:
    def test_file_not_found(self, tmp_path):
        """Test validation of a non-existent file."""
        fake_path = tmp_path / "does_not_exist.csv"
        assert validate_csv_artifact(fake_path, "dataset") is False

    def test_wrong_schema_type(self, tmp_path):
        """Test passing wrong schema type."""
        data = {"household_id": [1]}
        df = pd.DataFrame(data)
        csv_path = tmp_path / "test.csv"
        df.to_csv(csv_path, index=False)

        # Should fail because schema type doesn't match content or logic
        assert validate_csv_artifact(csv_path, "regression") is False

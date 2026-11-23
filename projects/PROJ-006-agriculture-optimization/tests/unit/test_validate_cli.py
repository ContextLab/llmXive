"""
Unit tests for the validate.py CLI tool.

These tests verify that the CLI correctly validates CSV and JSON artifacts
against their respective schema contracts.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from src.cli.validate import validate_csv_artifact, validate_json_artifact, FatalError
from src.config.schemas import AnalysisDatasetRecord, RegressionOutput

class TestCSVValidation:
    """Tests for CSV artifact validation."""
    
    def test_valid_csv_passes(self, tmp_path):
        """Test that a valid CSV file passes validation."""
        # Create a valid CSV file
        csv_path = tmp_path / "valid.csv"
        df = pd.DataFrame({
            'household_id': [1, 2, 3],
            'latitude': [32.1, 32.2, 32.3],
            'longitude': [35.1, 35.2, 35.3],
            'land_size': [1.5, 2.0, 1.8],
            'education_level': [3, 4, 2],
            'finance_access': [True, False, True],
            'practice_mixed_farming': [True, True, False],
            'practice_terracing': [False, True, True],
            'practice_conservation_tillage': [True, False, True],
            'practice_agroforestry': [False, True, True],
            'extension_visits': [2, 3, 1],
            'hlias': [10, 15, 8],
            'CSA_Index': [3.0, 4.0, 2.0],
            'Stability_Score': [0.8, 0.9, 0.7],
            'HFIAS': [5.0, 8.0, 3.0],
            'village_id': ['v1', 'v2', 'v3']
        })
        df.to_csv(csv_path, index=False)
        
        # Validate
        result = validate_csv_artifact(csv_path)
        assert result is True
    
    def test_missing_file_raises(self, tmp_path):
        """Test that missing file raises FatalError."""
        csv_path = tmp_path / "missing.csv"
        
        with pytest.raises(FatalError):
            validate_csv_artifact(csv_path)
    
    def test_invalid_schema_fails(self, tmp_path):
        """Test that a CSV with invalid schema fails validation."""
        # Create a CSV with missing required columns
        csv_path = tmp_path / "invalid.csv"
        df = pd.DataFrame({
            'household_id': [1, 2],
            'latitude': [32.1, 32.2]
            # Missing many required columns
        })
        df.to_csv(csv_path, index=False)
        
        # Validate (should return False, not raise)
        result = validate_csv_artifact(csv_path)
        assert result is False

class TestJSONValidation:
    """Tests for JSON artifact validation."""
    
    def test_valid_json_passes(self, tmp_path):
        """Test that a valid JSON file passes validation."""
        # Create a valid JSON file
        json_path = tmp_path / "valid.json"
        data = {
            "adjusted_alpha": 0.0167,
            "bonferroni_corrected_p_values": {"practice_mixed_farming": 0.02},
            "coefficients": {
                "practice_mixed_farming": 0.5,
                "finance_access": 0.3
            },
            "vif_scores": {
                "practice_mixed_farming": 1.2,
                "finance_access": 1.1
            },
            "model_type": "aggregated",
            "collinearity_warning": False
        }
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        # Validate
        result = validate_json_artifact(json_path)
        assert result is True
    
    def test_missing_file_raises(self, tmp_path):
        """Test that missing file raises FatalError."""
        json_path = tmp_path / "missing.json"
        
        with pytest.raises(FatalError):
            validate_json_artifact(json_path)
    
    def test_invalid_schema_fails(self, tmp_path):
        """Test that a JSON with invalid schema fails validation."""
        # Create a JSON with missing required fields
        json_path = tmp_path / "invalid.json"
        data = {
            "coefficients": {}
            # Missing many required fields
        }
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        # Validate (should return False, not raise)
        result = validate_json_artifact(json_path)
        assert result is False

class TestIntegration:
    """Integration tests for the validate CLI."""
    
    def test_full_validation_workflow(self, tmp_path):
        """Test the full validation workflow with both CSV and JSON."""
        # Create valid CSV
        csv_path = tmp_path / "analysis_dataset.csv"
        df = pd.DataFrame({
            'household_id': [1, 2, 3],
            'latitude': [32.1, 32.2, 32.3],
            'longitude': [35.1, 35.2, 35.3],
            'land_size': [1.5, 2.0, 1.8],
            'education_level': [3, 4, 2],
            'finance_access': [True, False, True],
            'practice_mixed_farming': [True, True, False],
            'practice_terracing': [False, True, True],
            'practice_conservation_tillage': [True, False, True],
            'practice_agroforestry': [False, True, True],
            'extension_visits': [2, 3, 1],
            'hlias': [10, 15, 8],
            'CSA_Index': [3.0, 4.0, 2.0],
            'Stability_Score': [0.8, 0.9, 0.7],
            'HFIAS': [5.0, 8.0, 3.0],
            'village_id': ['v1', 'v2', 'v3']
        })
        df.to_csv(csv_path, index=False)
        
        # Create valid JSON
        json_path = tmp_path / "regression_results.json"
        data = {
            "adjusted_alpha": 0.0167,
            "bonferroni_corrected_p_values": {"practice_mixed_farming": 0.02},
            "coefficients": {
                "practice_mixed_farming": 0.5,
                "finance_access": 0.3
            },
            "vif_scores": {
                "practice_mixed_farming": 1.2,
                "finance_access": 1.1
            },
            "model_type": "aggregated",
            "collinearity_warning": False
        }
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        # Validate both
        csv_result = validate_csv_artifact(csv_path)
        json_result = validate_json_artifact(json_path)
        
        assert csv_result is True
        assert json_result is True
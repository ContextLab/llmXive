"""
Contract tests for schema validation.
Ensures that data artifacts conform to the defined schemas.
"""
import pytest
import json
import yaml
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from validate_schemas import load_schema, validate_json_against_schema, validate_csv_against_schema
from config import get_raw_data_dir

class TestSchemaLoading:
    def test_load_stimulus_schema(self):
        """Test loading the stimulus schema."""
        schema = load_schema("stimulus.schema.yaml")
        assert "type" in schema
        assert schema["type"] == "object"
        assert "required" in schema
        assert "stimulus_id" in schema["required"]

    def test_load_rating_schema(self):
        """Test loading the rating schema."""
        schema = load_schema("rating.schema.yaml")
        assert "type" in schema
        assert schema["type"] == "object"
        assert "participant_id" in schema["required"]

    def test_load_analysis_result_schema(self):
        """Test loading the analysis result schema."""
        schema = load_schema("analysis_result.schema.yaml")
        assert "type" in schema
        assert "fixed_effects" in schema["required"]

class TestJsonValidation:
    def test_valid_stimulus_data(self):
        """Test validation of valid stimulus data."""
        schema = load_schema("stimulus.schema.yaml")
        valid_data = {
            "stimulus_id": "S0001",
            "text_content": "Hey, I'm really struggling with this assignment.",
            "base_scenario": "academic_stress",
            "emoji_count": 0,
            "punctuation_count": 1,
            "length": 50,
            "cue_intensity": "low",
            "relationship_context": "friend"
        }
        errors = validate_json_against_schema(valid_data, schema)
        assert len(errors) == 0

    def test_invalid_stimulus_missing_field(self):
        """Test validation fails on missing required field."""
        schema = load_schema("stimulus.schema.yaml")
        invalid_data = {
            "stimulus_id": "S0001",
            "text_content": "Hello",
            # Missing base_scenario
            "emoji_count": 0,
            "punctuation_count": 1,
            "length": 5,
            "cue_intensity": "low",
            "relationship_context": "friend"
        }
        errors = validate_json_against_schema(invalid_data, schema)
        assert len(errors) > 0
        assert any("base_scenario" in err for err in errors)

    def test_invalid_stimulus_wrong_enum(self):
        """Test validation fails on invalid enum value."""
        schema = load_schema("stimulus.schema.yaml")
        invalid_data = {
            "stimulus_id": "S0001",
            "text_content": "Hello",
            "base_scenario": "invalid_scenario",
            "emoji_count": 0,
            "punctuation_count": 1,
            "length": 5,
            "cue_intensity": "low",
            "relationship_context": "friend"
        }
        errors = validate_json_against_schema(invalid_data, schema)
        assert len(errors) > 0
        assert any("base_scenario" in err for err in errors)

class TestCsvValidation:
    def test_create_temp_csv_and_validate(self, tmp_path):
        """Test validating a temporary CSV file."""
        schema = load_schema("stimulus.schema.yaml")
        
        # Create a valid CSV
        csv_path = tmp_path / "test_stimuli.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["stimulus_id", "text_content", "base_scenario", "emoji_count", "punctuation_count", "length", "cue_intensity", "relationship_context"])
            writer.writerow(["S0001", "Hello", "academic_stress", 0, 1, 5, "low", "friend"])
        
        errors = validate_csv_against_schema(csv_path, schema)
        assert len(errors) == 0

    def test_create_invalid_csv_and_validate(self, tmp_path):
        """Test validating an invalid CSV file."""
        schema = load_schema("stimulus.schema.yaml")
        
        # Create an invalid CSV (missing required field)
        csv_path = tmp_path / "test_stimuli_invalid.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["stimulus_id", "text_content", "base_scenario", "emoji_count", "punctuation_count", "length", "cue_intensity", "relationship_context"])
            writer.writerow(["S0001", "Hello", "", 0, 1, 5, "low", "friend"]) # Empty base_scenario
        
        errors = validate_csv_against_schema(csv_path, schema)
        assert len(errors) > 0

class TestIntegration:
    def test_stimuli_csv_exists_and_valid(self):
        """Test that the actual stimuli.csv exists and is valid."""
        stimuli_path = get_raw_data_dir() / "stimuli.csv"
        if not stimuli_path.exists():
            pytest.skip("stimuli.csv not found (expected if T013 not run yet)")
        
        schema = load_schema("stimulus.schema.yaml")
        errors = validate_csv_against_schema(stimuli_path, schema)
        assert len(errors) == 0, f"Stimuli CSV validation failed: {errors}"

    def test_ratings_csv_exists_and_valid(self):
        """Test that the actual ratings.csv exists and is valid."""
        ratings_path = get_raw_data_dir() / "ratings.csv"
        if not ratings_path.exists():
            pytest.skip("ratings.csv not found (expected if T014 not run yet)")
        
        schema = load_schema("rating.schema.yaml")
        errors = validate_csv_against_schema(ratings_path, schema)
        assert len(errors) == 0, f"Ratings CSV validation failed: {errors}"

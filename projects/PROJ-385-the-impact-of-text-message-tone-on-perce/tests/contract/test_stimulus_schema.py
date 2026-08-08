"""
Contract test for stimulus schema validation.

Validates that the generated stimuli file (data/raw/stimuli.csv)
conforms to the expected schema defined in specs/001-the-impact-of-text-message-tone-on-perce/contracts/stimulus.schema.yaml.
"""
import csv
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pytest
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_raw_data_dir, get_contracts_dir
from validate_schemas import load_schema, validate_csv_against_schema

class TestStimulusSchema:
    """Test suite for stimulus schema validation."""

    @pytest.fixture
    def stimuli_file(self) -> Path:
        """Get the path to the stimuli CSV file."""
        return get_raw_data_dir() / "stimuli.csv"

    @pytest.fixture
    def schema_file(self) -> Path:
        """Get the path to the stimulus schema YAML file."""
        return get_contracts_dir() / "stimulus.schema.yaml"

    def test_stimuli_file_exists(self, stimuli_file: Path):
        """Test that the stimuli file exists."""
        assert stimuli_file.exists(), f"Stimuli file not found: {stimuli_file}"

    def test_stimuli_schema_exists(self, schema_file: Path):
        """Test that the schema file exists."""
        assert schema_file.exists(), f"Schema file not found: {schema_file}"

    def test_stimuli_against_schema(self, stimuli_file: Path, schema_file: Path):
        """Test that the stimuli file conforms to the schema."""
        # Load schema
        schema = load_schema(schema_file)
        
        # Validate CSV against schema
        is_valid, errors = validate_csv_against_schema(stimuli_file, schema)
        
        assert is_valid, f"Stimuli file does not conform to schema: {errors}"

    def test_required_columns_present(self, stimuli_file: Path):
        """Test that all required columns are present in the stimuli file."""
        required_columns = [
            "id", "text", "emoji_count", "punctuation_type", 
            "length_category", "scenario_id", "cue_intensity"
        ]
        
        with open(stimuli_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            for col in required_columns:
                assert col in headers, f"Missing required column: {col}"

    def test_data_types(self, stimuli_file: Path):
        """Test that data types are correct."""
        with open(stimuli_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) > 0, "Stimuli file is empty"
            
            # Check first row for data types
            row = rows[0]
            
            # id should be string
            assert isinstance(row["id"], str), "id should be a string"
            
            # text should be string
            assert isinstance(row["text"], str), "text should be a string"
            
            # emoji_count should be integer
            assert row["emoji_count"].isdigit(), "emoji_count should be an integer"
            
            # cue_intensity should be float
            try:
                float(row["cue_intensity"])
            except ValueError:
                assert False, "cue_intensity should be a float"

    def test_factorial_combinations_count(self, stimuli_file: Path):
        """Test that the stimuli file contains the expected 12 factorial combinations."""
        with open(stimuli_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            combinations = set()
            for row in rows:
                scenario_id = row["scenario_id"]
                parts = scenario_id.split("_")
                if len(parts) >= 4:
                    rel = parts[0]
                    cue = parts[1]
                    intensity = parts[2]
                    combinations.add((rel, cue, intensity))
            
            # We expect 12 unique combinations
            assert len(combinations) == 12, f"Expected 12 factorial combinations, found {len(combinations)}: {combinations}"

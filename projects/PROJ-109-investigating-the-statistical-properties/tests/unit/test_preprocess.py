"""
Unit tests for the preprocessing module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

# Import the function to test
from code.data.preprocess import filter_halos_by_particles, load_schema, validate_schema

class TestFilterHalosByParticles:
    """Tests for filter_halos_by_particles function."""

    def test_filter_halos_300_particles(self):
        """Test that halos with < 300 particles are removed."""
        # Create a mock dataframe
        data = {
            'mass': [1e10, 1e11, 1e12, 1e13],
            'particle_count': [100, 299, 300, 5000],
            'position': [[0,0,0], [1,1,1], [2,2,2], [3,3,3]]
        }
        df = pd.DataFrame(data)

        # Apply filter
        filtered_df = filter_halos_by_particles(df, min_particles=300)

        # Assertions
        assert len(filtered_df) == 2, f"Expected 2 rows, got {len(filtered_df)}"
        assert filtered_df['particle_count'].min() >= 300, "Minimum particle count should be >= 300"
        assert 300 in filtered_df['particle_count'].values, "Row with 300 particles should be kept"
        assert 5000 in filtered_df['particle_count'].values, "Row with 5000 particles should be kept"

    def test_filter_halos_all_removed(self):
        """Test behavior when all halos are below threshold."""
        data = {
            'mass': [1e10, 1e11],
            'particle_count': [100, 200],
            'position': [[0,0,0], [1,1,1]]
        }
        df = pd.DataFrame(data)

        filtered_df = filter_halos_by_particles(df, min_particles=300)

        assert len(filtered_df) == 0, "Expected empty dataframe"

    def test_filter_halos_none_removed(self):
        """Test behavior when all halos are above threshold."""
        data = {
            'mass': [1e12, 1e13],
            'particle_count': [301, 5000],
            'position': [[0,0,0], [1,1,1]]
        }
        df = pd.DataFrame(data)

        filtered_df = filter_halos_by_particles(df, min_particles=300)

        assert len(filtered_df) == 2, "Expected 2 rows"
        assert filtered_df['particle_count'].min() >= 300

class TestSchemaValidation:
    """Tests for schema loading and validation."""

    def test_load_schema(self):
        """Test loading a valid schema."""
        # Create a temporary schema file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            schema = {
                "type": "object",
                "properties": {
                    "particle_count": {"type": "integer"}
                },
                "required": ["particle_count"]
            }
            json.dump(schema, f)
            temp_path = f.name

        try:
            loaded = load_schema(temp_path)
            assert loaded is not None
            assert "properties" in loaded
        finally:
            os.remove(temp_path)

    def test_validate_schema_success(self):
        """Test successful validation."""
        schema = {
            "type": "object",
            "properties": {
                "particle_count": {"type": "integer", "minimum": 0}
            },
            "required": ["particle_count"]
        }
        
        df = pd.DataFrame({"particle_count": [300, 400]})
        assert validate_schema(df, schema) is True

    def test_validate_schema_failure(self):
        """Test validation failure."""
        schema = {
            "type": "object",
            "properties": {
                "particle_count": {"type": "integer", "minimum": 0}
            },
            "required": ["particle_count"]
        }
        
        # Create a row that violates the schema (if we could pass a dict that doesn't match)
        # Since validate_schema takes a DF and converts to dict, we test the logic.
        # Actually, jsonschema.validate raises on failure.
        df = pd.DataFrame({"particle_count": ["string"]}) # Type mismatch
        
        with pytest.raises(Exception): # jsonschema.ValidationError
            validate_schema(df, schema)
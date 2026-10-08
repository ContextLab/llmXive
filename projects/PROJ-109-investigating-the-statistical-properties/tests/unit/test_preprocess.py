import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
import json
import yaml

# Add parent to path for imports if running as script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.preprocess import filter_halos_by_particles, load_schema, validate_schema

class TestFilterHalos:
    def test_filter_halos_300_particles(self):
        """Test that filter_halos_by_particles correctly removes halos with < 300 particles."""
        data = {
            'mass': [1e12, 1e13, 1e11],
            'position': [[1, 1, 1], [2, 2, 2], [3, 3, 3]],
            'velocity': [[10, 10, 10], [20, 20, 20], [30, 30, 30]],
            'particle_count': [500, 300, 200]
        }
        df = pd.DataFrame(data)
        
        filtered = filter_halos_by_particles(df, min_particles=300)
        
        assert len(filtered) == 2
        assert all(filtered['particle_count'] >= 300)
        assert 200 not in filtered['particle_count'].values

class TestSchemaValidation:
    def test_validate_schema_valid_data(self):
        """Test validation with data that matches the schema."""
        # Create a temporary schema file for testing
        schema = {
            "type": "object",
            "properties": {
                "mass": {"type": "array", "items": {"type": "number"}},
                "position": {"type": "array", "items": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "number"}}},
                "velocity": {"type": "array", "items": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "number"}}},
                "particle_count": {"type": "array", "items": {"type": "integer"}}
            },
            "required": ["mass", "position", "velocity", "particle_count"],
            "additionalProperties": False
        }
        
        data = {
            'mass': [1e12, 1e13],
            'position': [[1, 1, 1], [2, 2, 2]],
            'velocity': [[10, 10, 10], [20, 20, 20]],
            'particle_count': [500, 300]
        }
        
        # This should not raise
        validate_schema(pd.DataFrame(data), schema)

    def test_validate_schema_invalid_particle_count(self):
        """Test validation fails for negative particle counts."""
        schema = {
            "type": "object",
            "properties": {
                "mass": {"type": "array", "items": {"type": "number"}},
                "position": {"type": "array", "items": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "number"}}},
                "velocity": {"type": "array", "items": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "number"}}},
                "particle_count": {"type": "array", "items": {"type": "integer", "minimum": 0}}
            },
            "required": ["mass", "position", "velocity", "particle_count"],
            "additionalProperties": False
        }
        
        data = {
            'mass': [1e12],
            'position': [[1, 1, 1]],
            'velocity': [[10, 10, 10]],
            'particle_count': [-5]  # Invalid: negative
        }
        
        with pytest.raises(Exception): # jsonschema.ValidationError
            validate_schema(pd.DataFrame(data), schema)
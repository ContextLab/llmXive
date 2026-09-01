import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
import yaml

# Import the functions to test
from data.preprocess import load_schema, validate_schema, filter_halos_by_particles

class TestSchemaValidation:
    @pytest.fixture
    def sample_schema(self):
        return {
            "type": "object",
            "properties": {
                "halo_id": {"type": "integer"},
                "mass": {"type": "number"},
                "x": {"type": "number"},
                "y": {"type": "number"},
                "z": {"type": "number"},
                "num_particles": {"type": "integer"},
                "shape_s": {"type": "number"},
                "spin_lambda": {"type": "number"},
                "concentration": {"type": "number"},
                "overdensity": {"type": "number"},
                "particle_count": {"type": "integer"},
                "fit_status": {"type": "string"}
            },
            "required": ["halo_id", "mass", "x", "y", "z", "num_particles"],
            "additionalProperties": True
        }

    @pytest.fixture
    def valid_dataframe(self):
        return pd.DataFrame({
            "halo_id": [1, 2, 3],
            "mass": [1e10, 2e10, 3e10],
            "x": [1.0, 2.0, 3.0],
            "y": [1.0, 2.0, 3.0],
            "z": [1.0, 2.0, 3.0],
            "num_particles": [500, 600, 700],
            "shape_s": [0.5, 0.6, 0.7],
            "spin_lambda": [0.02, 0.03, 0.04],
            "concentration": [10.0, 12.0, 11.0],
            "overdensity": [200.0, 250.0, 300.0],
            "particle_count": [500, 600, 700],
            "fit_status": ["converged", "converged", "failed"]
        })

    @pytest.fixture
    def invalid_dataframe(self):
        # Missing a required field (mass)
        return pd.DataFrame({
            "halo_id": [1, 2],
            "x": [1.0, 2.0],
            "y": [1.0, 2.0],
            "z": [1.0, 2.0],
            "num_particles": [500, 600],
        })

    @pytest.fixture
    def type_mismatch_dataframe(self):
        # mass should be number, but is string
        return pd.DataFrame({
            "halo_id": [1, 2],
            "mass": ["not_a_number", "also_not"],
            "x": [1.0, 2.0],
            "y": [1.0, 2.0],
            "z": [1.0, 2.0],
            "num_particles": [500, 600],
        })

    def test_load_schema_from_yaml(self, tmp_path):
        schema_content = """
        type: object
        properties:
          halo_id:
            type: integer
          mass:
            type: number
        required:
          - halo_id
          - mass
        """
        schema_file = tmp_path / "test_schema.yaml"
        schema_file.write_text(schema_content)
        
        schema = load_schema(str(schema_file))
        
        assert schema["type"] == "object"
        assert "halo_id" in schema["properties"]
        assert "mass" in schema["properties"]
        assert "halo_id" in schema["required"]

    def test_validate_valid_data(self, valid_dataframe, sample_schema):
        # This should not raise an exception
        result = validate_schema(valid_dataframe, sample_schema)
        assert result is True

    def test_validate_missing_required_field(self, invalid_dataframe, sample_schema):
        # Should raise ValidationError because 'mass' is missing
        with pytest.raises(Exception) as excinfo:
            validate_schema(invalid_dataframe, sample_schema)
        
        assert "missing required fields" in str(excinfo.value).lower() or "validation failed" in str(excinfo.value).lower()

    def test_validate_type_mismatch(self, type_mismatch_dataframe, sample_schema):
        # Should raise ValidationError because 'mass' is string not number
        with pytest.raises(Exception) as excinfo:
            validate_schema(type_mismatch_dataframe, sample_schema)
        
        assert "validation failed" in str(excinfo.value).lower()

    def test_filter_then_validate(self, sample_schema):
        # Create a dataframe with some halos having < 300 particles
        df = pd.DataFrame({
            "halo_id": [1, 2, 3, 4],
            "mass": [1e10, 2e10, 3e10, 4e10],
            "x": [1.0, 2.0, 3.0, 4.0],
            "y": [1.0, 2.0, 3.0, 4.0],
            "z": [1.0, 2.0, 3.0, 4.0],
            "num_particles": [200, 500, 100, 800], # 200 and 100 should be filtered out
            "shape_s": [0.5, 0.6, 0.7, 0.8],
            "spin_lambda": [0.02, 0.03, 0.04, 0.05],
            "concentration": [10.0, 12.0, 11.0, 13.0],
            "overdensity": [200.0, 250.0, 300.0, 350.0],
            "particle_count": [200, 500, 100, 800],
            "fit_status": ["converged", "converged", "failed", "converged"]
        })

        # Filter first
        df_filtered = filter_halos_by_particles(df, min_particles=300)
        
        # Verify filtering worked
        assert len(df_filtered) == 2
        assert all(df_filtered["num_particles"] >= 300)
        
        # Then validate
        result = validate_schema(df_filtered, sample_schema)
        assert result is True
        # Check that the IDs are the ones that passed (2 and 4)
        assert list(df_filtered["halo_id"]) == [2, 4]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
import pytest
import os
import json
from pathlib import Path
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_schemas import (
    generate_dataset_schema,
    generate_resampling_schema,
    save_dataset_schema,
    save_resampling_schema
)

class TestGenerateSchemas:
    """Tests for schema generation functions."""

    def test_generate_dataset_schema_structure(self):
        """Test that the dataset schema has the required structure."""
        schema = generate_dataset_schema()
        
        assert "$schema" in schema
        assert schema["title"] == "Processed Dataset Schema"
        assert "properties" in schema
        
        # Check required properties
        required_props = ["composition", "target_properties", "descriptors", "imbalance_scores"]
        for prop in required_props:
            assert prop in schema["properties"], f"Missing property: {prop}"

    def test_generate_resampling_schema_structure(self):
        """Test that the resampling schema has the required structure."""
        schema = generate_resampling_schema()
        
        assert "$schema" in schema
        assert schema["title"] == "Resampling Schema"
        assert "properties" in schema
        
        # Check required properties per FR-003
        required_props = ["bin_id", "sample_count", "CV", "real_data_flag", "synthetic_flag"]
        for prop in required_props:
            assert prop in schema["properties"], f"Missing property: {prop}"

    def test_resampling_schema_cv_constraints(self):
        """Test that CV property has correct min/max constraints."""
        schema = generate_resampling_schema()
        cv_prop = schema["properties"]["CV"]
        
        assert "minimum" in cv_prop
        assert cv_prop["minimum"] == 0.0
        assert "maximum" in cv_prop
        assert cv_prop["maximum"] == 1.0

    def test_resampling_schema_boolean_flags(self):
        """Test that boolean flags are correctly defined."""
        schema = generate_resampling_schema()
        
        for flag in ["real_data_flag", "synthetic_flag"]:
            assert flag in schema["properties"]
            assert schema["properties"][flag]["type"] == "boolean"

    def test_save_dataset_schema_creates_file(self, tmp_path):
        """Test that save_dataset_schema creates a valid JSON file."""
        output_path = str(tmp_path / "test_dataset_schema.json")
        schema = generate_dataset_schema()
        result_path = save_dataset_schema(schema, output_path)
        
        assert os.path.exists(result_path)
        
        with open(result_path, 'r') as f:
            loaded_schema = json.load(f)
        
        assert loaded_schema == schema

    def test_save_resampling_schema_creates_file(self, tmp_path):
        """Test that save_resampling_schema creates a valid JSON file."""
        output_path = str(tmp_path / "test_resampling_schema.json")
        schema = generate_resampling_schema()
        result_path = save_resampling_schema(schema, output_path)
        
        assert os.path.exists(result_path)
        
        with open(result_path, 'r') as f:
            loaded_schema = json.load(f)
        
        assert loaded_schema == schema

    def test_resampling_schema_contains_fr003_columns(self):
        """
        Verify that the resampling schema explicitly includes the columns
        required by FR-003: bin_id, sample_count, CV, real_data_flag, synthetic_flag.
        """
        schema = generate_resampling_schema()
        fr003_columns = ["bin_id", "sample_count", "CV", "real_data_flag", "synthetic_flag"]
        
        for col in fr003_columns:
            assert col in schema["properties"], f"FR-003 column '{col}' missing from schema"

    def test_schema_validates_against_draft07(self):
        """
        Basic validation that the generated schemas conform to JSON Schema Draft 07.
        """
        dataset_schema = generate_dataset_schema()
        resampling_schema = generate_resampling_schema()
        
        assert dataset_schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert resampling_schema["$schema"] == "http://json-schema.org/draft-07/schema#"
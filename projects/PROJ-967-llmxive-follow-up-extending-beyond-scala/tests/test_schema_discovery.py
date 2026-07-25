import pytest
import pandas as pd
import yaml
from pathlib import Path
import sys
import tempfile
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from schema_discovery import (
    load_schema,
    save_schema,
    load_dataset,
    discover_schema,
    validate_schema,
    REQUIRED_DIMENSIONS
)


class TestSchemaDiscovery:
    @pytest.fixture
    def temp_schema_file(self, tmp_path):
        schema_path = tmp_path / "test_schema.yaml"
        initial_schema = {
            "description": "Test schema",
            "expected_columns": ["prompt", "scores"]
        }
        with open(schema_path, "w") as f:
            yaml.dump(initial_schema, f)
        return schema_path

    @pytest.fixture
    def sample_dataframe(self):
        # Create a mock dataframe with expected columns
        data = {
            "prompt": ["test prompt 1", "test prompt 2"],
            "teacher_logits": [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]],
            "student_scalar": [0.75, 0.82],
            "human_annotation_Alignment": [0.9, 0.85],
            "human_annotation_Realism": [0.8, 0.75],
            "human_annotation_Aesthetics": [0.7, 0.65],
            "human_annotation_Plausibility": [0.6, 0.55],
            "primary_dimension": ["Alignment", "Realism"]
        }
        return pd.DataFrame(data)

    def test_load_schema_valid(self, temp_schema_file):
        schema = load_schema(temp_schema_file)
        assert "description" in schema
        assert schema["description"] == "Test schema"

    def test_load_schema_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_schema(tmp_path / "nonexistent.yaml")

    def test_discover_schema_mappings(self, temp_schema_file, sample_dataframe):
        current_schema = load_schema(temp_schema_file)
        discovered = discover_schema(sample_dataframe, current_schema)

        assert "actual_columns" in discovered
        assert "logical_field_mapping" in discovered

        mapping = discovered["logical_field_mapping"]
        assert "prompt" in mapping
        assert "teacher_logits" in mapping
        assert "student_scalar" in mapping
        assert "human_annotations" in mapping
        assert "primary_dimension" in mapping

        assert mapping["prompt"] == "prompt"
        assert mapping["student_scalar"] == "student_scalar"

    def test_validate_schema_success(self, temp_schema_file, sample_dataframe):
        current_schema = load_schema(temp_schema_file)
        discovered = discover_schema(sample_dataframe, current_schema)

        # Should not raise
        result = validate_schema(sample_dataframe, discovered)
        assert result is True

    def test_validate_schema_missing_dimensions(self, temp_schema_file):
        # Create dataframe missing required dimensions
        data = {
            "prompt": ["test"],
            "teacher_logits": [[0.1]],
            "student_scalar": [0.5],
            "human_annotation_Alignment": [0.9],
            # Missing Realism, Aesthetics, Plausibility
        }
        df = pd.DataFrame(data)
        current_schema = load_schema(temp_schema_file)
        discovered = discover_schema(df, current_schema)

        with pytest.raises(RuntimeError) as exc_info:
            validate_schema(df, discovered)

        assert "Missing required rubric dimensions" in str(exc_info.value)
        assert "Realism" in str(exc_info.value)

    def test_validate_schema_missing_student_scalar(self, temp_schema_file, sample_dataframe):
        # Remove student_scalar column
        df = sample_dataframe.drop(columns=["student_scalar"])
        current_schema = load_schema(temp_schema_file)
        discovered = discover_schema(df, current_schema)

        # Should raise because student_scalar is expected but not found
        with pytest.raises(RuntimeError) as exc_info:
            validate_schema(df, discovered)
        
        assert "Student scalar" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    def test_discover_schema_types(self, temp_schema_file, sample_dataframe):
        current_schema = load_schema(temp_schema_file)
        discovered = discover_schema(sample_dataframe, current_schema)

        assert "column_types" in discovered
        assert "prompt" in discovered["column_types"]
        assert discovered["column_types"]["prompt"] == "object"

    def test_validate_schema_no_human_annotations_list(self, temp_schema_file):
        # Test when human_annotations is not a list in mapping
        data = {
            "prompt": ["test"],
            "teacher_logits": [[0.1]],
            "student_scalar": [0.5],
            "human_annotation_Alignment": [0.9],
            "human_annotation_Realism": [0.8],
            "human_annotation_Aesthetics": [0.7],
            "human_annotation_Plausibility": [0.6],
        }
        df = pd.DataFrame(data)
        current_schema = load_schema(temp_schema_file)
        
        # Manually set mapping to have a single string instead of list for testing
        discovered = discover_schema(df, current_schema)
        discovered["logical_field_mapping"]["human_annotations"] = "human_annotation_Alignment"
        
        # Should still pass validation as it handles the string case
        result = validate_schema(df, discovered)
        assert result is True

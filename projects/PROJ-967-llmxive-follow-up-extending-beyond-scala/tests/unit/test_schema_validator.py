import pytest
import pandas as pd
import yaml
import tempfile
import os
from pathlib import Path

# We need to import the functions from the script.
# Since the script is a standalone file, we can import it as a module if we add the parent to path,
# but for testing purposes, we will replicate the logic or import directly if possible.
# To avoid circular imports or path issues in a test environment, we will test the logic directly
# by importing the functions if they are exposed, or by mocking the file system.

# For this task, we assume the code/schema_validator.py is the module.
# We will test the inference and validation logic.

def test_infer_actual_schema():
    """Test schema inference on a mock DataFrame."""
    import sys
    from code.schema_validator import infer_actual_schema

    data = {
        "image_path": ["img1.jpg", "img2.jpg"],
        "species_id": [1, 2],
        "prompt_text": ["A cat", "A dog"],
        "teacher_scores": [[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]],
        "student_scalar": [0.25, 0.65],
        "human_annotations": [[0.9, 0.8, 0.7, 0.6], [0.4, 0.3, 0.2, 0.1]],
    }
    df = pd.DataFrame(data)

    schema = infer_actual_schema(df)

    assert schema["version"] == 1.0
    assert len(schema["fields"]) == 6
    field_names = [f["name"] for f in schema["fields"]]
    assert "image_path" in field_names
    assert "teacher_scores" in field_names
    assert schema["fields"][3]["type"] == "list[float]"  # teacher_scores
    assert schema["fields"][5]["type"] == "list[float]"  # human_annotations

def test_validate_schema_missing_column():
    """Test validation fails when a required column is missing."""
    import sys
    from code.schema_validator import validate_schema

    actual_schema = {
        "version": 1.0,
        "fields": [
            {"name": "image_path", "type": "string"},
            {"name": "species_id", "type": "integer"},
            # Missing prompt_text, teacher_scores, etc.
        ],
    }
    provisional_schema = {
        "version": 1.0,
        "fields": [
            {"name": "image_path", "type": "string"},
            {"name": "species_id", "type": "integer"},
            {"name": "prompt_text", "type": "string"},
            {"name": "teacher_scores", "type": "list[float]"},
            {"name": "student_scalar", "type": "float"},
            {"name": "human_annotations", "type": "list[float]"},
        ],
    }
    df = pd.DataFrame({"image_path": ["a"], "species_id": [1]})

    is_valid, discrepancies = validate_schema(actual_schema, provisional_schema, df)

    assert not is_valid
    assert any("Missing required column: prompt_text" in d for d in discrepancies)
    assert any("Missing required column: teacher_scores" in d for d in discrepancies)

def test_validate_schema_correct():
    """Test validation passes when schema matches."""
    import sys
    from code.schema_validator import validate_schema

    actual_schema = {
        "version": 1.0,
        "fields": [
            {"name": "image_path", "type": "string"},
            {"name": "species_id", "type": "integer"},
            {"name": "prompt_text", "type": "string"},
            {"name": "teacher_scores", "type": "list[float]"},
            {"name": "student_scalar", "type": "float"},
            {"name": "human_annotations", "type": "list[float]"},
        ],
    }
    provisional_schema = actual_schema
    df = pd.DataFrame({"image_path": ["a"], "species_id": [1], "prompt_text": ["b"], "teacher_scores": [[1,2,3,4]], "student_scalar": [0.5], "human_annotations": [[1,2,3,4]]})

    is_valid, discrepancies = validate_schema(actual_schema, provisional_schema, df)

    assert is_valid
    assert not any("Missing required" in d for d in discrepancies)
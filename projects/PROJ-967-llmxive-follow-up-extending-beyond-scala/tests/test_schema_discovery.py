import pytest
import pandas as pd
import yaml
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from schema_discovery import (
    load_schema,
    save_schema,
    load_dataset,
    discover_schema,
    validate_schema,
    update_contract,
    LOGICAL_FIELDS,
    RUBRIC_DIMENSIONS
)

@pytest.fixture
def temp_schema_file(tmp_path):
    schema = {
        "prompt": {"type": "string"},
        "teacher_scores": {"type": "object"}
    }
    file_path = tmp_path / "test_schema.yaml"
    with open(file_path, "w") as f:
        yaml.dump(schema, f)
    return file_path

@pytest.fixture
def sample_dataframe():
    data = {
        "prompt": ["What is this?", "Describe the image"],
        "image_url": ["http://img1.jpg", "http://img2.jpg"],
        "teacher_scores": [
            {"Alignment": 0.9, "Realism": 0.8, "Aesthetics": 0.7, "Plausibility": 0.85},
            {"Alignment": 0.5, "Realism": 0.6, "Aesthetics": 0.4, "Plausibility": 0.55}
        ],
        "student_scalar": [0.8, 0.45],
        "human_annotations": [
            {"Alignment": 0.95, "Realism": 0.82, "Aesthetics": 0.75, "Plausibility": 0.88},
            {"Alignment": 0.55, "Realism": 0.65, "Aesthetics": 0.45, "Plausibility": 0.58}
        ],
        "primary_dimension": ["Alignment", "Realism"]
    }
    return pd.DataFrame(data)

def test_load_schema(temp_schema_file):
    schema = load_schema(temp_schema_file)
    assert "prompt" in schema
    assert schema["prompt"]["type"] == "string"

def test_discover_schema_match(sample_dataframe):
    # Mock logger
    logger = MagicMock()
    discovered = discover_schema(sample_dataframe, logger)

    assert discovered["prompt"]["detected"] is True
    assert discovered["prompt"]["matched_column"] == "prompt"
    
    assert discovered["teacher_scores"]["detected"] is True
    assert discovered["teacher_scores"]["matched_column"] == "teacher_scores"
    assert discovered["teacher_scores"]["structure"] == "nested_dict"
    assert set(discovered["teacher_scores"]["keys"]) == {"Alignment", "Realism", "Aesthetics", "Plausibility"}

    assert discovered["student_scalar"]["detected"] is True
    assert discovered["human_annotations"]["detected"] is True
    assert discovered["primary_dimension"]["detected"] is True

def test_discover_schema_missing_field(sample_dataframe):
    # Remove a column
    df_missing = sample_dataframe.drop(columns=["primary_dimension"])
    logger = MagicMock()
    discovered = discover_schema(df_missing, logger)

    assert discovered["primary_dimension"]["detected"] is False
    assert discovered["primary_dimension"]["missing"] is True

def test_validate_schema_valid(sample_dataframe):
    logger = MagicMock()
    discovered = discover_schema(sample_dataframe, logger)
    assert validate_schema(discovered, logger) is True

def test_validate_schema_invalid(sample_dataframe):
    # Force a critical field to be missing in discovery
    discovered = {
        "prompt": {"detected": True},
        "teacher_scores": {"detected": False}, # Critical missing
        "student_scalar": {"detected": True},
        "human_annotations": {"detected": True},
        "primary_dimension": {"detected": True}
    }
    logger = MagicMock()
    assert validate_schema(discovered, logger) is False
    logger.error.assert_called()

def test_save_and_load_schema_cycle(tmp_path):
    schema = {"test": {"key": "value"}}
    file_path = tmp_path / "cycle_test.yaml"
    
    save_schema(schema, file_path)
    assert file_path.exists()
    
    loaded = load_schema(file_path)
    assert loaded == schema

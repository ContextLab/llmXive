import pytest
import pandas as pd
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from descriptors import load_schema, validate_schema


def test_load_schema(tmp_path):
    """Test schema loading."""
    schema = {
        "required_columns": ["formula", "formation_energy_per_atom"],
    }
    schema_path = tmp_path / "schema.json"
    with open(schema_path, "w") as f:
        json.dump(schema, f)

    loaded = load_schema(schema_path)
    assert loaded == schema


def test_validate_schema_valid():
    """Test validation with valid DataFrame."""
    schema = {"required_columns": ["a", "b"]}
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert validate_schema(df, schema) is True


def test_validate_schema_missing_column():
    """Test validation with missing column."""
    schema = {"required_columns": ["a", "b"]}
    df = pd.DataFrame({"a": [1, 2]})
    assert validate_schema(df, schema) is False

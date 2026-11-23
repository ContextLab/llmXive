import json
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from validate_schema import validate_schema, SchemaValidationError


def test_valid_schema(tmp_path):
    input_path = tmp_path / "data.csv"
    output_path = tmp_path / "schema_validation.json"
    pd.DataFrame({
        "year": [2010, 2011],
        "effect_size": [0.5, 0.6],
        "sample_size": [50, 60],
        "field": ["psych", "psych"],
    }).to_csv(input_path, index=False)

    result = validate_schema(str(input_path), str(output_path))

    assert result["status"] == "valid"
    with open(output_path) as f:
        report = json.load(f)
    assert report["status"] == "valid"
    assert set(["year", "effect_size", "sample_size", "field"]).issubset(report["columns_found"])
    assert "missing_columns" not in report


def test_missing_column_raises(tmp_path):
    input_path = tmp_path / "data.csv"
    output_path = tmp_path / "schema_validation.json"
    pd.DataFrame({
        "year": [2010],
        "effect_size": [0.5],
        "field": ["psych"],
    }).to_csv(input_path, index=False)

    with pytest.raises(SchemaValidationError):
        validate_schema(str(input_path), str(output_path))

    with open(output_path) as f:
        report = json.load(f)
    assert report["status"] == "invalid"
    assert report["missing_columns"] == ["sample_size"]


def test_missing_input_raises(tmp_path):
    input_path = tmp_path / "nonexistent.csv"
    output_path = tmp_path / "out.json"
    with pytest.raises((FileNotFoundError, ValueError)):
        validate_schema(str(input_path), str(output_path))
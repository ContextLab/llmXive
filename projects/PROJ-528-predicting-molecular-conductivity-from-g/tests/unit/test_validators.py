"""
Basic sanity checks for the ``code.validators`` CLI.
"""

import json
import os
import tempfile

import pandas as pd
import pytest

from code.validators import validate_file

def test_validate_csv_success(tmp_path):
    csv_path = tmp_path / "data.csv"
    df = pd.DataFrame({"smiles": ["C"], "atom_count": [1]})
    df.to_csv(csv_path, index=False)

    schema = {
        "type": "object",
        "required": ["smiles", "atom_count"],
    }

    schema_path = tmp_path / "schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f)

    assert validate_file(str(csv_path), str(schema_path)) is True

def test_validate_csv_missing_column(tmp_path):
    csv_path = tmp_path / "data.csv"
    df = pd.DataFrame({"smiles": ["C"]})
    df.to_csv(csv_path, index=False)

    schema = {
        "type": "object",
        "required": ["smiles", "atom_count"],
    }

    schema_path = tmp_path / "schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f)

    assert validate_file(str(csv_path), str(schema_path)) is False
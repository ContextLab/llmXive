"""
Unit tests to validate that the JSON Schema files in the contracts directory
can be loaded without errors using PyYAML's safe_load.
"""

import os
from pathlib import Path

import yaml
import pytest


@pytest.fixture
def contracts_dir() -> Path:
    """
    Return the absolute path to the project's contracts directory.
    """
    # This file lives in tests/unit/, so go up two levels to the project root
    return Path(__file__).resolve().parents[2] / "contracts"


def test_dataset_schema_load(contracts_dir: Path):
    """
    Ensure that contracts/dataset.schema.yaml is valid YAML and loads to a dict.
    """
    schema_path = contracts_dir / "dataset.schema.yaml"
    assert schema_path.is_file(), f"Schema file not found: {schema_path}"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    assert isinstance(schema, dict), "Loaded dataset schema is not a dict"


def test_output_schema_load(contracts_dir: Path):
    """
    Ensure that contracts/output.schema.yaml is valid YAML and loads to a dict.
    """
    schema_path = contracts_dir / "output.schema.yaml"
    assert schema_path.is_file(), f"Schema file not found: {schema_path}"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    assert isinstance(schema, dict), "Loaded output schema is not a dict"
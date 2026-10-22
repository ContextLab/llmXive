"""
Contract tests for the descriptor dataset.
These tests verify that the required files exist and that the
descriptor parquet file conforms to the expected schema.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from tests.contract.validators import (
    DESCRIPTORS_PARQUET,
    DESCRIPTOR_NAMES_JSON,
    validate_descriptor_frame,
)

def test_descriptor_names_json_exists_and_is_list():
    """The descriptor_names.json file must exist and contain a JSON list."""
    assert DESCRIPTOR_NAMES_JSON.is_file(), f"{DESCRIPTOR_NAMES_JSON} does not exist"
    with open(DESCRIPTOR_NAMES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "descriptor_names.json must contain a list of strings"
    # Ensure every entry is a string
    assert all(isinstance(name, str) for name in data), "All descriptor names must be strings"

def test_descriptors_parquet_exists():
    """The descriptors.parquet file must exist."""
    assert DESCRIPTORS_PARQUET.is_file(), f"{DESCRIPTORS_PARQUET} does not exist"

def test_descriptors_parquet_schema():
    """Validate that the descriptor DataFrame contains required metadata and descriptor columns."""
    df = pd.read_parquet(DESCRIPTORS_PARQUET)
    # This will raise ValueError if schema is invalid
    descriptor_cols = validate_descriptor_frame(df)
    # Basic sanity: there should be at least 200 descriptor columns
    assert len(descriptor_cols) >= 200, f"Expected >=200 descriptor columns, found {len(descriptor_cols)}"

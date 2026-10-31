"""
Unit test for the ``fetch_materials`` data acquisition script.

The test checks that:
1. The parquet file ``data/raw/pcm.parquet`` exists after running the script.
2. The file contains at least ``MIN_ROWS`` (5 000) records.
3. Every row conforms to ``contracts/dataset.schema.yaml``.
4. The script does not exceed the memory limit defined in the configuration
   (checked via ``psutil``).
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd
import psutil
import pytest
import yaml

# Import the script's main function
from code.data.fetch_materials import main as fetch_main
from config import get_memory_limit_gb

# Path constants
OUTPUT_PARQUET = Path("data/raw/pcm.parquet")
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")
MIN_ROWS = 5_000

def _load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def _validate_row(row: dict, schema: dict):
    # Very lightweight validation: ensure required keys exist and types match.
    for key, prop in schema.get("properties", {}).items():
        if key not in row:
            return False, f"Missing key {key}"
        expected = prop.get("type")
        if expected == "string" and not isinstance(row[key], str):
            return False, f"Key {key} expected string"
        if expected == "integer" and not isinstance(row[key], int):
            return False, f"Key {key} expected integer"
        if expected == "number" and not isinstance(row[key], (int, float)):
            return False, f"Key {key} expected number"
        if expected == "array" and not isinstance(row[key], list):
            return False, f"Key {key} expected list"
    return True, ""

@pytest.fixture(scope="module")
def run_fetch():
    """Run the fetch script once for the test module."""
    # Ensure a clean state: delete existing file if present
    if OUTPUT_PARQUET.is_file():
        OUTPUT_PARQUET.unlink()
    # Execute the script
    fetch_main()
    yield
    # Cleanup after tests (optional)
    if OUTPUT_PARQUET.is_file():
        OUTPUT_PARQUET.unlink()

def test_parquet_exists(run_fetch):
    assert OUTPUT_PARQUET.is_file(), "Parquet output file was not created."

def test_row_count(run_fetch):
    df = pd.read_parquet(OUTPUT_PARQUET)
    assert len(df) >= MIN_ROWS, f"Expected at least {MIN_ROWS} rows, got {len(df)}."

def test_schema_conformance(run_fetch):
    df = pd.read_parquet(OUTPUT_PARQUET)
    schema = _load_schema()
    for _, row in df.iterrows():
        ok, msg = _validate_row(row.to_dict(), schema)
        assert ok, f"Schema validation failed: {msg}"

def test_memory_usage(run_fetch):
    # The script should not exceed the configured memory limit.
    mem_limit_gb = get_memory_limit_gb()
    process = psutil.Process()
    mem_used_gb = process.memory_info().rss / (1024 ** 3)
    assert mem_used_gb <= mem_limit_gb, (
        f"Memory usage {mem_used_gb:.2f} GB exceeds limit of {mem_limit_gb} GB"
    )
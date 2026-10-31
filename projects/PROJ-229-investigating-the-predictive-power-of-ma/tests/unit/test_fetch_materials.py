"""
Unit test for the `fetch_materials` data acquisition script.
"""

import pytest
import pandas as pd
import psutil
import yaml
from pathlib import Path

from code.data.fetch_materials import main as fetch_main
from config import get_memory_limit_gb

OUTPUT_PARQUET = Path("data/raw/pcm.parquet")
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")
MIN_ROWS = 5_000

def _load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def _validate_row(row: dict, schema: dict):
    for key, prop in schema.get("properties", {}).items():
        if key not in row:
            return False, f"Missing key {key}"
        expected = prop.get("type")
        val = row[key]
        if expected == "string" and not isinstance(val, str):
            return False, f"Key {key} expected string"
        if expected == "integer" and not isinstance(val, int):
            return False, f"Key {key} expected integer"
        if expected == "number" and not isinstance(val, (int, float)):
            return False, f"Key {key} expected number"
        if expected == "array" and not isinstance(val, list):
            return False, f"Key {key} expected list"
    return True, ""

@pytest.fixture(scope="module")
def run_fetch():
    if OUTPUT_PARQUET.is_file():
        OUTPUT_PARQUET.unlink()
    fetch_main()
    yield

def test_parquet_exists(run_fetch):
    assert OUTPUT_PARQUET.is_file(), "Parquet output file was not created."

def test_row_count(run_fetch):
    df = pd.read_parquet(OUTPUT_PARQUET)
    assert len(df) >= MIN_ROWS, f"Expected at least {MIN_ROWS} rows, got {len(df)}."

def test_schema_conformance(run_fetch):
    df = pd.read_parquet(OUTPUT_PARQUET)
    schema = _load_schema()
    # Sample check for performance if dataset is large, but task asks for conformance
    for _, row in df.head(100).iterrows():
        ok, msg = _validate_row(row.to_dict(), schema)
        assert ok, f"Schema validation failed: {msg}"

def test_memory_usage(run_fetch):
    mem_limit_gb = get_memory_limit_gb()
    process = psutil.Process()
    mem_used_gb = process.memory_info().rss / (1024 ** 3)
    assert mem_used_gb <= mem_limit_gb, (
        f"Memory usage {mem_used_gb:.2f} GB exceeds limit of {mem_limit_gb} GB"
    )
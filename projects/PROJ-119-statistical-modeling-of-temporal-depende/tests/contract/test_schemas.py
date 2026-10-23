"""Basic contract validation tests for the cryptocurrency analysis pipeline.

The tests verify that:
  * The raw OHLCV Parquet files exist.
  * The checksums.json file exists and is valid JSON.
  * At least one record from each Parquet file conforms to the ``raw_price``
    JSON schema.
"""

import json
import pathlib

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
import jsonschema

from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_schema(schema_name: str) -> dict:
    """Load a JSON schema from the contracts directory."""
    schema_path = (
        paths.root
        / "specs"
        / "001-statistical-modeling-of-temporal-depende"
        / "contracts"
        / f"{schema_name}.schema.yaml"
    )
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _load_one_record(parquet_path: pathlib.Path) -> dict:
    """Load the first row of a Parquet file as a plain Python dict."""
    table = pq.read_table(parquet_path, use_pandas_metadata=False)
    df = table.to_pandas()
    assert not df.empty, f"{parquet_path} contains no rows"
    record = df.iloc[0].to_dict()
    # Convert numpy scalar types to native Python types for jsonschema
    for k, v in record.items():
        if isinstance(v, (np.generic, np.ndarray)):
            record[k] = v.item() if hasattr(v, "item") else v.tolist()
    return record

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_checksums_file_exists_and_is_valid_json():
    """The checksums.json file must exist and contain a JSON object."""
    checksums_path = paths.data("checksums.json")
    assert checksums_path.is_file(), f"{checksums_path} not found"
    with open(checksums_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict), "checksums.json should contain a JSON object"

def test_raw_ohlcv_files_exist():
    """Both BTC and ETH raw Parquet files must exist."""
    for fname in ("btc_ohlcv.parquet", "eth_ohlcv.parquet"):
        p = paths.data("raw", fname)
        assert p.is_file(), f"Missing raw data file: {p}"

def test_raw_records_conform_to_schema():
    """At least one record from each raw Parquet file must satisfy the schema."""
    schema = _load_schema("raw_price")
    for fname in ("btc_ohlcv.parquet", "eth_ohlcv.parquet"):
        p = paths.data("raw", fname)
        record = _load_one_record(p)
        jsonschema.validate(instance=record, schema=schema)
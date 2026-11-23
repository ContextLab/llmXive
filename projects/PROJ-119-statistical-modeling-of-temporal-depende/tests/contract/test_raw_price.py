import pytest
import pandas as pd
import yaml
import jsonschema
from pathlib import Path
from llmxive_toolkit import paths

SCHEMA_PATH = paths.root / "specs/001-statistical-modeling-of-temporal-depende/contracts/raw_price.schema.yaml"
RAW_FILES = [
    paths.data("raw", "btc_ohlcv.parquet"),
    paths.data("raw", "eth_ohlcv.parquet"),
]

@pytest.fixture
def schema():
    """Load the JSON schema for raw price records."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.mark.parametrize("file_path", RAW_FILES)
def test_raw_price_schema(file_path, schema):
    """Validate that each raw OHLCV parquet file conforms to the schema."""
    assert file_path.exists(), f"Data file missing: {file_path}"
    
    df = pd.read_parquet(file_path)
    
    # Check that all required columns are present
    required_cols = schema["required"]
    for col in required_cols:
        assert col in df.columns, f"Column {col} missing in {file_path}"
    
    # Validate a sample of rows against the schema
    # (Converting to dict for jsonschema validation)
    records = df.to_dict(orient="records")
    assert len(records) > 0, f"File {file_path} is empty"
    
    for i, record in enumerate(records):
        # Validate first 100 and last 100 rows for performance
        if i < 100 or i > (len(records) - 100):
            try:
                jsonschema.validate(instance=record, schema=schema)
            except jsonschema.ValidationError as e:
                pytest.fail(f"Schema validation failed for {file_path} at row {i}: {e.message}")

def test_checksums_exist():
    """Ensure checksums.json was created."""
    checksums_path = paths.data("checksums.json")
    assert checksums_path.exists(), "checksums.json is missing"
    
    import json
    with open(checksums_path, "r") as f:
        data = json.load(f)
        assert "btc_ohlcv.parquet" in data
        assert "eth_ohlcv.parquet" in data
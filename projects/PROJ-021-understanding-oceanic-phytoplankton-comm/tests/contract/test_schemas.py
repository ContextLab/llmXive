"""
Contract tests for schema validation. The original repository already contains
a test for the aligned_dataset schema (T009). This file is kept unchanged
because the current task (T011a) does not introduce new schemas.
"""
import pytest
import yaml
from pathlib import Path
from llmxive_toolkit import paths

def load_schema(schema_name: str) -> dict:
    schema_path = paths.code("specs/001-understanding-oceanic-phytoplankton-comm/contracts", f"{schema_name}.schema.yaml")
    with open(schema_path) as f:
        return yaml.safe_load(f)

def test_aligned_dataset_schema():
    schema = load_schema("aligned_dataset")
    # Basic sanity checks – the schema must define the required fields.
    required_fields = {"lat", "lon", "timestamp", "basin", "temp", "salinity", "nutrients", "chlorophyll_a", "quality_flags"}
    assert "type" in schema and schema["type"] == "object"
    assert "properties" in schema
    assert required_fields.issubset(set(schema["properties"].keys()))
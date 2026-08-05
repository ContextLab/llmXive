"""
Unit tests for data schema definitions (T007).
Validates that schema files exist, are valid YAML, and contain required fields.
"""
import os
import sys
import json
import yaml
import pytest
from pathlib import Path

# Project root for imports
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

def load_schema(filename: str) -> dict:
    """Load a schema file from the contracts directory."""
    schema_path = CONTRACTS_DIR / filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

class TestSchemaExistence:
    def test_waveform_schema_exists(self):
        """Verify waveform.schema.yaml exists."""
        assert (CONTRACTS_DIR / "waveform.schema.yaml").exists()

    def test_result_schema_exists(self):
        """Verify result.schema.yaml exists."""
        assert (CONTRACTS_DIR / "result.schema.yaml").exists()

class TestSchemaSyntax:
    def test_waveform_schema_syntax(self):
        """Verify waveform schema is valid YAML."""
        schema = load_schema("waveform.schema.yaml")
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "properties" in schema

    def test_result_schema_syntax(self):
        """Verify result schema is valid YAML."""
        schema = load_schema("result.schema.yaml")
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "properties" in schema

class TestRequiredFields:
    def test_waveform_schema_required_fields(self):
        """Verify waveform schema defines required top-level fields."""
        schema = load_schema("waveform.schema.yaml")
        required = schema.get("required", [])
        assert "metadata" in required
        assert "waveforms" in required

        # Check metadata required fields
        metadata_props = schema["properties"]["metadata"]["properties"]
        metadata_required = schema["properties"]["metadata"].get("required", [])
        assert "version" in metadata_required
        assert "generated_at" in metadata_required
        assert "seed" in metadata_required
        assert "bit_depths" in metadata_required

        # Check waveform item required fields
        waveform_item = schema["properties"]["waveforms"]["items"]
        item_required = waveform_item.get("required", [])
        assert "signal_id" in item_required
        assert "injection_params" in item_required
        assert "quantization_params" in item_required

    def test_result_schema_required_fields(self):
        """Verify result schema defines required top-level fields."""
        schema = load_schema("result.schema.yaml")
        required = schema.get("required", [])
        assert "metadata" in required
        assert "results" in required

        # Check metadata required fields
        metadata_props = schema["properties"]["metadata"]["properties"]
        metadata_required = schema["properties"]["metadata"].get("required", [])
        assert "version" in metadata_required
        assert "generated_at" in metadata_required

        # Check result item required fields
        result_item = schema["properties"]["results"]["items"]
        item_required = result_item.get("required", [])
        assert "signal_id" in item_required
        assert "inference_status" in item_required
        assert "posterior_summary" in item_required
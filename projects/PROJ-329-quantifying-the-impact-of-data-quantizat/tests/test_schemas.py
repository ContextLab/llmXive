"""
Unit tests for data schemas (waveform.schema.yaml, result.schema.yaml).
Validates schema existence, syntax, and required fields.
"""
import os
import sys
import json
import yaml
import pytest
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"


def load_schema(filename: str) -> dict:
    """Load a YAML schema from the contracts directory."""
    filepath = CONTRACTS_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Schema file not found: {filepath}")
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


class TestWaveformSchema:
    def test_waveform_schema_exists(self):
        """Verify waveform.schema.yaml exists."""
        assert (CONTRACTS_DIR / "waveform.schema.yaml").exists()

    def test_waveform_schema_syntax(self):
        """Verify waveform schema is valid YAML."""
        schema = load_schema("waveform.schema.yaml")
        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "object"

    def test_waveform_schema_required_fields(self):
        """Verify required fields in waveform schema."""
        schema = load_schema("waveform.schema.yaml")
        # Check top-level required fields
        assert "required" in schema
        assert "metadata" in schema["required"]
        assert "signals" in schema["required"]

        # Check metadata required fields
        metadata_props = schema["properties"]["metadata"]
        assert "required" in metadata_props
        required_meta = metadata_props["required"]
        assert "version" in required_meta
        assert "seed" in required_meta
        assert "bit_depths" in required_meta

        # Check signal item required fields
        signals_items = schema["properties"]["signals"]["items"]
        assert "required" in signals_items
        required_sig = signals_items["required"]
        assert "signal_id" in required_sig
        assert "injection_params" in required_sig
        assert "quantization_results" in required_sig


class TestResultSchema:
    def test_result_schema_exists(self):
        """Verify result.schema.yaml exists."""
        assert (CONTRACTS_DIR / "result.schema.yaml").exists()

    def test_result_schema_syntax(self):
        """Verify result schema is valid YAML."""
        schema = load_schema("result.schema.yaml")
        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "object"

    def test_result_schema_required_fields(self):
        """Verify required fields in result schema."""
        schema = load_schema("result.schema.yaml")
        
        # Check top-level required fields
        assert "required" in schema
        assert "metadata" in schema["required"]
        assert "results" in schema["required"]

        # Check results item structure
        results_items = schema["properties"]["results"]["items"]
        assert "required" in results_items
        required_res = results_items["required"]
        assert "signal_id" in required_res
        assert "status" in required_res
        assert "posterior_samples" in required_res or "recovered_params" in required_res
        
        # Verify status enum
        status_def = results_items["properties"]["status"]
        assert "enum" in status_def
        assert "converged" in status_def["enum"]
        assert "failed" in status_def["enum"]
        assert "non_detection" in status_def["enum"]

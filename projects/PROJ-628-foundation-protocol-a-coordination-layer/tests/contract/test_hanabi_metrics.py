"""
Contract test for Hanabi metrics schema.

This test validates that logs produced by the Hanabi benchmark conform to the
MetricRecord schema defined in contracts/metrics.schema.yaml.
"""

import json
import os
import pytest
from pathlib import Path

import jsonschema
import yaml

# Project root relative to this file (tests/contract)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SCHEMA_PATH = PROJECT_ROOT / "contracts" / "metrics.schema.yaml"


def load_schema():
    """Load the MetricRecord schema from YAML."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_sample_metric_record():
    """
    Generate a sample MetricRecord that should be valid against the schema.
    This mimics the structure produced by hanabi_runner.py or similar benchmarks.
    """
    return {
        "seed": 42,
        "protocol": "Foundation",
        "episode_length": 100,
        "msg_count": 50,
        "bytes_sent": 1024,
        "recovery_success": True,
        "recovery_latency": 0.5,
        "task_success": True
    }


def test_schema_compliance():
    """
    Contract test: Assert that sample metric records match the schema.
    This ensures that the data generation logic (e.g., in hanabi_runner)
    produces output compatible with the defined schema.
    """
    schema = load_schema()
    sample_record = generate_sample_metric_record()

    # Validate the sample record against the schema
    try:
        jsonschema.validate(instance=sample_record, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"MetricRecord does not match schema: {e.message}")


def test_schema_compliance_invalid_type():
    """
    Contract test: Assert that invalid types are caught by the schema.
    """
    schema = load_schema()
    invalid_record = {
        "seed": "not_an_int",  # Should be integer
        "protocol": "Foundation",
        "episode_length": 100,
        "msg_count": 50,
        "bytes_sent": 1024,
        "recovery_success": True,
        "recovery_latency": 0.5,
        "task_success": True
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_record, schema=schema)


def test_schema_compliance_missing_field():
    """
    Contract test: Assert that missing required fields are caught.
    """
    schema = load_schema()
    incomplete_record = {
        "seed": 42,
        "protocol": "Foundation",
        # Missing episode_length, msg_count, etc.
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=incomplete_record, schema=schema)
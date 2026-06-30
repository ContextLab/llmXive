"""
Contract test for bandwidth metrics (User Story 3).

Validates that bandwidth-related metrics (bytes_sent, bytes_received,
payload_size) conform to the schema defined in contracts/metrics.schema.yaml.
"""
import json
import os
import pytest
from pathlib import Path

import jsonschema

# Determine the path to the schema file relative to the project root
# The test is in tests/contract/, schema is in contracts/
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "metrics.schema.yaml"


def load_schema(schema_path: Path) -> dict:
    """Load JSON schema from YAML file."""
    try:
        import yaml
        with open(schema_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        pytest.fail("PyYAML is required to load the schema file. Install it via requirements.txt.")


def test_bandwidth_schema_compliance():
    """
    Contract test: Asserts that simulated bandwidth metrics match the schema.

    This test generates synthetic MetricRecord entries that include bandwidth
    fields (bytes_sent, bytes_received, payload_size) and validates them against
    the official schema. It ensures that:
    1. The schema exists and is valid JSON/YAML.
    2. Sample data containing bandwidth metrics is structurally correct.
    3. The data passes jsonschema validation.
    """
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. Ensure T005 (MetricRecord schema) is completed.")

    schema = load_schema(SCHEMA_PATH)

    # Validate schema structure itself
    if "properties" not in schema:
        pytest.fail("Schema must contain a 'properties' key.")

    required_fields = ["bytes_sent", "bytes_received", "payload_size"]
    schema_props = schema.get("properties", {})

    # Verify that bandwidth-related fields are defined in the schema
    for field in required_fields:
        if field not in schema_props:
            pytest.fail(f"Schema is missing required bandwidth field: '{field}'. "
                        f"Please update contracts/metrics.schema.yaml to include bandwidth metrics.")

    # Generate synthetic test data representing a valid MetricRecord with bandwidth info
    # This mimics the output of benchmarks (hanabi_runner, spear_runner, etc.)
    test_records = [
        {
            "seed": 42,
            "protocol": "foundation",
            "episode_length": 100,
            "msg_count": 50,
            "bytes_sent": 10240,      # 10 KB
            "bytes_received": 9216,    # 9 KB
            "payload_size": 256,       # Avg payload size in bytes
            "recovery_success": True,
            "recovery_latency": 0.5,
            "task_success": True,
            "timestamp": "2026-01-01T00:00:00Z"
        },
        {
            "seed": 43,
            "protocol": "native_direct",
            "episode_length": 110,
            "msg_count": 60,
            "bytes_sent": 15360,
            "bytes_received": 14336,
            "payload_size": 256,
            "recovery_success": False,
            "recovery_latency": None,
            "task_success": True,
            "timestamp": "2026-01-01T00:01:00Z"
        },
        {
            "seed": 44,
            "protocol": "foundation",
            "episode_length": 95,
            "msg_count": 45,
            "bytes_sent": 8192,
            "bytes_received": 8192,
            "payload_size": 256,
            "recovery_success": True,
            "recovery_latency": 0.4,
            "task_success": True,
            "timestamp": "2026-01-01T00:02:00Z"
        }
    ]

    # Validate each record against the schema
    for i, record in enumerate(test_records):
        try:
            jsonschema.validate(instance=record, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            pytest.fail(
                f"MetricRecord #{i+1} failed schema validation: {e.message}. "
                f"Record: {record}"
            )

    # Additional explicit checks for bandwidth logic constraints (if defined in schema)
    # e.g., bytes_sent >= 0, payload_size > 0
    for i, record in enumerate(test_records):
        if record["bytes_sent"] < 0:
            pytest.fail(f"Record #{i+1} has negative bytes_sent: {record['bytes_sent']}")
        if record["bytes_received"] < 0:
            pytest.fail(f"Record #{i+1} has negative bytes_received: {record['bytes_received']}")
        if record["payload_size"] <= 0:
            pytest.fail(f"Record #{i+1} has invalid payload_size: {record['payload_size']}")

    print("✓ All bandwidth metrics conform to the schema in contracts/metrics.schema.yaml")
    print(f"✓ Validated {len(test_records)} synthetic records with fields: {required_fields}")
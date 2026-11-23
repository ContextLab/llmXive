"""
Unit tests for ExecutionRun schema validation.
Validates that YAML schema matches Pydantic model constraints.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import pytest
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from orchestrator.models import ExecutionRun, NodeStatus, TaskStatus


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load YAML schema from file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_json_against_schema(json_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Basic JSON schema validation.
    Note: For production, use jsonschema library, but for unit tests we verify key constraints manually.
    """
    # Check required fields
    for field in schema.get('required', []):
        if field not in json_data:
            raise AssertionError(f"Missing required field: {field}")

    # Check properties
    props = schema.get('properties', {})
    for key, value in json_data.items():
        if key not in props:
            if schema.get('additionalProperties') is False:
                raise AssertionError(f"Unexpected property: {key}")
            continue

        prop_schema = props[key]

        # Type checking
        expected_type = prop_schema.get('type')
        if expected_type == 'string':
            if not isinstance(value, str):
                raise AssertionError(f"Field {key} must be string, got {type(value)}")
        elif expected_type == 'number':
            if not isinstance(value, (int, float)):
                raise AssertionError(f"Field {key} must be number, got {type(value)}")
        elif expected_type == 'integer':
            if not isinstance(value, int):
                raise AssertionError(f"Field {key} must be integer, got {type(value)}")
        elif expected_type == 'boolean':
            if not isinstance(value, bool):
                raise AssertionError(f"Field {key} must be boolean, got {type(value)}")
        elif expected_type == 'array':
            if not isinstance(value, list):
                raise AssertionError(f"Field {key} must be array, got {type(value)}")
            # Check minItems
            if 'minItems' in prop_schema and len(value) < prop_schema['minItems']:
                raise AssertionError(f"Field {key} must have at least {prop_schema['minItems']} items")
        elif expected_type == 'object':
            if not isinstance(value, dict):
                raise AssertionError(f"Field {key} must be object, got {type(value)}")

        # Enum checking
        if 'enum' in prop_schema:
            if value not in prop_schema['enum']:
                raise AssertionError(f"Field {key} must be one of {prop_schema['enum']}, got {value}")

        # Pattern checking
        if 'pattern' in prop_schema and isinstance(value, str):
            import re
            if not re.match(prop_schema['pattern'], value):
                raise AssertionError(f"Field {key} does not match pattern {prop_schema['pattern']}, got {value}")

    return True


class TestExecutionRunSchema:
    """Tests for ExecutionRun schema validation."""

    @pytest.fixture
    def schema(self):
        """Load the ExecutionRun schema."""
        schema_path = PROJECT_ROOT / "contracts" / "execution_run_schema.yaml"
        assert schema_path.exists(), f"Schema file not found: {schema_path}"
        return load_schema(str(schema_path))

    @pytest.fixture
    def valid_run_data(self) -> Dict[str, Any]:
        """Generate valid ExecutionRun data."""
        return {
            "run_id": "run_12345678",
            "start_time": "2023-10-01T12:00:00Z",
            "status": "running",
            "nodes": [
                {
                    "node_id": "node_aabbccdd",
                    "hostname": "node1.local",
                    "status": "available",
                    "hardware_spec": {"cpu": "Intel i7", "ram_gb": 32}
                }
            ],
            "task_chunks": [
                {
                    "chunk_id": "chunk_11223344",
                    "status": "pending",
                    "assigned_node_id": "node_aabbccdd",
                    "start_time": None
                }
            ],
            "config_snapshot": {
                "granularity": "medium",
                "network_params": {
                    "target_latency_ms": 10.0,
                    "target_packet_loss": 0.01
                }
            },
            "config_snapshot": {
                "granularity": "medium",
                "network_params": {
                    "target_latency_ms": 10.0,
                    "target_packet_loss": 0.01
                }
            },
            "error_code": None
        }

    def test_schema_file_exists(self, schema):
        """Verify schema file is valid YAML."""
        assert schema is not None
        assert 'properties' in schema

    def test_valid_run_passes_schema(self, schema, valid_run_data):
        """Valid data should pass schema validation."""
        # Validate against JSON schema logic
        validate_json_against_schema(valid_run_data, schema)

    def test_valid_run_passes_pydantic(self, valid_run_data):
        """Valid data should instantiate Pydantic model."""
        # Convert to Pydantic model
        run = ExecutionRun(
            run_id=valid_run_data["run_id"],
            start_time=datetime.fromisoformat(valid_run_data["start_time"].replace('Z', '+00:00')),
            status=valid_run_data["status"],
            nodes=[{
                "node_id": n["node_id"],
                "hostname": n["hostname"],
                "status": n["status"],
                "hardware_spec": n.get("hardware_spec")
            } for n in valid_run_data["nodes"]],
            task_chunks=[{
                "chunk_id": c["chunk_id"],
                "status": c["status"],
                "assigned_node_id": c["assigned_node_id"],
                "start_time": c["start_time"]
            } for c in valid_run_data["task_chunks"]],
            config_snapshot=valid_run_data["config_snapshot"]
        )
        assert run is not None
        assert run.run_id == "run_12345678"

    def test_missing_required_field(self, schema):
        """Missing required field should fail validation."""
        invalid_data = {
            "run_id": "run_12345678",
            # Missing start_time
            "status": "running",
            "nodes": [],
            "task_chunks": [],
            "config_snapshot": {"granularity": "medium", "network_params": {}}
        }
        with pytest.raises(AssertionError, match="Missing required field: start_time"):
            validate_json_against_schema(invalid_data, schema)

    def test_invalid_enum_value(self, schema):
        """Invalid enum value should fail validation."""
        invalid_data = {
            "run_id": "run_12345678",
            "start_time": "2023-10-01T12:00:00Z",
            "status": "invalid_status",  # Not in enum
            "nodes": [],
            "task_chunks": [],
            "config_snapshot": {"granularity": "medium", "network_params": {}}
        }
        with pytest.raises(AssertionError, match="must be one of"):
            validate_json_against_schema(invalid_data, schema)

    def test_invalid_pattern(self, schema):
        """Invalid ID pattern should fail validation."""
        invalid_data = {
            "run_id": "invalid_id",  # Should match ^run_[0-9a-f]{8}$
            "start_time": "2023-10-01T12:00:00Z",
            "status": "running",
            "nodes": [],
            "task_chunks": [],
            "config_snapshot": {"granularity": "medium", "network_params": {}}
        }
        with pytest.raises(AssertionError, match="does not match pattern"):
            validate_json_against_schema(invalid_data, schema)

    def test_empty_nodes_array(self, schema):
        """Empty nodes array should fail (minItems: 1)."""
        invalid_data = {
            "run_id": "run_12345678",
            "start_time": "2023-10-01T12:00:00Z",
            "status": "running",
            "nodes": [],  # Violates minItems
            "task_chunks": [],
            "config_snapshot": {"granularity": "medium", "network_params": {}}
        }
        with pytest.raises(AssertionError, match="must have at least 1 items"):
            validate_json_against_schema(invalid_data, schema)

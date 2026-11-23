"""
Contract tests for state.yaml schema validation.
Ensures the state file produced by T037 adheres to the expected structure.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

import yaml

from code.utils import validate_json_schema

# Define the expected schema for state.yaml
STATE_SCHEMA = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string"},
        "updated_at": {"type": "string"},
        "artifact_count": {"type": "number"},
        "missing_count": {"type": "number"},
        "artifacts": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "exists": {"type": "boolean"},
                    "hash": {"type": ["string", "null"]},
                    "size_bytes": {"type": ["number", "null"]},
                    "last_modified": {"type": ["string", "null"]},
                    "reason": {"type": ["string", "null"]}
                },
                "required": ["exists"]
            }
        }
    },
    "required": ["updated_at", "artifact_count", "missing_count", "artifacts"]
}

class TestStateSchema(TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "state.yaml"

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_state_schema_structure(self):
        """Test that a valid state file conforms to the schema."""
        valid_state = {
            "project_id": "PROJ-312-test",
            "updated_at": "2024-01-01T00:00:00Z",
            "artifact_count": 1,
            "missing_count": 0,
            "artifacts": {
                "data/test.txt": {
                    "exists": True,
                    "hash": "abc123",
                    "size_bytes": 100,
                    "last_modified": "2024-01-01T00:00:00Z"
                }
            }
        }

        with open(self.state_file, "w") as f:
            yaml.dump(valid_state, f)

        # Load and validate
        with open(self.state_file, "r") as f:
            loaded_state = yaml.safe_load(f)

        # Convert to JSON for schema validation
        json_state = json.loads(json.dumps(loaded_state))
        
        # Validate against schema
        is_valid = validate_json_schema(json_state, STATE_SCHEMA)
        self.assertTrue(is_valid, "Valid state should pass schema validation")

    def test_state_schema_missing_artifact(self):
        """Test state file with missing artifact entries."""
        valid_state = {
            "updated_at": "2024-01-01T00:00:00Z",
            "artifact_count": 0,
            "missing_count": 1,
            "artifacts": {
                "data/missing.txt": {
                    "exists": False,
                    "hash": None,
                    "size_bytes": None,
                    "last_modified": None,
                    "reason": "File not found"
                }
            }
        }

        with open(self.state_file, "w") as f:
            yaml.dump(valid_state, f)

        with open(self.state_file, "r") as f:
            loaded_state = yaml.safe_load(f)

        json_state = json.loads(json.dumps(loaded_state))
        is_valid = validate_json_schema(json_state, STATE_SCHEMA)
        self.assertTrue(is_valid, "State with missing artifacts should pass schema validation")

    def test_state_schema_required_fields(self):
        """Test that missing required fields fail validation."""
        invalid_state = {
            "updated_at": "2024-01-01T00:00:00Z",
            # Missing artifact_count, missing_count, artifacts
        }

        is_valid = validate_json_schema(invalid_state, STATE_SCHEMA)
        self.assertFalse(is_valid, "State missing required fields should fail validation")

    def test_state_schema_artifact_fields(self):
        """Test that artifact entries must have 'exists' field."""
        invalid_artifact_state = {
            "updated_at": "2024-01-01T00:00:00Z",
            "artifact_count": 1,
            "missing_count": 0,
            "artifacts": {
                "data/test.txt": {
                    # Missing 'exists' field
                    "hash": "abc123"
                }
            }
        }

        is_valid = validate_json_schema(invalid_artifact_state, STATE_SCHEMA)
        self.assertFalse(is_valid, "Artifact entry missing 'exists' should fail validation")

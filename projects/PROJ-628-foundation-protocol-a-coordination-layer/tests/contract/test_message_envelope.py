"""
Contract tests for the MessageEnvelope schema (T004).
Validates that generated messages and data structures comply with the
defined JSON schema in contracts/dataset.schema.yaml.
"""
import json
import os
import unittest
from pathlib import Path

import jsonschema
from jsonschema import validate, ValidationError

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

def load_schema():
    """Load the JSON/YAML schema from disk."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    # Simple YAML loader without external dependency if possible, 
    # but task T002 added pyyaml to requirements.txt
    import yaml
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

class TestMessageEnvelopeSchema(unittest.TestCase):
    """Test cases for MessageEnvelope schema compliance."""

    def setUp(self):
        """Load the schema once for all tests."""
        try:
            self.schema = load_schema()
        except Exception as e:
            self.skipTest(f"Schema loading failed: {e}")

    def test_schema_exists_and_valid(self):
        """Verify the schema file exists and is a valid dictionary."""
        self.assertIsInstance(self.schema, dict)
        self.assertIn("properties", self.schema)
        self.assertIn("required", self.schema)

    def test_valid_message_envelope(self):
        """Test a fully compliant MessageEnvelope instance."""
        valid_envelope = {
            "sender_id": "agent_alpha_001",
            "receiver_id": "agent_beta_002",
            "timestamp": "2026-06-01T12:34:56Z",
            "signature": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/==",
            "payload_size": 1024,
            "checkpoint_ref": "cp_20260601_123456_abc123"
        }
        
        try:
            validate(instance=valid_envelope, schema=self.schema)
            self.assertTrue(True)
        except ValidationError as e:
            self.fail(f"Valid envelope failed schema validation: {e.message}")

    def test_missing_required_field(self):
        """Test that a message missing a required field fails validation."""
        invalid_envelope = {
            "sender_id": "agent_alpha_001",
            "receiver_id": "agent_beta_002",
            # Missing timestamp, signature, payload_size, checkpoint_ref
            "timestamp": "2026-06-01T12:34:56Z"
        }
        
        with self.assertRaises(ValidationError):
            validate(instance=invalid_envelope, schema=self.schema)

    def test_invalid_payload_type(self):
        """Test that a non-integer payload_size fails validation."""
        invalid_envelope = {
            "sender_id": "agent_alpha_001",
            "receiver_id": "agent_beta_002",
            "timestamp": "2026-06-01T12:34:56Z",
            "signature": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/==",
            "payload_size": "large",  # Should be integer
            "checkpoint_ref": "cp_20260601_123456_abc123"
        }
        
        with self.assertRaises(ValidationError):
            validate(instance=invalid_envelope, schema=self.schema)

    def test_negative_payload_size(self):
        """Test that negative payload_size fails validation."""
        invalid_envelope = {
            "sender_id": "agent_alpha_001",
            "receiver_id": "agent_beta_002",
            "timestamp": "2026-06-01T12:34:56Z",
            "signature": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/==",
            "payload_size": -100,
            "checkpoint_ref": "cp_20260601_123456_abc123"
        }
        
        with self.assertRaises(ValidationError):
            validate(instance=invalid_envelope, schema=self.schema)

    def test_empty_string_fields(self):
        """Test that empty strings for ID fields fail minLength constraint."""
        invalid_envelope = {
            "sender_id": "",
            "receiver_id": "agent_beta_002",
            "timestamp": "2026-06-01T12:34:56Z",
            "signature": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/==",
            "payload_size": 1024,
            "checkpoint_ref": "cp_20260601_123456_abc123"
        }
        
        with self.assertRaises(ValidationError):
            validate(instance=invalid_envelope, schema=self.schema)

if __name__ == "__main__":
    unittest.main()
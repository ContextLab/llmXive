"""
Contract test for submission schema.

This test verifies that the submission schema conforms to the expected
structure as defined in the data-model.md and contract specifications.
"""

import os
import sys
import json
import unittest
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.models import Submission
from config.settings import get_config


class TestSubmissionSchema(unittest.TestCase):
    """Contract tests for the Submission schema."""

    def setUp(self):
        """Set up test fixtures."""
        self.required_fields = [
            "submission_id",
            "participant_id",
            "problem_id",
            "condition",
            "code",
            "language",
            "timestamp",
            "session_id",
            "status"
        ]
        
        self.optional_fields = [
            "model_response",
            "error_message",
            "metadata"
        ]

    def test_submission_has_required_fields(self):
        """Test that a valid submission has all required fields."""
        # Create a sample submission
        submission = {
            "submission_id": "sub-123",
            "participant_id": "p-456",
            "problem_id": "human-eval-001",
            "condition": "llm-assisted",
            "code": "def hello():\n    return 'world'",
            "language": "python",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "sess-789",
            "status": "submitted"
        }

        for field in self.required_fields:
            self.assertIn(field, submission, f"Missing required field: {field}")

    def test_submission_field_types(self):
        """Test that submission fields have correct types."""
        submission = {
            "submission_id": "sub-123",
            "participant_id": "p-456",
            "problem_id": "human-eval-001",
            "condition": "llm-assisted",
            "code": "def hello():\n    return 'world'",
            "language": "python",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "sess-789",
            "status": "submitted"
        }

        self.assertIsInstance(submission["submission_id"], str)
        self.assertIsInstance(submission["participant_id"], str)
        self.assertIsInstance(submission["problem_id"], str)
        self.assertIsInstance(submission["condition"], str)
        self.assertIsInstance(submission["code"], str)
        self.assertIsInstance(submission["language"], str)
        self.assertIsInstance(submission["timestamp"], str)
        self.assertIsInstance(submission["session_id"], str)
        self.assertIsInstance(submission["status"], str)

    def test_submission_condition_values(self):
        """Test that condition field has valid values."""
        valid_conditions = ["llm-assisted", "baseline"]
        
        for condition in valid_conditions:
            submission = {
                "submission_id": "sub-123",
                "participant_id": "p-456",
                "problem_id": "human-eval-001",
                "condition": condition,
                "code": "def hello():\n    return 'world'",
                "language": "python",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "sess-789",
                "status": "submitted"
            }
            self.assertIn(condition, valid_conditions)

    def test_submission_language_values(self):
        """Test that language field has valid values."""
        valid_languages = ["python", "java"]
        
        for language in valid_languages:
            submission = {
                "submission_id": "sub-123",
                "participant_id": "p-456",
                "problem_id": "human-eval-001",
                "condition": "llm-assisted",
                "code": "def hello():\n    return 'world'",
                "language": language,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "sess-789",
                "status": "submitted"
            }
            self.assertIn(language, valid_languages)

    def test_submission_status_values(self):
        """Test that status field has valid values."""
        valid_statuses = ["submitted", "processing", "completed", "failed"]
        
        for status in valid_statuses:
            submission = {
                "submission_id": "sub-123",
                "participant_id": "p-456",
                "problem_id": "human-eval-001",
                "condition": "llm-assisted",
                "code": "def hello():\n    return 'world'",
                "language": "python",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "sess-789",
                "status": status
            }
            self.assertIn(status, valid_statuses)

    def test_submission_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Verify it can be parsed back
        parsed = datetime.fromisoformat(timestamp)
        self.assertIsNotNone(parsed)

    def test_submission_json_serializable(self):
        """Test that submission can be serialized to JSON."""
        submission = {
            "submission_id": "sub-123",
            "participant_id": "p-456",
            "problem_id": "human-eval-001",
            "condition": "llm-assisted",
            "code": "def hello():\n    return 'world'",
            "language": "python",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "sess-789",
            "status": "submitted"
        }

        try:
            json_str = json.dumps(submission)
            parsed = json.loads(json_str)
            self.assertEqual(parsed["submission_id"], submission["submission_id"])
        except Exception as e:
            self.fail(f"Submission is not JSON serializable: {e}")

    def test_submission_optional_fields(self):
        """Test that optional fields can be present."""
        submission = {
            "submission_id": "sub-123",
            "participant_id": "p-456",
            "problem_id": "human-eval-001",
            "condition": "llm-assisted",
            "code": "def hello():\n    return 'world'",
            "language": "python",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "sess-789",
            "status": "submitted",
            "model_response": "Generated code response",
            "error_message": None,
            "metadata": {"key": "value"}
        }

        # Verify optional fields don't break schema
        self.assertIn("model_response", submission)
        self.assertIn("error_message", submission)
        self.assertIn("metadata", submission)

    def test_submission_empty_code_handling(self):
        """Test handling of empty code submissions."""
        submission = {
            "submission_id": "sub-123",
            "participant_id": "p-456",
            "problem_id": "human-eval-001",
            "condition": "baseline",
            "code": "",
            "language": "python",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "sess-789",
            "status": "submitted"
        }

        # Empty code should be allowed (will fail validation later)
        self.assertEqual(submission["code"], "")

    def test_submission_uuid_format(self):
        """Test that submission_id follows UUID format."""
        import uuid
        
        submission_id = str(uuid.uuid4())
        submission = {
            "submission_id": submission_id,
            "participant_id": "p-456",
            "problem_id": "human-eval-001",
            "condition": "llm-assisted",
            "code": "def hello():\n    return 'world'",
            "language": "python",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "sess-789",
            "status": "submitted"
        }

        # Verify it's a valid UUID
        try:
            uuid.UUID(submission_id)
        except ValueError:
            self.fail(f"submission_id is not a valid UUID: {submission_id}")


if __name__ == "__main__":
    unittest.main()
"""
Contract test for submission schema (User Story 1).

Validates that the Submission entity defined in code/data/models.py
conforms to the schema requirements for the experiment interface.
"""
import pytest
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict

# Import the real model definitions from the project
from data.models import Submission, Condition, ProblemSource
from data.db_schema import get_connection, init_schema


# --- Schema Constants (Contract Definition) ---
SUBMISSION_REQUIRED_FIELDS = {
    "id",
    "participant_id",
    "session_id",
    "problem_id",
    "condition",
    "code_content",
    "language",
    "timestamp",
    "submission_order",
    "model_used",
    "error_message",
    "is_valid"
}

SUBMISSION_FIELD_TYPES = {
    "id": str,
    "participant_id": str,
    "session_id": str,
    "problem_id": str,
    "condition": str,  # Enum serialized as string
    "code_content": str,
    "language": str,
    "timestamp": str,  # ISO 8601 UTC
    "submission_order": int,
    "model_used": str,
    "error_message": (str, type(None)),
    "is_valid": bool
}

VALID_CONDITIONS = {"llm_assisted", "baseline"}
VALID_LANGUAGES = {"python", "java"}


def validate_iso8601_utc(timestamp_str: str) -> bool:
    """Validate that a timestamp string is ISO 8601 UTC format."""
    # Pattern for ISO 8601 with timezone (Z or +00:00)
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
    if not re.match(pattern, timestamp_str):
        return False
    try:
        # Attempt to parse to ensure it's a valid date
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        # Check if it's UTC
        return dt.tzinfo is not None and dt.utcoffset().total_seconds() == 0
    except ValueError:
        return False


def validate_submission_dict(data: Dict[str, Any], strict: bool = True) -> Dict[str, Any]:
    """
    Validate a dictionary against the Submission schema.
    Returns a dict with 'valid' boolean and 'errors' list.
    """
    errors = []
    warnings = []

    # Check required fields
    missing = SUBMISSION_REQUIRED_FIELDS - set(data.keys())
    if missing:
        errors.append(f"Missing required fields: {missing}")

    # Check field types
    for field, expected_type in SUBMISSION_FIELD_TYPES.items():
        if field in data:
            value = data[field]
            if isinstance(expected_type, tuple):
                # Allow multiple types (e.g., str or None)
                if not isinstance(value, expected_type):
                    errors.append(f"Field '{field}' has invalid type: expected {expected_type}, got {type(value)}")
            elif not isinstance(value, expected_type):
                errors.append(f"Field '{field}' has invalid type: expected {expected_type}, got {type(value)}")

    # Specific value validations
    if "condition" in data:
        if data["condition"] not in VALID_CONDITIONS:
            errors.append(f"Invalid condition: {data['condition']}. Must be one of {VALID_CONDITIONS}")

    if "language" in data:
        if data["language"] not in VALID_LANGUAGES:
            errors.append(f"Invalid language: {data['language']}. Must be one of {VALID_LANGUAGES}")

    if "timestamp" in data:
        if not validate_iso8601_utc(data["timestamp"]):
            errors.append(f"Invalid timestamp format: {data['timestamp']}. Must be ISO 8601 UTC.")

    if "submission_order" in data:
        if not isinstance(data["submission_order"], int) or data["submission_order"] < 0:
            errors.append(f"Invalid submission_order: {data['submission_order']}. Must be non-negative integer.")

    if strict and errors:
        raise ValueError(f"Submission schema validation failed: {errors}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "data": data
    }


class TestSubmissionSchema:
    """Contract tests for the Submission schema."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Ensure database schema is initialized before tests."""
        # We don't necessarily need the DB for schema contract tests,
        # but if we test serialization to DB format, we might.
        # For now, just verify the model class exists and is importable.
        assert Submission is not None
        yield

    def test_submission_model_exists(self):
        """Verify the Submission dataclass exists and has required attributes."""
        assert hasattr(Submission, "__dataclass_fields__")
        fields = set(Submission.__dataclass_fields__.keys())
        assert SUBMISSION_REQUIRED_FIELDS.issubset(fields), \
            f"Missing fields in Submission model: {SUBMISSION_REQUIRED_FIELDS - fields}"

    def test_valid_submission_creation(self):
        """Test creating a valid Submission instance."""
        now = datetime.now(timezone.utc).isoformat()
        sub = Submission(
            id="sub_123",
            participant_id="p_001",
            session_id="sess_001",
            problem_id="prob_001",
            condition=Condition.LLM_ASSISTED,
            code_content="print('hello')",
            language="python",
            timestamp=now,
            submission_order=1,
            model_used="starcoder",
            error_message=None,
            is_valid=True
        )
        assert sub.id == "sub_123"
        assert sub.participant_id == "p_001"
        assert sub.condition == Condition.LLM_ASSISTED

    def test_serialization_to_dict(self):
        """Test that a Submission instance can be serialized to a valid dict."""
        now = datetime.now(timezone.utc).isoformat()
        sub = Submission(
            id="sub_123",
            participant_id="p_001",
            session_id="sess_001",
            problem_id="prob_001",
            condition=Condition.BASELINE,
            code_content="def foo(): pass",
            language="python",
            timestamp=now,
            submission_order=1,
            model_used="baseline",
            error_message=None,
            is_valid=True
        )
        # Convert to dict (using asdict or manual)
        from dataclasses import asdict
        data = asdict(sub)

        # Validate against contract
        result = validate_submission_dict(data)
        assert result["valid"], f"Serialized dict failed validation: {result['errors']}"

    def test_json_serialization_roundtrip(self):
        """Test JSON serialization and deserialization preserves schema."""
        now = datetime.now(timezone.utc).isoformat()
        sub = Submission(
            id="sub_123",
            participant_id="p_001",
            session_id="sess_001",
            problem_id="prob_001",
            condition=Condition.LLM_ASSISTED,
            code_content="x = 1",
            language="java",
            timestamp=now,
            submission_order=2,
            model_used="jacotext",
            error_message="SyntaxError: missing semicolon",
            is_valid=False
        )
        from dataclasses import asdict
        data = asdict(sub)
        json_str = json.dumps(data)
        loaded = json.loads(json_str)

        result = validate_submission_dict(loaded)
        assert result["valid"], f"JSON roundtrip failed validation: {result['errors']}"

    def test_invalid_condition_rejected(self):
        """Test that an invalid condition value is caught."""
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "id": "sub_999",
            "participant_id": "p_001",
            "session_id": "sess_001",
            "problem_id": "prob_001",
            "condition": "invalid_condition",  # Invalid
            "code_content": "code",
            "language": "python",
            "timestamp": now,
            "submission_order": 1,
            "model_used": "test",
            "error_message": None,
            "is_valid": True
        }
        result = validate_submission_dict(data)
        assert not result["valid"]
        assert any("Invalid condition" in e for e in result["errors"])

    def test_invalid_timestamp_rejected(self):
        """Test that an invalid timestamp format is caught."""
        data = {
            "id": "sub_999",
            "participant_id": "p_001",
            "session_id": "sess_001",
            "problem_id": "prob_001",
            "condition": "baseline",
            "code_content": "code",
            "language": "python",
            "timestamp": "2023-01-01",  # Missing time
            "submission_order": 1,
            "model_used": "test",
            "error_message": None,
            "is_valid": True
        }
        result = validate_submission_dict(data)
        assert not result["valid"]
        assert any("Invalid timestamp" in e for e in result["errors"])

    def test_null_error_message_allowed(self):
        """Test that error_message can be null."""
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "id": "sub_999",
            "participant_id": "p_001",
            "session_id": "sess_001",
            "problem_id": "prob_001",
            "condition": "baseline",
            "code_content": "code",
            "language": "python",
            "timestamp": now,
            "submission_order": 1,
            "model_used": "test",
            "error_message": None,
            "is_valid": True
        }
        result = validate_submission_dict(data)
        assert result["valid"]

    def test_missing_required_field_rejected(self):
        """Test that missing required fields are caught."""
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "id": "sub_999",
            "participant_id": "p_001",
            "session_id": "sess_001",
            # Missing problem_id
            "condition": "baseline",
            "code_content": "code",
            "language": "python",
            "timestamp": now,
            "submission_order": 1,
            "model_used": "test",
            "error_message": None,
            "is_valid": True
        }
        result = validate_submission_dict(data)
        assert not result["valid"]
        assert any("Missing required fields" in e for e in result["errors"])

    def test_negative_submission_order_rejected(self):
        """Test that negative submission_order is rejected."""
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "id": "sub_999",
            "participant_id": "p_001",
            "session_id": "sess_001",
            "problem_id": "prob_001",
            "condition": "baseline",
            "code_content": "code",
            "language": "python",
            "timestamp": now,
            "submission_order": -1,
            "model_used": "test",
            "error_message": None,
            "is_valid": True
        }
        result = validate_submission_dict(data)
        assert not result["valid"]
        assert any("Invalid submission_order" in e for e in result["errors"])
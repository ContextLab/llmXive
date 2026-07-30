"""
Contract tests for the divergence metric output schema.
Validates the structure of divergence calculation results.
"""
import pytest
import json
from pathlib import Path
from typing import Dict, Any, List


def validate_divergence_record(record: Dict[str, Any]) -> bool:
    """
    Validates a single divergence record.

    Expected schema:
    {
        "problem_id": str,
        "thinking_embedding": List[float],
        "tool_centroid_embedding": List[float],
        "cosine_similarity": float,
        "semantic_divergence_score": float
    }
    """
    required_fields = {
        "problem_id": str,
        "thinking_embedding": list,
        "tool_centroid_embedding": list,
        "cosine_similarity": (int, float),
        "semantic_divergence_score": (int, float)
    }

    if not isinstance(record, dict):
        return False

    for field, expected_type in required_fields.items():
        if field not in record:
            return False
        if not isinstance(record[field], expected_type):
            return False

    # Additional checks for specific fields
    if not isinstance(record["thinking_embedding"][0], (int, float)):
        return False
    if not isinstance(record["tool_centroid_embedding"][0], (int, float)):
        return False

    return True


def test_divergence_output_schema() -> None:
    """Test that a valid divergence record passes validation."""
    valid_record = {
        "problem_id": "math_001",
        "thinking_embedding": [0.1, 0.2, 0.3],
        "tool_centroid_embedding": [0.4, 0.5, 0.6],
        "cosine_similarity": 0.85,
        "semantic_divergence_score": 0.15
    }
    assert validate_divergence_record(valid_record) is True


def test_divergence_output_invalid_missing_field() -> None:
    """Test that a record with a missing field fails validation."""
    invalid_record = {
        "problem_id": "math_001",
        "thinking_embedding": [0.1, 0.2, 0.3],
        "tool_centroid_embedding": [0.4, 0.5, 0.6],
        "cosine_similarity": 0.85
        # Missing "semantic_divergence_score"
    }
    assert validate_divergence_record(invalid_record) is False


def test_divergence_output_invalid_range() -> None:
    """Test that a record with invalid types fails validation."""
    invalid_record = {
        "problem_id": "math_001",
        "thinking_embedding": "not a list",
        "tool_centroid_embedding": [0.4, 0.5, 0.6],
        "cosine_similarity": 0.85,
        "semantic_divergence_score": 0.15
    }
    assert validate_divergence_record(invalid_record) is False

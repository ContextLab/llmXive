"""
Contract Tests for Dialogue Schema (T045).

Validates that generated dialogue tuples adhere to the required structure:
- question
- initial_answer
- critique
- revised_answer
"""
import json
import pytest
from pathlib import Path
from typing import List, Dict, Any, Optional

REQUIRED_FIELDS = ["question", "initial_answer", "critique", "revised_answer"]

def load_jsonl_records(file_path: Path) -> List[Dict[str, Any]]:
    """Helper to load JSONL records."""
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def validate_dialogue_schema(record: Dict[str, Any]) -> bool:
    """
    Validates a single record against the schema.

    Args:
        record: The dictionary to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(record, dict):
        return False

    for field in REQUIRED_FIELDS:
        if field not in record:
            return False
        if not isinstance(record[field], str):
            return False
        if len(record[field].strip()) == 0:
            return False

    return True

def test_validate_dialogue_schema():
    """
    Unit test for schema validation logic.
    """
    valid_record = {
        "question": "What is 2+2?",
        "initial_answer": "5",
        "critique": "The calculation is incorrect. 2+2 equals 4.",
        "revised_answer": "4"
    }
    assert validate_dialogue_schema(valid_record) is True

    invalid_record_missing_field = {
        "question": "What is 2+2?",
        "initial_answer": "5",
        "critique": "The calculation is incorrect."
        # Missing revised_answer
    }
    assert validate_dialogue_schema(invalid_record_missing_field) is False

    invalid_record_empty_field = {
        "question": "What is 2+2?",
        "initial_answer": "5",
        "critique": "",
        "revised_answer": "4"
    }
    assert validate_dialogue_schema(invalid_record_empty_field) is False

def test_validate_dialogue_schema_file(tmp_path: Path):
    """
    Integration test: Validate a generated JSONL file.
    """
    test_file = tmp_path / "test_dialogue.jsonl"
    valid_records = [
        {
            "question": "Q1",
            "initial_answer": "A1",
            "critique": "C1",
            "revised_answer": "R1"
        },
        {
            "question": "Q2",
            "initial_answer": "A2",
            "critique": "C2",
            "revised_answer": "R2"
        }
    ]

    with open(test_file, "w", encoding="utf-8") as f:
        for rec in valid_records:
            f.write(json.dumps(rec) + "\n")

    records = load_jsonl_records(test_file)
    assert len(records) == 2
    for rec in records:
        assert validate_dialogue_schema(rec) is True
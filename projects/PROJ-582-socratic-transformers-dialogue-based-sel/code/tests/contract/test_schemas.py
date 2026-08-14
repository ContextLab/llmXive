"""
Contract tests for dialogue tuple schema validation.
Tests that JSONL records contain required fields: question, initial_answer, critique, revised_answer.
"""
import json
import pytest
from pathlib import Path
from typing import List, Dict, Any, Optional

REQUIRED_FIELDS = ["question", "initial_answer", "critique", "revised_answer"]

def load_jsonl_records(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSONL records from a file."""
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def validate_dialogue_schema(record: Dict[str, Any]) -> bool:
    """
    Validate that a dialogue tuple record contains all required fields.
    
    Args:
        record: A single dialogue tuple record (dict).
    
    Returns:
        True if the record is valid, False otherwise.
    """
    if not isinstance(record, dict):
        return False
    
    for field in REQUIRED_FIELDS:
        if field not in record:
            return False
        if record[field] is None:
            return False
    
    return True

def test_validate_dialogue_schema():
    """
    Test that the schema validation function correctly identifies valid and invalid records.
    """
    # Valid record
    valid_record = {
        "question": "What is 2+2?",
        "initial_answer": "4",
        "critique": "The reasoning is correct.",
        "revised_answer": "4"
    }
    assert validate_dialogue_schema(valid_record) is True

    # Invalid record - missing field
    invalid_record_missing = {
        "question": "What is 2+2?",
        "initial_answer": "4",
        "critique": "The reasoning is correct."
    }
    assert validate_dialogue_schema(invalid_record_missing) is False

    # Invalid record - None value
    invalid_record_none = {
        "question": "What is 2+2?",
        "initial_answer": "4",
        "critique": "The reasoning is correct.",
        "revised_answer": None
    }
    assert validate_dialogue_schema(invalid_record_none) is False

    # Invalid record - not a dict
    assert validate_dialogue_schema("not a dict") is False

def test_validate_dialogue_schema_file(tmp_path: Path):
    """
    Test validation against a temporary JSONL file.
    """
    # Create a valid JSONL file
    valid_file = tmp_path / "valid.jsonl"
    with open(valid_file, "w", encoding="utf-8") as f:
        f.write('{"question": "Q1", "initial_answer": "A1", "critique": "C1", "revised_answer": "R1"}\n')
        f.write('{"question": "Q2", "initial_answer": "A2", "critique": "C2", "revised_answer": "R2"}\n')
    
    records = load_jsonl_records(valid_file)
    assert len(records) == 2
    for record in records:
        assert validate_dialogue_schema(record) is True

    # Create an invalid JSONL file (missing field)
    invalid_file = tmp_path / "invalid.jsonl"
    with open(invalid_file, "w", encoding="utf-8") as f:
        f.write('{"question": "Q1", "initial_answer": "A1"}\n')
    
    records = load_jsonl_records(invalid_file)
    assert len(records) == 1
    assert validate_dialogue_schema(records[0]) is False

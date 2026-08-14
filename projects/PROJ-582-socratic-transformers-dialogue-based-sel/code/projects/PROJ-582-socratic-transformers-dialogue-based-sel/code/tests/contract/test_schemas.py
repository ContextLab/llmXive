import json
import pytest
from pathlib import Path
from typing import List, Dict, Any, Optional

def load_jsonl_records(file_path: str) -> List[Dict[str, Any]]:
    """
    Helper to load JSONL records from a file.
    Used for testing schema validation against generated data.
    """
    records = []
    path = Path(file_path)
    if not path.exists():
        return records
    
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num}: {e}")
    return records

def validate_dialogue_schema(record: Dict[str, Any]) -> bool:
    """
    Validates a single dialogue tuple record against the required schema.
    
    Required fields:
    - question (str)
    - initial_answer (str)
    - critique (dict):
        - confidence_score (float)
        - reasoning_snippet (str)
    - revised_answer (str)
    
    Returns True if valid, raises AssertionError if invalid.
    """
    required_top_level = ['question', 'initial_answer', 'critique', 'revised_answer']
    
    for field in required_top_level:
        if field not in record:
            raise AssertionError(f"Missing required field: '{field}'")
    
    # Validate types
    if not isinstance(record['question'], str):
        raise AssertionError(f"Field 'question' must be a string, got {type(record['question'])}")
    if not isinstance(record['initial_answer'], str):
        raise AssertionError(f"Field 'initial_answer' must be a string, got {type(record['initial_answer'])}")
    if not isinstance(record['revised_answer'], str):
        raise AssertionError(f"Field 'revised_answer' must be a string, got {type(record['revised_answer'])}")
    
    # Validate critique structure
    critique = record['critique']
    if not isinstance(critique, dict):
        raise AssertionError(f"Field 'critique' must be a dict, got {type(critique)}")
    
    critique_required = ['confidence_score', 'reasoning_snippet']
    for field in critique_required:
        if field not in critique:
            raise AssertionError(f"Missing required field in critique: '{field}'")
    
    if not isinstance(critique['confidence_score'], (int, float)):
        raise AssertionError(f"Field 'critique.confidence_score' must be a number, got {type(critique['confidence_score'])}")
    if not isinstance(critique['reasoning_snippet'], str):
        raise AssertionError(f"Field 'critique.reasoning_snippet' must be a string, got {type(critique['reasoning_snippet'])}")
    
    return True

def test_validate_dialogue_schema():
    """
    Contract test for dialogue tuple schema.
    Asserts JSONL records contain required fields with correct types.
    """
    # Test valid record
    valid_record = {
        "question": "What is 2 + 2?",
        "initial_answer": "5",
        "critique": {
            "confidence_score": 0.45,
            "reasoning_snippet": "The addition seems incorrect; 2+2 is typically 4."
        },
        "revised_answer": "4"
    }
    
    assert validate_dialogue_schema(valid_record) is True
    
    # Test missing top-level field
    invalid_record_missing = {
        "question": "Test?",
        "initial_answer": "A",
        "critique": {"confidence_score": 0.5, "reasoning_snippet": "Reason"}
        # Missing revised_answer
    }
    
    with pytest.raises(AssertionError) as exc_info:
        validate_dialogue_schema(invalid_record_missing)
    assert "Missing required field: 'revised_answer'" in str(exc_info.value)
    
    # Test invalid critique structure
    invalid_record_critique = {
        "question": "Test?",
        "initial_answer": "A",
        "critique": {
            "confidence_score": "high", # Should be number
            "reasoning_snippet": "Reason"
        },
        "revised_answer": "B"
    }
    
    with pytest.raises(AssertionError) as exc_info:
        validate_dialogue_schema(invalid_record_critique)
    assert "must be a number" in str(exc_info.value)
    
    # Test missing critique field
    invalid_record_no_critique = {
        "question": "Test?",
        "initial_answer": "A",
        "critique": {
            "confidence_score": 0.5
            # Missing reasoning_snippet
        },
        "revised_answer": "B"
    }
    
    with pytest.raises(AssertionError) as exc_info:
        validate_dialogue_schema(invalid_record_no_critique)
    assert "Missing required field in critique: 'reasoning_snippet'" in str(exc_info.value)

def test_validate_dialogue_schema_file(tmp_path):
    """
    Integration-style contract test: validates a file containing multiple records.
    """
    output_file = tmp_path / "dialogue_test.jsonl"
    
    records = [
        {
            "question": "Q1",
            "initial_answer": "A1",
            "critique": {"confidence_score": 0.8, "reasoning_snippet": "R1"},
            "revised_answer": "A1_rev"
        },
        {
            "question": "Q2",
            "initial_answer": "A2",
            "critique": {"confidence_score": 0.2, "reasoning_snippet": "R2"},
            "revised_answer": "A2_rev"
        }
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    
    loaded = load_jsonl_records(str(output_file))
    assert len(loaded) == 2
    
    for rec in loaded:
        validate_dialogue_schema(rec)
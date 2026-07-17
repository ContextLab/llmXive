"""
Unit tests for the merge and validation logic in preprocessing.py.

Tests T022: Merging entropy profiles with labeled dataset.
Tests T023: Validation of entropy profiles.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.preprocessing import merge_entropy_profiles, validate_entropy_profile, BatchSizeError
from src.utils.validators import validate_json_schema

# Mock schema for testing if the real one is missing or to ensure self-containment
MOCK_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["sequence_id", "validity", "entropy_profile"],
    "properties": {
        "sequence_id": {"type": "string"},
        "validity": {"type": "string", "enum": ["valid", "invalid", "ambiguous"]},
        "entropy_profile": {
            "type": "object",
            "required": ["layers"],
            "properties": {
                "layers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["layer_id", "token_probs"],
                        "properties": {
                            "layer_id": {"type": "integer"},
                            "token_probs": {
                                "type": "array",
                                "items": {"type": "number"}
                            }
                        }
                    }
                }
            }
        }
    }
}

@pytest.fixture
def temp_test_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_schema_file(temp_test_dir):
    schema_path = temp_test_dir / "test_schema.yaml"
    # Write a simple YAML representation for the validator
    # Note: The validator uses json schema logic, but file extension is .yaml in spec.
    # We will write JSON content to a .yaml file for the test to work with the json schema validator
    # if the validator reads the file content as JSON.
    # The actual implementation of validate_json_schema likely loads the yaml and converts to dict.
    # For this test, we assume the validator can handle a JSON file passed as a path.
    with open(schema_path, "w") as f:
        json.dump(MOCK_SCHEMA, f)
    return schema_path

def test_merge_entropy_profiles_success(temp_test_dir, mock_schema_file):
    labeled_path = temp_test_dir / "labeled.jsonl"
    entropy_path = temp_test_dir / "entropy.jsonl"
    output_path = temp_test_dir / "merged.jsonl"

    # Create labeled data
    labeled_data = [
        {"sequence_id": "seq_1", "validity": "valid", "tokens": ["a", "b"]},
        {"sequence_id": "seq_2", "validity": "invalid", "tokens": ["c", "d"]}
    ]
    with open(labeled_path, "w") as f:
        for item in labeled_data:
            f.write(json.dumps(item) + "\n")

    # Create entropy data
    entropy_data = [
        {
            "sequence_id": "seq_1",
            "entropy_profile": {
                "layers": [
                    {"layer_id": 0, "token_probs": [0.9, 0.1]},
                    {"layer_id": 1, "token_probs": [0.8, 0.2]}
                ]
            }
        },
        {
            "sequence_id": "seq_2",
            "entropy_profile": {
                "layers": [
                    {"layer_id": 0, "token_probs": [0.5, 0.5]}
                ]
            }
        }
    ]
    with open(entropy_path, "w") as f:
        for item in entropy_data:
            f.write(json.dumps(item) + "\n")

    # Perform merge
    count = merge_entropy_profiles(labeled_path, entropy_path, output_path)

    assert count == 2
    assert output_path.exists()

    with open(output_path, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    
    # Verify structure
    for line in lines:
        record = json.loads(line)
        assert "sequence_id" in record
        assert "validity" in record
        assert "entropy_profile" in record
        assert "layers" in record["entropy_profile"]

def test_merge_missing_sequence_id(temp_test_dir, mock_schema_file):
    labeled_path = temp_test_dir / "labeled.jsonl"
    entropy_path = temp_test_dir / "entropy.jsonl"
    output_path = temp_test_dir / "merged.jsonl"

    # Labeled data
    with open(labeled_path, "w") as f:
        f.write(json.dumps({"sequence_id": "seq_1", "validity": "valid"}) + "\n")

    # Entropy data missing sequence_id
    with open(entropy_path, "w") as f:
        f.write(json.dumps({"entropy_profile": {"layers": []}}) + "\n")

    count = merge_entropy_profiles(labeled_path, entropy_path, output_path)
    assert count == 0 # Should skip the one with missing ID

def test_validate_entropy_profile_valid(temp_test_dir, mock_schema_file):
    data_path = temp_test_dir / "valid_entropy.jsonl"
    
    record = {
        "sequence_id": "seq_1",
        "validity": "valid",
        "entropy_profile": {
            "layers": [
                {"layer_id": 0, "token_probs": [0.9, 0.1]},
                {"layer_id": 1, "token_probs": [0.8, 0.2]}
            ]
        }
    }
    
    with open(data_path, "w") as f:
        f.write(json.dumps(record) + "\n")

    # This will call the real validation logic which might fail if schema path is wrong
    # We assume the test environment has the schema or we pass the mock one
    # For this unit test, we rely on the mock_schema_file fixture
    is_valid = validate_entropy_profile(data_path, mock_schema_file)
    assert is_valid

def test_validate_entropy_profile_missing_values(temp_test_dir, mock_schema_file):
    data_path = temp_test_dir / "invalid_entropy.jsonl"
    
    # Record with None token_probs
    record = {
        "sequence_id": "seq_1",
        "validity": "valid",
        "entropy_profile": {
            "layers": [
                {"layer_id": 0, "token_probs": None}
            ]
        }
    }
    
    with open(data_path, "w") as f:
        f.write(json.dumps(record) + "\n")

    is_valid = validate_entropy_profile(data_path, mock_schema_file)
    assert not is_valid

def test_validate_entropy_profile_missing_layer(temp_test_dir, mock_schema_file):
    data_path = temp_test_dir / "invalid_entropy2.jsonl"
    
    # Record with missing layers key
    record = {
        "sequence_id": "seq_1",
        "validity": "valid",
        "entropy_profile": {}
    }
    
    with open(data_path, "w") as f:
        f.write(json.dumps(record) + "\n")

    is_valid = validate_entropy_profile(data_path, mock_schema_file)
    assert not is_valid
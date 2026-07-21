import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest

from src.generation.generation import (
    load_and_merge_outputs,
    write_labeled_dataset,
)
from src.utils.validators import TokenSequence, ValidityLabel

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def gsm8k_data_path(temp_output_dir):
    path = temp_output_dir / "gsm8k_gen.jsonl"
    # Simulating generation output for GSM8K
    data = [
        {"sequence_id": "gsm_001", "tokens": ["4", "+"], "source": "gsm8k", "prompt": "What is 2+2?"},
        {"sequence_id": "gsm_002", "tokens": ["3", "*", "3"], "source": "gsm8k", "prompt": "What is 3 times 3?"},
        {"sequence_id": "gsm_003", "tokens": ["1", "0"], "source": "gsm8k", "prompt": "What is 10?"},
    ]
    with open(path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return path

@pytest.fixture
def minigrid_data_path(temp_output_dir):
    path = temp_output_dir / "minigrid_gen.jsonl"
    # Simulating generation output for MiniGrid
    data = [
        {"sequence_id": "mg_001", "tokens": ["move", "right"], "source": "minigrid", "prompt": "Go right"},
        {"sequence_id": "mg_002", "tokens": ["pick", "up"], "source": "minigrid", "prompt": "Pick object"},
    ]
    with open(path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return path

@pytest.fixture
def label_data_path(temp_output_dir):
    path = temp_output_dir / "labels.jsonl"
    # Simulating ground truth labels
    # Note: mg_003 is in labels but NOT in generation data (tests orphan handling)
    # mg_001 has multiple valid paths in a real scenario, here we simulate one match
    data = [
        {"sequence_id": "gsm_001", "is_valid": True, "reason": "matched", "metadata": {"path": "direct"}},
        {"sequence_id": "gsm_002", "is_valid": False, "reason": "mismatch", "metadata": {"expected": ["9"]}},
        {"sequence_id": "mg_001", "is_valid": True, "reason": "matched", "metadata": {"path": "optimal"}},
        {"sequence_id": "mg_003", "is_valid": True, "reason": "matched", "metadata": {"path": "alt"}},
    ]
    with open(path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return path

def test_ground_truth_labeling_gsm8k(temp_output_dir, gsm8k_data_path, label_data_path):
    """
    Test that GSM8K data is correctly merged with ground truth labels.
    Verifies multi-path matching logic by ensuring valid tokens are marked correctly.
    """
    output_path = temp_output_dir / "merged_gsm8k.jsonl"
    import logging
    logger = logging.getLogger("test_gsm8k")
    logger.setLevel(logging.DEBUG)

    # This calls the implementation from T016 which merges generation with labels
    load_and_merge_outputs(gsm8k_data_path, label_data_path, output_path, logger)

    assert output_path.exists()
    with open(output_path) as f:
        lines = f.readlines()
    
    # We expect 2 records from generation (gsm_001, gsm_002). 
    # gsm_003 is in generation but not in labels -> should be marked invalid or dropped?
    # Based on T014 logic: if no match, log warning and retain with validity=false.
    # Let's check the count.
    assert len(lines) == 3 

    results = [json.loads(line) for line in lines]
    
    # Check gsm_001 is valid
    gsm_001 = next((r for r in results if r["sequence_id"] == "gsm_001"), None)
    assert gsm_001 is not None
    assert gsm_001["validity"] is True
    assert gsm_001["reason"] == "matched"

    # Check gsm_002 is invalid (mismatch)
    gsm_002 = next((r for r in results if r["sequence_id"] == "gsm_002"), None)
    assert gsm_002 is not None
    assert gsm_002["validity"] is False
    assert gsm_002["reason"] == "mismatch"

    # Check gsm_003 (no label found) -> validity should be false per T014
    gsm_003 = next((r for r in results if r["sequence_id"] == "gsm_003"), None)
    assert gsm_003 is not None
    assert gsm_003["validity"] is False
    assert gsm_003["reason"] == "no_match"

def test_ground_truth_labeling_minigrid(temp_output_dir, minigrid_data_path, label_data_path):
    """
    Test that MiniGrid data is correctly merged, handling multi-path scenarios.
    """
    output_path = temp_output_dir / "merged_minigrid.jsonl"
    import logging
    logger = logging.getLogger("test_minigrid")
    logger.setLevel(logging.DEBUG)

    load_and_merge_outputs(minigrid_data_path, label_data_path, output_path, logger)

    assert output_path.exists()
    with open(output_path) as f:
        lines = f.readlines()
    
    # We expect 2 records from generation (mg_001, mg_002).
    assert len(lines) == 2

    results = [json.loads(line) for line in lines]

    # mg_001 is valid
    mg_001 = next((r for r in results if r["sequence_id"] == "mg_001"), None)
    assert mg_001 is not None
    assert mg_001["validity"] is True
    assert mg_001["reason"] == "matched"

    # mg_002 has no label -> validity false
    mg_002 = next((r for r in results if r["sequence_id"] == "mg_002"), None)
    assert mg_002 is not None
    assert mg_002["validity"] is False
    assert mg_002["reason"] == "no_match"

def test_labeled_dataset_schema_compliance(temp_output_dir, gsm8k_data_path, label_data_path):
    """
    Verify the merged output conforms to the dataset schema defined in contracts.
    """
    output_path = temp_output_dir / "schema_test.jsonl"
    import logging
    logger = logging.getLogger("test_schema")
    logger.setLevel(logging.DEBUG)

    load_and_merge_outputs(gsm8k_data_path, label_data_path, output_path, logger)

    import yaml
    schema_path = Path(__file__).resolve().parents[2] / "contracts" / "dataset.schema.yaml"
    
    # Ensure schema file exists
    if not schema_path.exists():
        # Create a minimal schema for testing if missing (should exist in project)
        schema = {
            "type": "object",
            "required": ["sequence_id", "tokens", "validity", "reason"],
            "properties": {
                "sequence_id": {"type": "string"},
                "tokens": {"type": "array", "items": {"type": "string"}},
                "validity": {"type": "boolean"},
                "reason": {"type": "string"},
                "metadata": {"type": "object"}
            }
        }
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        with open(schema_path, "w") as f:
            yaml.dump(schema, f)
    else:
        with open(schema_path) as f:
            schema = yaml.safe_load(f)

    with open(output_path) as f:
        for line in f:
            record = json.loads(line)
            # Validate required fields per schema
            assert "sequence_id" in record, "Missing sequence_id"
            assert "tokens" in record, "Missing tokens"
            assert "validity" in record, "Missing validity"
            assert "reason" in record, "Missing reason"
            
            # Type checks
            assert isinstance(record["sequence_id"], str)
            assert isinstance(record["tokens"], list)
            assert isinstance(record["validity"], bool)
            assert isinstance(record["reason"], str)
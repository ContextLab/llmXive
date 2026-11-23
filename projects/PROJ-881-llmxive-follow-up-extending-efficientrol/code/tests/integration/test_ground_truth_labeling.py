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
    data = [
        {"sequence_id": "1", "tokens": ["4", "+"], "source": "gsm8k"},
        {"sequence_id": "2", "tokens": ["3", "*", "3"], "source": "gsm8k"},
    ]
    with open(path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return path

@pytest.fixture
def minigrid_data_path(temp_output_dir):
    path = temp_output_dir / "minigrid_gen.jsonl"
    data = [
        {"sequence_id": "mg1", "tokens": ["move", "right"], "source": "minigrid"},
    ]
    with open(path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return path

@pytest.fixture
def label_data_path(temp_output_dir):
    path = temp_output_dir / "labels.jsonl"
    data = [
        {"sequence_id": "1", "is_valid": True, "reason": "matched", "metadata": {}},
        {"sequence_id": "2", "is_valid": False, "reason": "mismatch", "metadata": {}},
        {"sequence_id": "mg1", "is_valid": True, "reason": "matched", "metadata": {}},
    ]
    with open(path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return path

def test_ground_truth_labeling_gsm8k(temp_output_dir, gsm8k_data_path, label_data_path):
    output_path = temp_output_dir / "merged_gsm8k.jsonl"
    import logging
    logger = logging.getLogger("test")

    load_and_merge_outputs(gsm8k_data_path, label_data_path, output_path, logger)

    assert output_path.exists()
    with open(output_path) as f:
        lines = f.readlines()
    assert len(lines) == 2

def test_ground_truth_labeling_minigrid(temp_output_dir, minigrid_data_path, label_data_path):
    output_path = temp_output_dir / "merged_minigrid.jsonl"
    import logging
    logger = logging.getLogger("test")

    load_and_merge_outputs(minigrid_data_path, label_data_path, output_path, logger)

    assert output_path.exists()
    with open(output_path) as f:
        lines = f.readlines()
    assert len(lines) == 1

def test_labeled_dataset_schema_compliance(temp_output_dir, gsm8k_data_path, label_data_path):
    output_path = temp_output_dir / "schema_test.jsonl"
    import logging
    logger = logging.getLogger("test")

    load_and_merge_outputs(gsm8k_data_path, label_data_path, output_path, logger)

    import yaml
    schema_path = Path(__file__).resolve().parents[2] / "contracts" / "dataset.schema.yaml"
    with open(schema_path) as f:
        schema = yaml.safe_load(f)

    with open(output_path) as f:
        for line in f:
            record = json.loads(line)
            # Validate required fields
            assert "sequence_id" in record
            assert "tokens" in record
            assert "validity" in record
            assert "reason" in record
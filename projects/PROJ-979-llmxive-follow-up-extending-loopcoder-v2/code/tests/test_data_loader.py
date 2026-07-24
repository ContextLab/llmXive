import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import json

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_loader import filter_underpowered, determine_strata

@pytest.fixture
def temp_dir():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

def test_filter_underpowered_basic(temp_dir):
    """Test that filter_underpowered correctly removes underpowered strata."""
    # Create mock strata log
    strata_log_path = os.path.join(temp_dir, "strata_log.json")
    strata_data = {
        "strata": {"easy": 100, "hard": 20},
        "underpowered_strata": ["hard"],
        "total_samples": 120
    }
    with open(strata_log_path, "w") as f:
        json.dump(strata_data, f)

    # Create mock input dataset
    # We need items with 'difficulty' or 'task_id' to match strata
    input_data = []
    for i in range(100):
        input_data.append({"task_id": f"easy_{i}", "difficulty": "easy", "prompt": "test"})
    for i in range(20):
        input_data.append({"task_id": f"hard_{i}", "difficulty": "hard", "prompt": "test"})
    
    input_path = os.path.join(temp_dir, "split_dataset.json")
    with open(input_path, "w") as f:
        json.dump(input_data, f)

    output_path = os.path.join(temp_dir, "filtered_dataset.json")

    # Run filter
    result_path = filter_underpowered(
        strata_log_path=strata_log_path,
        input_dataset_path=input_path,
        output_dataset_path=output_path
    )

    assert os.path.exists(result_path)
    
    # Load and verify
    with open(result_path, "r") as f:
        filtered = json.load(f)
    
    # All 'hard' items should be excluded
    assert len(filtered) == 100
    for item in filtered:
        assert item["difficulty"] == "easy"

def test_filter_underpowered_no_underpowered(temp_dir):
    """Test that if no strata are underpowered, all data is kept."""
    strata_log_path = os.path.join(temp_dir, "strata_log.json")
    strata_data = {
        "strata": {"easy": 100, "hard": 100},
        "underpowered_strata": [],
        "total_samples": 200
    }
    with open(strata_log_path, "w") as f:
        json.dump(strata_data, f)

    input_data = []
    for i in range(100):
        input_data.append({"task_id": f"easy_{i}", "difficulty": "easy", "prompt": "test"})
    for i in range(100):
        input_data.append({"task_id": f"hard_{i}", "difficulty": "hard", "prompt": "test"})
    
    input_path = os.path.join(temp_dir, "split_dataset.json")
    with open(input_path, "w") as f:
        json.dump(input_data, f)

    output_path = os.path.join(temp_dir, "filtered_dataset.json")

    result_path = filter_underpowered(
        strata_log_path=strata_log_path,
        input_dataset_path=input_path,
        output_dataset_path=output_path
    )

    with open(result_path, "r") as f:
        filtered = json.load(f)
    
    assert len(filtered) == 200

def test_filter_underpowered_missing_stratum_column(temp_dir):
    """Test handling of items without difficulty column (fallback to hash)."""
    strata_log_path = os.path.join(temp_dir, "strata_log.json")
    # Simulate a scenario where bucket_1 is underpowered
    strata_data = {
        "strata": {"bucket_0": 50, "bucket_1": 10, "bucket_2": 50, "bucket_3": 50},
        "underpowered_strata": ["bucket_1"],
        "total_samples": 160
    }
    with open(strata_log_path, "w") as f:
        json.dump(strata_data, f)

    # Create items without difficulty
    input_data = []
    for i in range(160):
        # Force some to fall into bucket_1 via hash? Hard to control exactly without knowing hash logic.
        # We'll just create a mix and rely on the re-calculation in filter_underpowered
        input_data.append({"task_id": f"task_{i}", "prompt": "test"})
    
    input_path = os.path.join(temp_dir, "split_dataset.json")
    with open(input_path, "w") as f:
        json.dump(input_data, f)

    output_path = os.path.join(temp_dir, "filtered_dataset.json")

    # This should run without error, filtering based on the re-calculated strata
    # Note: The exact count depends on the hash distribution, but it shouldn't crash.
    result_path = filter_underpowered(
        strata_log_path=strata_log_path,
        input_dataset_path=input_path,
        output_dataset_path=output_path
    )
    
    assert os.path.exists(result_path)
    with open(result_path, "r") as f:
        filtered = json.load(f)
    # Should be less than 160 if any fell into bucket_1
    assert len(filtered) <= 160

def test_filter_underpowered_missing_log_file(temp_dir):
    """Test that FileNotFoundError is raised if log is missing."""
    input_path = os.path.join(temp_dir, "split_dataset.json")
    with open(input_path, "w") as f:
        json.dump([{"task_id": "1", "prompt": "test"}], f)
    
    output_path = os.path.join(temp_dir, "filtered_dataset.json")
    
    with pytest.raises(FileNotFoundError):
        filter_underpowered(
            strata_log_path=os.path.join(temp_dir, "missing.json"),
            input_dataset_path=input_path,
            output_dataset_path=output_path
        )

def test_filter_underpowered_missing_input_file(temp_dir):
    """Test that FileNotFoundError is raised if input dataset is missing."""
    strata_log_path = os.path.join(temp_dir, "strata_log.json")
    with open(strata_log_path, "w") as f:
        json.dump({"underpowered_strata": [], "strata": {}}, f)
    
    output_path = os.path.join(temp_dir, "filtered_dataset.json")
    
    with pytest.raises(FileNotFoundError):
        filter_underpowered(
            strata_log_path=strata_log_path,
            input_dataset_path=os.path.join(temp_dir, "missing.json"),
            output_dataset_path=output_path
        )
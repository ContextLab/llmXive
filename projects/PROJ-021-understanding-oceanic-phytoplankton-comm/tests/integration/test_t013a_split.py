import os
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config import get_config, reset_config

def test_t013a_output_exists():
    """Verify that T013a produces the split_indices.json file."""
    config = get_config()
    project_root = Path(config.get('project_root', '.'))
    output_path = project_root / "data" / "processed" / "split_indices.json"
    
    # Note: This test assumes T013a has been run. 
    # In a full CI pipeline, T013a would run before this test.
    # For now, we check if the file exists.
    assert output_path.exists(), f"Output file {output_path} not found. Did T013a run?"

def test_t013a_split_structure():
    """Verify the structure of the split_indices.json file."""
    config = get_config()
    project_root = Path(config.get('project_root', '.'))
    output_path = project_root / "data" / "processed" / "split_indices.json"
    
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} not found. Skipping structure test.")

    with open(output_path, 'r') as f:
        data = json.load(f)

    assert "train" in data, "Missing 'train' key in split indices."
    assert "val" in data, "Missing 'val' key in split indices."
    assert "test" in data, "Missing 'test' key in split indices."

    assert isinstance(data["train"], list), "'train' must be a list of indices."
    assert isinstance(data["val"], list), "'val' must be a list of indices."
    assert isinstance(data["test"], list), "'test' must be a list of indices."

def test_t013a_no_overlap():
    """Verify that train, val, and test sets are disjoint."""
    config = get_config()
    project_root = Path(config.get('project_root', '.'))
    output_path = project_root / "data" / "processed" / "split_indices.json"
    
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} not found. Skipping disjoint test.")

    with open(output_path, 'r') as f:
        data = json.load(f)

    train_set = set(data["train"])
    val_set = set(data["val"])
    test_set = set(data["test"])

    assert len(train_set & val_set) == 0, "Train and Val sets overlap!"
    assert len(train_set & test_set) == 0, "Train and Test sets overlap!"
    assert len(val_set & test_set) == 0, "Val and Test sets overlap!"

def test_t013a_basin_stratification_approx():
    """
    Verify that the split sizes are roughly proportional to the total.
    This is a soft check to ensure stratification logic ran.
    """
    config = get_config()
    project_root = Path(config.get('project_root', '.'))
    output_path = project_root / "data" / "processed" / "split_indices.json"
    
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} not found. Skipping size check.")

    with open(output_path, 'r') as f:
        data = json.load(f)

    total = len(data["train"]) + len(data["val"]) + len(data["test"])
    assert total > 0, "Total split size is zero."

    train_ratio = len(data["train"]) / total
    val_ratio = len(data["val"]) / total
    test_ratio = len(data["test"]) / total

    # Expected: 0.7, 0.15, 0.15
    # Allow some variance due to integer rounding and basin distribution
    assert 0.6 < train_ratio < 0.8, f"Train ratio {train_ratio} is outside expected range (0.6-0.8)"
    assert 0.1 < val_ratio < 0.25, f"Val ratio {val_ratio} is outside expected range (0.1-0.25)"
    assert 0.05 < test_ratio < 0.25, f"Test ratio {test_ratio} is outside expected range (0.05-0.25)"

    # Ensure sum is 1.0 (within float precision)
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "Ratios do not sum to 1.0"

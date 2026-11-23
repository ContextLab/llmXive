import json
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the functions to test
from apply_mask import (
    load_json_file,
    save_json_file,
    apply_masks_to_attribution,
    verify_masking_effect
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)

def test_apply_masks_zeroes_redundant():
    """Test that redundant subgraphs have their weights zeroed."""
    raw = {
        "mol_1": {
            "subgraph_id": "sg_1",
            "weights": {"atom_0": 0.5, "atom_1": 0.3}
        },
        "mol_2": {
            "subgraph_id": "sg_2",
            "weights": {"atom_0": 0.1, "atom_1": 0.9}
        }
    }
    masks = {
        "sg_1": True,  # Redundant
        "sg_2": False  # Not redundant
    }

    result = apply_masks_to_attribution(raw, masks)

    # Check mol_1 (redundant)
    assert result["mol_1"]["is_redundant"] is True
    assert all(w == 0.0 for w in result["mol_1"]["weights"].values())

    # Check mol_2 (not redundant)
    assert result["mol_2"]["is_redundant"] is False
    assert result["mol_2"]["weights"]["atom_0"] == 0.1
    assert result["mol_2"]["weights"]["atom_1"] == 0.9

def test_verify_masking_effect_pass():
    """Test verification passes when redundant subgraphs are zeroed."""
    masked = {
        "mol_1": {
            "subgraph_id": "sg_1",
            "weights": {"atom_0": 0.0, "atom_1": 0.0},
            "is_redundant": True
        }
    }
    masks = {"sg_1": True}

    assert verify_masking_effect(masked, masks) is True

def test_verify_masking_effect_fail():
    """Test verification fails when redundant subgraph has non-zero weights."""
    masked = {
        "mol_1": {
            "subgraph_id": "sg_1",
            "weights": {"atom_0": 0.5, "atom_1": 0.0}, # Non-zero
            "is_redundant": True
        }
    }
    masks = {"sg_1": True}

    assert verify_masking_effect(masked, masks) is False

def test_io_operations(temp_dir):
    """Test loading and saving JSON files."""
    test_data = {"key": "value", "num": 42}
    path = Path(temp_dir) / "test.json"

    save_json_file(path, test_data)
    loaded = load_json_file(path)

    assert loaded == test_data
"""Unit tests for the workflow_generator (T012, T010)."""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from generators.workflow_generator import generate_workflow, calculate_sha256, validate_workflow_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure."""
    root = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(root)
    yield root
    os.chdir(original_cwd)
    shutil.rmtree(root)

def test_generate_workflow_deterministic(temp_project_root):
    """Test that generation is deterministic with the same seed."""
    seed = 42
    workflow1 = generate_workflow(workflow_id="wf_1", seed=seed)
    workflow2 = generate_workflow(workflow_id="wf_1", seed=seed)
    
    assert workflow1 == workflow2
    assert workflow1["workflow_id"] == "wf_1"
    assert "steps" in workflow1
    assert "ground_truth" in workflow1

def test_generate_workflow_structure(temp_project_root):
    """Test that generated workflow has required structure."""
    workflow = generate_workflow(workflow_id="wf_test", seed=123)
    
    assert validate_workflow_structure(workflow)
    assert "workflow_id" in workflow
    assert "agents" in workflow
    assert "steps" in workflow
    assert "ground_truth" in workflow
    assert "final_state" in workflow["ground_truth"]
    assert "decision_tree" in workflow["ground_truth"]

def test_calculate_sha256_consistency(temp_project_root):
    """Test that SHA256 calculation is consistent."""
    data = {"key": "value"}
    hash1 = calculate_sha256(json.dumps(data, sort_keys=True))
    hash2 = calculate_sha256(json.dumps(data, sort_keys=True))
    
    assert hash1 == hash2
    assert len(hash1) == 64

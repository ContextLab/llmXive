"""Unit tests for workflow_validator (T014)."""
import pytest
from generators.workflow_validator import validate_workflow, validate_workflow_file, ValidationError
import json
import tempfile
import os

def test_validate_workflow_valid():
    """Test validation of a valid workflow."""
    valid_workflow = {
        "workflow_id": "wf_123",
        "agents": ["agent_1"],
        "steps": [
            {"id": 1, "tool": "debug", "output": "out1", "decision": "continue"}
        ],
        "ground_truth": {
            "final_state": {"status": "ok"},
            "decision_tree": {"nodes": []}
        }
    }
    
    result = validate_workflow(valid_workflow)
    assert result is True

def test_validate_workflow_invalid_missing_field():
    """Test validation fails on missing required field."""
    invalid_workflow = {
        "workflow_id": "wf_123",
        "agents": ["agent_1"],
        # Missing "steps"
        "ground_truth": {"final_state": {}, "decision_tree": {}}
    }
    
    with pytest.raises(ValidationError):
        validate_workflow(invalid_workflow)

def test_validate_workflow_file(tmp_path):
    """Test validating a workflow from a file."""
    workflow = {
        "workflow_id": "wf_file",
        "agents": ["a"],
        "steps": [{"id": 1, "tool": "t", "output": "o", "decision": "c"}],
        "ground_truth": {"final_state": {}, "decision_tree": {}}
    }
    
    file_path = tmp_path / "test_wf.json"
    with open(file_path, "w") as f:
        json.dump(workflow, f)
    
    assert validate_workflow_file(str(file_path)) is True

def test_validate_workflow_file_invalid(tmp_path):
    """Test validation fails for invalid file content."""
    invalid_wf = {"missing": "fields"}
    
    file_path = tmp_path / "invalid_wf.json"
    with open(file_path, "w") as f:
        json.dump(invalid_wf, f)
    
    with pytest.raises(ValidationError):
        validate_workflow_file(str(file_path))
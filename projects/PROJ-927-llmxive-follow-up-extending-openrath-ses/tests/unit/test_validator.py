import pytest
import json
import os
from pathlib import Path
import tempfile

from generators.workflow_validator import (
    validate_workflow,
    validate_workflow_file,
    validate_workflow_batch,
    ValidationError
)

# Helper to create a minimal valid workflow
def create_minimal_valid_workflow(workflow_id="test-001"):
    return {
        "workflow_id": workflow_id,
        "timestamp": "2023-10-01T00:00:00Z",
        "agent_id": "agent-alpha",
        "decision_tree": {
            "root_id": "node-0",
            "nodes": [
                {
                    "node_id": "node-0",
                    "action_type": "tool_call",
                    "parameters": {"tool": "search", "query": "test"}
                }
            ]
        },
        "tool_outputs": [
            {
                "tool_name": "search",
                "output_data": "results",
                "timestamp": "2023-10-01T00:00:01Z"
            }
        ],
        "state_snapshots": [
            {
                "snapshot_id": "snap-0",
                "timestamp": "2023-10-01T00:00:02Z",
                "state_data": {"memory": "active"}
            }
        ]
    }

class TestWorkflowValidator:
    def test_valid_workflow_passes(self):
        workflow = create_minimal_valid_workflow()
        assert validate_workflow(workflow) is True

    def test_missing_top_level_key_raises(self):
        workflow = create_minimal_valid_workflow()
        del workflow["tool_outputs"]
        
        with pytest.raises(ValidationError) as exc_info:
            validate_workflow(workflow)
        
        assert "tool_outputs" in str(exc_info.value)

    def test_invalid_decision_tree_structure_raises(self):
        workflow = create_minimal_valid_workflow()
        workflow["decision_tree"] = {"invalid": "structure"} # Missing nodes, root_id
        
        with pytest.raises(ValidationError) as exc_info:
            validate_workflow(workflow)
        
        assert "decision_tree" in str(exc_info.value)

    def test_missing_node_keys_raises(self):
        workflow = create_minimal_valid_workflow()
        workflow["decision_tree"]["nodes"][0] = {"node_id": "node-0"} # Missing action_type, parameters
        
        with pytest.raises(ValidationError) as exc_info:
            validate_workflow(workflow)
        
        assert "Node 0" in str(exc_info.value)

    def test_missing_tool_output_keys_raises(self):
        workflow = create_minimal_valid_workflow()
        workflow["tool_outputs"][0] = {"tool_name": "search"} # Missing output_data, timestamp
        
        with pytest.raises(ValidationError) as exc_info:
            validate_workflow(workflow)
        
        assert "tool_output 0" in str(exc_info.value)

    def test_missing_state_snapshot_keys_raises(self):
        workflow = create_minimal_valid_workflow()
        workflow["state_snapshots"][0] = {"snapshot_id": "snap-0"} # Missing timestamp, state_data
        
        with pytest.raises(ValidationError) as exc_info:
            validate_workflow(workflow)
        
        assert "state_snapshot 0" in str(exc_info.value)

    def test_validate_workflow_file_valid(tmp_path):
        workflow = create_minimal_valid_workflow()
        file_path = tmp_path / "valid_workflow.json"
        with open(file_path, 'w') as f:
            json.dump(workflow, f)
        
        assert validate_workflow_file(str(file_path)) is True

    def test_validate_workflow_file_invalid(tmp_path):
        workflow = create_minimal_valid_workflow()
        del workflow["state_snapshots"]
        file_path = tmp_path / "invalid_workflow.json"
        with open(file_path, 'w') as f:
            json.dump(workflow, f)
        
        with pytest.raises(ValidationError):
            validate_workflow_file(str(file_path))

    def test_validate_workflow_file_not_found():
        with pytest.raises(FileNotFoundError):
            validate_workflow_file("/nonexistent/path/file.json")

    def test_validate_workflow_batch(tmp_path):
        # Create one valid, one invalid
        valid_wf = create_minimal_valid_workflow("valid-1")
        invalid_wf = create_minimal_valid_workflow("invalid-1")
        del invalid_wf["tool_outputs"]

        valid_path = tmp_path / "valid.json"
        invalid_path = tmp_path / "invalid.json"

        with open(valid_path, 'w') as f:
            json.dump(valid_wf, f)
        with open(invalid_path, 'w') as f:
            json.dump(invalid_wf, f)

        results = validate_workflow_batch([str(valid_path), str(invalid_path)])
        
        assert results[str(valid_path)] is True
        assert results[str(invalid_path)] is False

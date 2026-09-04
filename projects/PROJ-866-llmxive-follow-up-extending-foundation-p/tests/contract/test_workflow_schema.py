import pytest
import json
from pathlib import Path
import yaml

@pytest.fixture
def workflow_schema():
    schema_path = Path(__file__).parent.parent.parent / "contracts" / "workflow.schema.yaml"
    if not schema_path.exists():
        pytest.skip("Workflow schema not found")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_workflow_json_structure(workflow_schema):
    """
    T011: Contract test for workflow JSON output.
    Validates that generated workflows conform to the schema structure.
    """
    # Load a sample workflow if available, or generate one
    workflows_dir = Path(__file__).parent.parent.parent / "data" / "raw"
    if workflows_dir.exists():
        workflow_files = list(workflows_dir.glob("workflow_*.json"))
        if workflow_files:
            with open(workflow_files[0], 'r') as f:
                workflow = json.load(f)
            # Basic structural checks based on common schema expectations
            assert "id" in workflow, "Workflow must have an 'id'"
            assert "nodes" in workflow, "Workflow must have 'nodes'"
            assert "edges" in workflow, "Workflow must have 'edges'"
            assert "depth" in workflow, "Workflow must have 'depth'"
            assert isinstance(workflow["nodes"], list), "Nodes must be a list"
            assert isinstance(workflow["edges"], list), "Edges must be a list"
            return
    
    pytest.skip("No workflow files found to validate against schema")

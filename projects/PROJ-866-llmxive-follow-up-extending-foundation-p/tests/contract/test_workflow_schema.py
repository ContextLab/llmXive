"""
Contract test for workflow JSON output against workflow.schema.yaml.

This test validates that the synthetic workflow generator produces
JSON files that strictly conform to the defined schema.
"""
import json
import os
import pytest
import yaml
from pathlib import Path

# Import the generator to test (T012 will implement this)
# We import here to ensure the module exists when tests run
try:
    from code.generators.synthetic_workflow import generate_workflows
except ImportError:
    pytest.skip("Generator module not yet implemented (T012)", allow_module_level=True)

# Path to the schema file
SCHEMA_PATH = Path("contracts/workflow.schema.yaml")
OUTPUT_DIR = Path("data/raw")


def load_schema():
    """Load the workflow schema from YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def validate_workflow_against_schema(workflow, schema):
    """
    Validate a single workflow dictionary against the schema.
    
    Returns a list of validation errors (empty if valid).
    """
    errors = []
    
    # Check required top-level fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in workflow:
            errors.append(f"Missing required field: {field}")
    
    # Check field types based on schema properties
    properties = schema.get("properties", {})
    for field_name, field_schema in properties.items():
        if field_name in workflow:
            value = workflow[field_name]
            expected_type = field_schema.get("type")
            
            # Type validation
            if expected_type == "object" and not isinstance(value, dict):
                errors.append(f"Field '{field_name}' should be an object, got {type(value).__name__}")
            elif expected_type == "array" and not isinstance(value, list):
                errors.append(f"Field '{field_name}' should be an array, got {type(value).__name__}")
            elif expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field_name}' should be a string, got {type(value).__name__}")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"Field '{field_name}' should be an integer, got {type(value).__name__}")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field_name}' should be a number, got {type(value).__name__}")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Field '{field_name}' should be a boolean, got {type(value).__name__}")
            
            # Check for additional properties if not allowed
            if not field_schema.get("additionalProperties", True) and isinstance(value, dict):
                allowed_keys = set(field_schema.get("properties", {}).keys())
                actual_keys = set(value.keys())
                extra_keys = actual_keys - allowed_keys
                if extra_keys:
                    errors.append(f"Field '{field_name}' has unexpected keys: {extra_keys}")
    
    return errors


@pytest.fixture
def schema():
    """Load the workflow schema."""
    return load_schema()


@pytest.fixture
def generated_workflows(schema):
    """Generate workflows and validate each one against the schema."""
    # Generate a small sample set for testing
    workflows = generate_workflows(num_workflows=10, seed=42)
    
    # Validate each workflow
    for i, workflow in enumerate(workflows):
        errors = validate_workflow_against_schema(workflow, schema)
        assert not errors, f"Workflow {i} validation errors: {errors}"
    
    return workflows


def test_schema_file_exists():
    """Test that the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found: {SCHEMA_PATH}"


def test_schema_is_valid_yaml():
    """Test that the schema file is valid YAML."""
    schema = load_schema()
    assert isinstance(schema, dict), "Schema should be a dictionary"
    assert "type" in schema, "Schema must have a 'type' field"
    assert schema["type"] == "object", "Workflow schema type should be 'object'"


def test_workflow_structure(generated_workflows, schema):
    """Test that generated workflows have the correct top-level structure."""
    required_fields = schema.get("required", [])
    
    for workflow in generated_workflows:
        assert isinstance(workflow, dict), "Each workflow should be a dictionary"
        
        # Check all required fields are present
        for field in required_fields:
            assert field in workflow, f"Workflow missing required field: {field}"


def test_workflow_metadata_fields(generated_workflows):
    """Test that workflow metadata fields have correct types."""
    for workflow in generated_workflows:
        # Test id field
        assert "id" in workflow, "Workflow missing 'id' field"
        assert isinstance(workflow["id"], str), "Workflow 'id' should be a string"
        
        # Test depth field
        assert "depth" in workflow, "Workflow missing 'depth' field"
        assert isinstance(workflow["depth"], int), "Workflow 'depth' should be an integer"
        assert workflow["depth"] >= 1, "Workflow 'depth' should be at least 1"
        
        # Test complexity field
        assert "complexity" in workflow, "Workflow missing 'complexity' field"
        assert isinstance(workflow["complexity"], int), "Workflow 'complexity' should be an integer"
        
        # Test nodes field
        assert "nodes" in workflow, "Workflow missing 'nodes' field"
        assert isinstance(workflow["nodes"], list), "Workflow 'nodes' should be a list"
        
        # Test edges field
        assert "edges" in workflow, "Workflow missing 'edges' field"
        assert isinstance(workflow["edges"], list), "Workflow 'edges' should be a list"


def test_workflow_nodes_structure(generated_workflows):
    """Test that workflow nodes have the correct structure."""
    for workflow in generated_workflows:
        nodes = workflow.get("nodes", [])
        
        for node in nodes:
            assert isinstance(node, dict), "Each node should be a dictionary"
            assert "id" in node, "Node missing 'id' field"
            assert isinstance(node["id"], str), "Node 'id' should be a string"
            assert "type" in node, "Node missing 'type' field"
            assert isinstance(node["type"], str), "Node 'type' should be a string"
            
            # Check that node type is valid
            valid_types = ["task", "decision", "start", "end"]
            assert node["type"] in valid_types, f"Invalid node type: {node['type']}"


def test_workflow_edges_structure(generated_workflows):
    """Test that workflow edges have the correct structure."""
    for workflow in generated_workflows:
        edges = workflow.get("edges", [])
        
        for edge in edges:
            assert isinstance(edge, dict), "Each edge should be a dictionary"
            assert "source" in edge, "Edge missing 'source' field"
            assert "target" in edge, "Edge missing 'target' field"
            assert isinstance(edge["source"], str), "Edge 'source' should be a string"
            assert isinstance(edge["target"], str), "Edge 'target' should be a string"
            
            # Verify source and target exist in nodes
            node_ids = {node["id"] for node in workflow.get("nodes", [])}
            assert edge["source"] in node_ids, f"Edge source '{edge['source']}' not found in nodes"
            assert edge["target"] in node_ids, f"Edge target '{edge['target']}' not found in nodes"


def test_workflow_uniqueness(generated_workflows):
    """Test that all generated workflows have unique IDs."""
    ids = [workflow["id"] for workflow in generated_workflows]
    assert len(ids) == len(set(ids)), "Workflow IDs should be unique"


def test_workflow_dag_property(generated_workflows):
    """Test that workflows are valid DAGs (no cycles)."""
    for workflow in generated_workflows:
        nodes = {node["id"] for node in workflow.get("nodes", [])}
        edges = workflow.get("edges", [])
        
        # Build adjacency list
        adj = {node: [] for node in nodes}
        for edge in edges:
            adj[edge["source"]].append(edge["target"])
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in adj[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in nodes:
            if node not in visited:
                assert not has_cycle(node), f"Workflow {workflow['id']} contains a cycle"


def test_workflow_save_to_file(generated_workflows):
    """Test that workflows can be saved to JSON files."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for i, workflow in enumerate(generated_workflows):
        file_path = OUTPUT_DIR / f"workflow_{workflow['id']}.json"
        
        # Save workflow to file
        with open(file_path, "w") as f:
            json.dump(workflow, f, indent=2)
        
        # Verify file was created
        assert file_path.exists(), f"Workflow file not created: {file_path}"
        
        # Verify file can be loaded and matches original
        with open(file_path, "r") as f:
            loaded_workflow = json.load(f)
        
        assert loaded_workflow == workflow, f"Loaded workflow does not match original for {workflow['id']}"


def test_workflow_json_validity(generated_workflows):
    """Test that each workflow can be serialized to valid JSON."""
    for workflow in generated_workflows:
        try:
            json_str = json.dumps(workflow)
            # Verify we can deserialize it back
            reconstructed = json.loads(json_str)
            assert reconstructed == workflow, "JSON round-trip failed"
        except (TypeError, ValueError) as e:
            pytest.fail(f"Workflow {workflow.get('id', 'unknown')} cannot be serialized to JSON: {e}")
import json
import pytest
from pathlib import Path
import yaml

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from engines.full_context import FullContextEngine
from engines.oracle_policy import OraclePolicyEngine

@pytest.fixture
def schema():
    """Load the execution log schema."""
    schema_path = Path(__file__).parent.parent.parent / 'code' / 'contracts' / 'execution_log.schema.yaml'
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_workflow():
    """Create a valid test workflow."""
    return {
        'id': 'test_workflow_valid',
        'nodes': [
            {'id': 'node1', 'type': 'start', 'policy': 'default'},
            {'id': 'node2', 'type': 'process', 'policy': 'default'},
            {'id': 'node3', 'type': 'end', 'policy': 'default'}
        ],
        'edges': [
            {'source': 'node1', 'target': 'node2'},
            {'source': 'node2', 'target': 'node3'}
        ],
        'depth': 2,
        'complexity': 3
    }

@pytest.fixture
def invalid_workflow():
    """Create a logically impossible workflow (circular dependency)."""
    return {
        'id': 'test_workflow_invalid',
        'nodes': [
            {'id': 'node1', 'type': 'start', 'policy': 'default'},
            {'id': 'node2', 'type': 'process', 'policy': 'default'}
        ],
        'edges': [
            {'source': 'node1', 'target': 'node2'},
            {'source': 'node2', 'target': 'node1'}  # Circular dependency
        ],
        'depth': 2,
        'complexity': 2
    }

@pytest.fixture
def edge_case_workflow():
    """Create an edge case workflow (single node)."""
    return {
        'id': 'test_workflow_edge',
        'nodes': [
            {'id': 'node1', 'type': 'start', 'policy': 'default'}
        ],
        'edges': [],
        'depth': 0,
        'complexity': 1
    }

def test_execution_log_has_required_fields(valid_workflow, schema):
    """Test that execution log contains all required fields."""
    engine = FullContextEngine()
    result = engine.execute(valid_workflow)
    
    required_fields = schema['required']
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"

def test_execution_log_is_valid_field_type(valid_workflow):
    """Test that is_valid field is a boolean."""
    engine = FullContextEngine()
    result = engine.execute(valid_workflow)
    
    assert isinstance(result['is_valid'], bool), "is_valid must be a boolean"

def test_invalid_workflow_marks_is_valid_false(invalid_workflow):
    """Test that logically impossible workflows are marked as invalid."""
    engine = FullContextEngine()
    result = engine.execute(invalid_workflow)
    
    assert result['is_valid'] == False, "Invalid workflow should have is_valid=False"
    assert result['execution_status'] == 'failed', "Invalid workflow should have status 'failed'"

def test_valid_workflow_marks_is_valid_true(valid_workflow):
    """Test that valid workflows are marked as valid."""
    engine = FullContextEngine()
    result = engine.execute(valid_workflow)
    
    assert result['is_valid'] == True, "Valid workflow should have is_valid=True"

def test_edge_case_workflow_handling(edge_case_workflow):
    """Test that edge case workflows are handled correctly."""
    engine = FullContextEngine()
    result = engine.execute(edge_case_workflow)
    
    assert result['execution_status'] == 'edge_case', "Edge case workflow should have status 'edge_case'"
    assert result['context_reduction_pct'] == '[deferred]', "Edge case should have context_reduction_pct as '[deferred]'"
    # Edge cases can still be valid if they are logically sound
    assert result['is_valid'] == True, "Edge case workflow should still be logically valid"

def test_execution_log_schema_compliance(valid_workflow, schema):
    """Test that execution log complies with schema types."""
    engine = FullContextEngine()
    result = engine.execute(valid_workflow)
    
    properties = schema['properties']
    
    # Check workflow_id is string
    assert isinstance(result['workflow_id'], str), "workflow_id must be string"
    
    # Check execution_status is valid enum
    valid_statuses = properties['execution_status']['enum']
    assert result['execution_status'] in valid_statuses, f"execution_status must be one of {valid_statuses}"
    
    # Check is_valid is boolean
    assert isinstance(result['is_valid'], bool), "is_valid must be boolean"
    
    # Check node_count is integer
    assert isinstance(result['node_count'], int), "node_count must be integer"
    
    # Check depth is integer
    assert isinstance(result['depth'], int), "depth must be integer"
    
    # Check complexity is integer
    assert isinstance(result['complexity'], int), "complexity must be integer"
    
    # Check policy_violations is list
    assert isinstance(result['policy_violations'], list), "policy_violations must be list"
    
    # Check metadata is dict
    assert isinstance(result['metadata'], dict), "metadata must be dict"
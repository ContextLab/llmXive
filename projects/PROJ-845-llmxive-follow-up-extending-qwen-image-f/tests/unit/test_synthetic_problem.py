import json
import pytest
from code.models.synthetic_problem import SyntheticProblem

def test_synthetic_problem_creation():
    """Test basic instantiation of SyntheticProblem."""
    problem = SyntheticProblem(
        id="test-001",
        premises=["A is true", "B is false"],
        operators=["AND", "NOT"],
        solution="Result X",
        entropy_level="High",
        metadata={"source": "generator_v1"}
    )
    
    assert problem.id == "test-001"
    assert len(problem.premises) == 2
    assert problem.entropy_level == "High"
    assert problem.metadata["source"] == "generator_v1"

def test_to_dict_roundtrip():
    """Test that to_dict produces a valid dictionary."""
    problem = SyntheticProblem(
        id="test-002",
        premises=["X > 5"],
        operators=["GREATER_THAN"],
        solution="True",
        entropy_level="Low",
        metadata={}
    )
    
    data = problem.to_dict()
    assert isinstance(data, dict)
    assert data["id"] == "test-002"
    assert data["solution"] == "True"
    assert "entropy_level" in data

def test_from_dict_creation():
    """Test that from_dict correctly reconstructs the object."""
    raw_data = {
        "id": "test-003",
        "premises": ["P1", "P2"],
        "operators": ["OR"],
        "solution": "Q",
        "entropy_level": "Target",
        "metadata": {"key": "value"}
    }
    
    problem = SyntheticProblem.from_dict(raw_data)
    assert problem.id == "test-003"
    assert problem.premises == ["P1", "P2"]
    assert problem.metadata["key"] == "value"

def test_json_serialization():
    """Test JSON string conversion methods."""
    problem = SyntheticProblem(
        id="test-004",
        premises=["A"],
        operators=["NOT"],
        solution="B",
        entropy_level="High",
        metadata={"nested": {"a": 1}}
    )
    
    json_str = problem.to_json()
    assert isinstance(json_str, str)
    
    # Verify it is valid JSON
    parsed = json.loads(json_str)
    assert parsed["id"] == "test-004"
    
    # Test roundtrip via JSON
    restored = SyntheticProblem.from_json(json_str)
    assert restored.id == problem.id
    assert restored.metadata["nested"]["a"] == 1

def test_structure_hash():
    """Test that structure hash is deterministic and based on content."""
    p1 = SyntheticProblem(
        id="test-005",
        premises=["A"],
        operators=["AND"],
        solution="B",
        entropy_level="Low"
    )
    
    p2 = SyntheticProblem(
        id="test-006",
        premises=["A"],
        operators=["AND"],
        solution="B",
        entropy_level="High"
    )
    
    # Hash should be same because premises/operators are same
    assert p1.compute_structure_hash() == p2.compute_structure_hash()
    
    # Different premises should yield different hash
    p3 = SyntheticProblem(
        id="test-007",
        premises=["C"],
        operators=["AND"],
        solution="B",
        entropy_level="Low"
    )
    assert p1.compute_structure_hash() != p3.compute_structure_hash()
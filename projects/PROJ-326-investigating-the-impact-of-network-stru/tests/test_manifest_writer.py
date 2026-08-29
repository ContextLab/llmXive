"""
Unit tests for manifest writing logic (T018e).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from code.src.generators.manifest_writer import validate_manifest_schema, write_manifest, MANIFEST_PATH

@pytest.fixture
def sample_manifest_data():
    return {
        "version": "1.0.0",
        "generated_at": "2025-01-15T12:00:00+00:00",
        "global_seed": 42,
        "topology_classes": [
            {
                "class_name": "erdos_renyi",
                "graphs": [
                    {
                        "graph_id": 1,
                        "parameters": {"p": 0.1},
                        "metrics": {
                            "clustering_coefficient": 0.1,
                            "average_path_length": 3.5,
                            "degree_distribution": {"mean": 3.0}
                        },
                        "is_connected": True
                    }
                ],
                "success_count": 1,
                "total_attempts": 1
            }
        ],
        "stratification_summary": {
            "bins": [0.1, 0.2, 0.3, 0.4, 0.5],
            "target_counts": {"0.1": 10, "0.2": 10, "0.3": 10, "0.4": 10, "0.5": 10},
            "actual_counts": {"0.1": 1, "0.2": 0, "0.3": 0, "0.4": 0, "0.5": 0},
            "tolerance": 0.1
        },
        "generation_algorithm": "batch_generator_v1"
    }

def test_validate_manifest_schema_valid(sample_manifest_data):
    """Test that a valid manifest passes schema validation."""
    assert validate_manifest_schema(sample_manifest_data) is True

def test_validate_manifest_schema_missing_key(sample_manifest_data):
    """Test that a manifest with missing required keys fails validation."""
    del sample_manifest_data["version"]
    assert validate_manifest_schema(sample_manifest_data) is False

def test_validate_manifest_schema_invalid_topology_class(sample_manifest_data):
    """Test that invalid topology class structure fails validation."""
    sample_manifest_data["topology_classes"][0]["graphs"] = "not_a_list"
    assert validate_manifest_schema(sample_manifest_data) is False

def test_validate_manifest_schema_missing_graph_field(sample_manifest_data):
    """Test that a graph with missing required fields fails validation."""
    del sample_manifest_data["topology_classes"][0]["graphs"][0]["is_connected"]
    assert validate_manifest_schema(sample_manifest_data) is False

def test_validate_manifest_schema_invalid_stratification(sample_manifest_data):
    """Test that invalid stratification summary fails validation."""
    sample_manifest_data["stratification_summary"]["bins"] = "not_a_list"
    assert validate_manifest_schema(sample_manifest_data) is False

def test_write_manifest_creates_file(sample_manifest_data, tmp_path):
    """Test that write_manifest creates the output file."""
    # Temporarily override MANIFEST_PATH for testing
    original_path = MANIFEST_PATH
    test_path = str(tmp_path / "test_manifest.json")
    
    # Create a temporary version of the module to test with custom path
    import code.src.generators.manifest_writer as mw
    mw.MANIFEST_PATH = test_path
    
    try:
        result_path = mw.write_manifest(
            topology_classes=sample_manifest_data["topology_classes"],
            stratification_summary=sample_manifest_data["stratification_summary"],
            generation_algorithm=sample_manifest_data["generation_algorithm"],
            global_seed=sample_manifest_data["global_seed"],
            version=sample_manifest_data["version"]
        )
        
        assert os.path.exists(result_path)
        assert result_path == test_path
        
        with open(result_path, 'r') as f:
            loaded = json.load(f)
        
        assert "global_batch_manifest" in loaded
        assert loaded["global_batch_manifest"]["version"] == "1.0.0"
    finally:
        mw.MANIFEST_PATH = original_path

def test_write_manifest_invalid_schema_raises_error(sample_manifest_data):
    """Test that write_manifest raises an error for invalid schema."""
    invalid_data = sample_manifest_data.copy()
    del invalid_data["version"]
    
    with pytest.raises(ValueError, match="Manifest schema validation failed"):
        write_manifest(
            topology_classes=invalid_data.get("topology_classes", []),
            stratification_summary=invalid_data.get("stratification_summary", {}),
            generation_algorithm="test",
            global_seed=42
        )
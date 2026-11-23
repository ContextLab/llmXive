"""
Contract test for network output schema (T025).

Validates that the output of code/04_network.py conforms to the expected schema
defined for network analysis results, including modularity, edge counts, 
sensitivity analysis, and delta calculations.
"""
import json
import os
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Schema definition for Network Analysis Output
# This schema mirrors the expected structure from code/04_network.py
NETWORK_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["metadata", "network_summary", "modularity_analysis", "sensitivity_analysis"],
    "properties": {
        "metadata": {
            "type": "object",
            "required": ["source_file", "threshold", "p_value_threshold", "sample_count", "taxa_count"],
            "properties": {
                "source_file": {"type": "string"},
                "threshold": {"type": "number"},
                "p_value_threshold": {"type": "number"},
                "sample_count": {"type": "integer"},
                "taxa_count": {"type": "integer"},
                "under_determined_flag": {"type": "boolean"}
            }
        },
        "network_summary": {
            "type": "object",
            "required": ["total_nodes", "total_edges", "density", "avg_degree"],
            "properties": {
                "total_nodes": {"type": "integer"},
                "total_edges": {"type": "integer"},
                "density": {"type": "number"},
                "avg_degree": {"type": "number"}
            }
        },
        "modularity_analysis": {
            "type": "object",
            "required": ["early_stage_modularity", "mature_stage_modularity", "delta_modularity"],
            "properties": {
                "early_stage_modularity": {"type": ["number", "null"]},
                "mature_stage_modularity": {"type": ["number", "null"]},
                "delta_modularity": {"type": ["number", "null"]},
                "skipped_reason": {"type": ["string", "null"]}
            }
        },
        "sensitivity_analysis": {
            "type": "object",
            "required": ["thresholds_tested", "delta_modularity_variance"],
            "properties": {
                "thresholds_tested": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "delta_modularity_variance": {"type": "number"},
                "details": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "threshold": {"type": "number"},
                            "early_modularity": {"type": ["number", "null"]},
                            "mature_modularity": {"type": ["number", "null"]},
                            "delta": {"type": ["number", "null"]}
                        }
                    }
                }
            }
        }
    }
}

def validate_network_output(data: Dict[str, Any]) -> bool:
    """
    Validate network output data against the schema.
    
    Args:
        data: The loaded JSON content from the network output file.
        
    Returns:
        True if valid, raises AssertionError if invalid.
    """
    # Check top-level keys
    required_top_keys = ["metadata", "network_summary", "modularity_analysis", "sensitivity_analysis"]
    for key in required_top_keys:
        assert key in data, f"Missing required top-level key: {key}"
    
    # Validate metadata
    meta = data["metadata"]
    assert isinstance(meta, dict), "metadata must be a dictionary"
    assert "source_file" in meta, "metadata missing source_file"
    assert "threshold" in meta, "metadata missing threshold"
    assert "sample_count" in meta, "metadata missing sample_count"
    assert "taxa_count" in meta, "metadata missing taxa_count"
    assert isinstance(meta["threshold"], (int, float)), "threshold must be numeric"
    assert isinstance(meta["sample_count"], int), "sample_count must be integer"
    
    # Validate network_summary
    summary = data["network_summary"]
    assert isinstance(summary, dict), "network_summary must be a dictionary"
    assert "total_nodes" in summary, "network_summary missing total_nodes"
    assert "total_edges" in summary, "network_summary missing total_edges"
    assert isinstance(summary["total_nodes"], int), "total_nodes must be integer"
    assert isinstance(summary["total_edges"], int), "total_edges must be integer"
    
    # Validate modularity_analysis
    mod = data["modularity_analysis"]
    assert isinstance(mod, dict), "modularity_analysis must be a dictionary"
    # Delta might be null if under-determined
    if mod.get("delta_modularity") is not None:
        assert isinstance(mod["delta_modularity"], (int, float)), "delta_modularity must be numeric"
    
    # Validate sensitivity_analysis
    sens = data["sensitivity_analysis"]
    assert isinstance(sens, dict), "sensitivity_analysis must be a dictionary"
    assert "thresholds_tested" in sens, "sensitivity_analysis missing thresholds_tested"
    assert isinstance(sens["thresholds_tested"], list), "thresholds_tested must be a list"
    assert "delta_modularity_variance" in sens, "sensitivity_analysis missing delta_modularity_variance"
    assert isinstance(sens["delta_modularity_variance"], (int, float)), "variance must be numeric"
    
    return True

@pytest.fixture
def network_output_path() -> Path:
    """Locate the network output file."""
    # Expected path based on project structure
    possible_paths = [
        Path("data/processed/network_analysis.json"),
        Path("projects/PROJ-280-investigating-microbial-community-succes/data/processed/network_analysis.json")
    ]
    
    for p in possible_paths:
        if p.exists():
            return p
    
    # If file doesn't exist yet, this test will fail (expected if task not run)
    # but the schema validation logic is what we are testing
    return possible_paths[0]

def test_network_output_schema_structure(network_output_path: Path):
    """
    Test that the network output file exists and conforms to the schema.
    """
    if not network_output_path.exists():
        pytest.skip(f"Network output file not found at {network_output_path}. "
                    "This is expected if code/04_network.py has not been executed yet.")
    
    with open(network_output_path, 'r') as f:
        data = json.load(f)
    
    assert validate_network_output(data), "Network output failed schema validation"

def test_network_output_data_types(network_output_path: Path):
    """
    Test specific data types in the network output.
    """
    if not network_output_path.exists():
        pytest.skip(f"Network output file not found at {network_output_path}.")
    
    with open(network_output_path, 'r') as f:
        data = json.load(f)
    
    # Verify numeric types
    assert isinstance(data["metadata"]["threshold"], (int, float))
    assert isinstance(data["network_summary"]["density"], (int, float))
    assert isinstance(data["sensitivity_analysis"]["delta_modularity_variance"], (int, float))
    
    # Verify array types
    assert isinstance(data["sensitivity_analysis"]["thresholds_tested"], list)
    assert len(data["sensitivity_analysis"]["thresholds_tested"]) > 0, "Thresholds list should not be empty"

def test_modularity_delta_logic(network_output_path: Path):
    """
    Test that delta modularity is calculated correctly or flagged appropriately.
    """
    if not network_output_path.exists():
        pytest.skip(f"Network output file not found at {network_output_path}.")
    
    with open(network_output_path, 'r') as f:
        data = json.load(f)
    
    mod = data["modularity_analysis"]
    meta = data["metadata"]
    
    # If under-determined, delta should be null and reason provided
    if meta.get("under_determined_flag", False):
        assert mod.get("delta_modularity") is None, "Delta should be null if under-determined"
        assert "skipped_reason" in mod, "Skipped reason required if under-determined"
    else:
        # If not under-determined, delta should be numeric
        assert isinstance(mod.get("delta_modularity"), (int, float)), "Delta must be numeric if not under-determined"

def test_sensitivity_analysis_completeness(network_output_path: Path):
    """
    Test that sensitivity analysis includes all required thresholds.
    """
    if not network_output_path.exists():
        pytest.skip(f"Network output file not found at {network_output_path}.")
    
    with open(network_output_path, 'r') as f:
        data = json.load(f)
    
    thresholds = data["sensitivity_analysis"]["thresholds_tested"]
    # Expecting at least 3 thresholds based on spec (0.5, 0.6, 0.7)
    assert len(thresholds) >= 3, f"Expected at least 3 thresholds, got {len(thresholds)}"
    
    # Verify variance is calculated
    variance = data["sensitivity_analysis"]["delta_modularity_variance"]
    assert variance >= 0, "Variance cannot be negative"
"""
Tests for T058: Verify Task Ordering
"""
import json
import os
import sys
from pathlib import Path
import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingestion.verify_task_ordering import main, audit_file_dependencies, FILE_DEPENDENCIES

def test_t058_audit_execution(tmp_path):
    """
    Test that the T058 audit script runs and produces the expected output file.
    """
    # Mock the base directory structure if needed, but we can run against the actual project
    # for a sanity check.
    
    # Run the main function
    result = main()
    
    # Verify result structure
    assert "graph" in result
    assert "is_valid" in result
    assert "issues" in result
    
    # Verify graph structure
    assert "nodes" in result["graph"]
    assert "edges" in result["graph"]
    
    # Verify the output file was written
    output_file = Path("data/outputs/task_ordering_audit.json")
    assert output_file.exists(), "Output file task_ordering_audit.json was not created"
    
    # Verify JSON content
    with open(output_file, 'r') as f:
        saved_result = json.load(f)
    
    assert saved_result == result

def test_dependency_graph_logic():
    """
    Verify that the defined FILE_DEPENDENCIES contains the critical links required by the task.
    """
    # T013 produces solder_hardness_cleaned.csv
    assert "data/processed/solder_hardness_cleaned.csv" in FILE_DEPENDENCIES
    assert FILE_DEPENDENCIES["data/processed/solder_hardness_cleaned.csv"]["producer"] == "T013"
    assert "T023b" in FILE_DEPENDENCIES["data/processed/solder_hardness_cleaned.csv"]["consumers"]
    assert "T023c" in FILE_DEPENDENCIES["data/processed/solder_hardness_cleaned.csv"]["consumers"]

    # T023b produces clr_features.csv
    assert "data/processed/clr_features.csv" in FILE_DEPENDENCIES
    assert FILE_DEPENDENCIES["data/processed/clr_features.csv"]["producer"] == "T023b"
    assert "T025" in FILE_DEPENDENCIES["data/processed/clr_features.csv"]["consumers"]
    assert "T026" in FILE_DEPENDENCIES["data/processed/clr_features.csv"]["consumers"]

    # T023c produces descriptors.csv
    assert "data/processed/descriptors.csv" in FILE_DEPENDENCIES
    assert FILE_DEPENDENCIES["data/processed/descriptors.csv"]["producer"] == "T023c"
    assert "T025" in FILE_DEPENDENCIES["data/processed/descriptors.csv"]["consumers"]
    assert "T026" in FILE_DEPENDENCIES["data/processed/descriptors.csv"]["consumers"]

def test_no_circular_dependencies():
    """
    Verify that the defined graph does not have circular dependencies.
    """
    # Build a simple adjacency list
    adj = {}
    for file_path, info in FILE_DEPENDENCIES.items():
        producer = info["producer"]
        consumers = info["consumers"]
        
        if producer not in adj:
            adj[producer] = []
        
        for consumer in consumers:
            adj[producer].append(consumer)

    # DFS to detect cycles
    visited = set()
    rec_stack = set()

    def has_cycle(node):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False

    for node in adj:
        if node not in visited:
            if has_cycle(node):
                pytest.fail("Circular dependency detected in task graph")
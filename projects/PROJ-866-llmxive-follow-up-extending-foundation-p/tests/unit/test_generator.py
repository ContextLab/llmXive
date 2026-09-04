import pytest
import json
import os
from pathlib import Path
from generators.synthetic_workflow import SyntheticWorkflowGenerator

@pytest.fixture
def generator():
    return SyntheticWorkflowGenerator(seed=42)

def test_graph_variance(generator):
    """
    T010: Verify exactly 20 unique depth levels exist and each level has at least 25 workflows.
    """
    # Generate a substantial set to ensure coverage
    workflows, _ = generator.generate_workflows(num_workflows=500)
    
    depth_counts = {}
    for wf in workflows:
        depth = wf.get("depth", 0)
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    
    unique_depths = set(depth_counts.keys())
    
    # Assert exactly 20 unique depth levels (1-20)
    assert len(unique_depths) == 20, f"Expected 20 unique depths, found {len(unique_depths)}: {unique_depths}"
    
    # Assert each depth level has at least 25 workflows
    for depth in range(1, 21):
        count = depth_counts.get(depth, 0)
        assert count >= 25, f"Depth {depth} has only {count} workflows, expected >= 25"

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from generators.synthetic_workflow import SyntheticWorkflowGenerator


def test_graph_variance():
    """Test that generated workflows have the expected variance."""
    generator = SyntheticWorkflowGenerator(seed=42)
    workflows = generator.generate_workflows(500)

    # Check unique depth levels
    depths = set()
    for w in workflows:
        depths.add(w["metadata"]["depth"])

    assert len(depths) == 20, f"Expected 20 unique depths, got {len(depths)}"

    # Check minimum workflows per depth
    depth_counts = {}
    for w in workflows:
        d = w["metadata"]["depth"]
        depth_counts[d] = depth_counts.get(d, 0) + 1

    for d, count in depth_counts.items():
        assert count >= 25, f"Depth {d} has only {count} workflows, expected >= 25"

    print("All variance tests passed.")


if __name__ == "__main__":
    test_graph_variance()

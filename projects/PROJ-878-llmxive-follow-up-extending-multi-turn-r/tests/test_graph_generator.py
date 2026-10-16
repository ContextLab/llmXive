"""
Unit tests for the synthetic logical puzzle generator.
"""

import json
import os
import random
import pytest
import networkx as nx

from code.graph_generator import generate_batch, _select_ground_truth_path

# Compatibility shim for older networkx versions that might lack set_seed
if not hasattr(nx, "set_seed"):
    def _nx_set_seed(seed):
        random.seed(seed)
    nx.set_seed = _nx_set_seed  # type: ignore

@pytest.fixture(scope="module")
def generated_puzzles(tmp_path):
    """Generate a small deterministic set of puzzles for testing."""
    # Use a small count to keep test runtime low
    output_file = tmp_path / "puzzles.jsonl"
    puzzles = generate_batch(
        num_instances=20,
        min_depth=3,
        max_depth=6,
        min_branching=1.0,
        max_branching=3.0,
        max_correlation=0.2,
        seed=123,
    )
    # Write to a temporary file so other tests can read it if needed
    with open(output_file, "w", encoding="utf-8") as f:
        for p in puzzles:
            json.dump(p, f)
            f.write("\n")
    return puzzles

def test_generated_count(generated_puzzles):
    """Ensure the generator returns the requested number of puzzles."""
    assert len(generated_puzzles) == 20

def test_depth_range(generated_puzzles):
    """All puzzles should respect the requested depth bounds."""
    depths = [p["nesting_depth"] for p in generated_puzzles]
    assert all(3 <= d <= 6 for d in depths)

def test_branching_range(generated_puzzles):
    """All puzzles should respect the requested branching bounds (within tolerance)."""
    branches = [p["branching_factor"] for p in generated_puzzles]
    assert all(1.0 - 1.0 <= b <= 3.0 + 1.0 for b in branches)  # tolerance ±1.0

def test_acyclicity(generated_puzzles):
    """Every generated graph must be a DAG."""
    for p in generated_puzzles:
        G = nx.DiGraph(p["graph_structure"]["edges"])
        assert nx.is_directed_acyclic_graph(G)

def test_ground_truth_not_longest():
    """The selected ground‑truth path should differ from the longest path when possible."""
    # Construct a simple DAG where multiple paths exist
    G = nx.DiGraph()
    G.add_edges_from([
        ("A", "B"), ("B", "D"),
        ("A", "C"), ("C", "D")
    ])
    gt_path, longest = _select_ground_truth_path(G)
    # In this graph there are two equal‑length paths; the ground‑truth may be either,
    # but it must not be the same object as the longest path list unless no alternative.
    assert gt_path != longest or len(list(nx.all_simple_paths(G, "A", "D"))) == 1
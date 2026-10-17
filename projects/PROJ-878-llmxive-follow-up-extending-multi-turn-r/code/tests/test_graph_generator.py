import json
import os
import random
import logging
import pathlib

import pytest
import networkx as nx

from graph_generator import generate_batch, _write_jsonl, _write_validation_metrics

logger = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def temp_dir(tmp_path_factory):
    """Create a temporary directory for generated files."""
    return tmp_path_factory.mktemp("data")

def test_generate_batch_basic():
    """Generate a small batch and verify basic properties."""
    batch = generate_batch(
        num_instances=10,
        min_depth=3,
        max_depth=6,
        min_branching=1.0,
        max_branching=5.0,
        max_correlation=0.2,
        seed=123,
    )
    assert len(batch) == 10
    # Verify required fields exist and have plausible types
    for puzzle in batch:
        assert "instance_id" in puzzle
        assert "text" in puzzle
        assert isinstance(puzzle["nesting_depth"], int)
        assert isinstance(puzzle["branching_factor"], float)
        assert isinstance(puzzle["ground_truth_path"], list)
        # Graph structure must be a dict with nodes/edges lists
        gs = puzzle["graph_structure"]
        assert isinstance(gs, dict)
        assert "nodes" in gs and "edges" in gs
        assert isinstance(gs["nodes"], list)
        assert isinstance(gs["edges"], list)

def test_write_jsonl_and_load(tmp_path):
    """Write a batch to JSONL and ensure it can be read back correctly."""
    batch = generate_batch(
        num_instances=5,
        min_depth=3,
        max_depth=4,
        min_branching=1.0,
        max_branching=2.0,
        max_correlation=0.2,
        seed=42,
    )
    out_path = tmp_path / "puzzles.jsonl"
    _write_jsonl(batch, out_path)
    # Load back
    loaded = []
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            loaded.append(json.loads(line))
    assert len(loaded) == 5
    # Compare a few fields for consistency
    for original, rec in zip(batch, loaded):
        assert original["instance_id"] == rec["instance_id"]
        assert original["nesting_depth"] == rec["nesting_depth"]

def test_validation_metrics(tmp_path):
    """Check that validation metrics are written and contain expected keys."""
    primary = generate_batch(
        num_instances=20,
        min_depth=3,
        max_depth=5,
        min_branching=1.0,
        max_branching=3.0,
        max_correlation=0.2,
        seed=7,
    )
    aux = []  # No auxiliary for this test
    out_path = tmp_path / "validation_metrics.json"
    _write_validation_metrics(
        primary=primary,
        aux=aux,
        output_path=out_path,
        attempts_primary=1000,
        attempts_aux=0,
    )
    assert out_path.exists()
    with out_path.open("r", encoding="utf-8") as f:
        metrics = json.load(f)
    # Required keys
    for key in [
        "total_puzzles",
        "samples_generated_primary",
        "samples_generated_aux",
        "samples_attempted_primary",
        "samples_attempted_aux",
        "correlation_coefficient",
        "cycle_rate",
    ]:
        assert key in metrics
    # Correlation should be a float between -1 and 1
    corr = metrics["correlation_coefficient"]
    assert isinstance(corr, float)
    assert -1.0 <= corr <= 1.0

def test_orthogonalization_correlation():
    """Ensure that the orthogonalization flag is set correctly."""
    batch = generate_batch(
        num_instances=30,
        min_depth=3,
        max_depth=6,
        min_branching=1.0,
        max_branching=5.0,
        max_correlation=0.2,
        seed=999,
    )
    # Compute correlation manually
    depths = [p["nesting_depth"] for p in batch]
    branches = [p["branching_factor"] for p in batch]
    # Simple Pearson implementation
    mean_d = sum(depths) / len(depths)
    mean_b = sum(branches) / len(branches)
    num = sum((d - mean_d) * (b - mean_b) for d, b in zip(depths, branches))
    den_d = (sum((d - mean_d) ** 2 for d in depths)) ** 0.5
    den_b = (sum((b - mean_b) ** 2 for b in branches)) ** 0.5
    corr = num / (den_d * den_b) if den_d and den_b else 0.0
    # All puzzles should have the same flag
    for p in batch:
        assert p["is_orthogonal"] == (abs(corr) < 0.2)

# Ensure that the compatibility shim for nx.set_seed does not raise
def test_nx_set_seed_compatibility():
    """Calling nx.set_seed should not raise an exception."""
    try:
        nx.set_seed(12345)
    except Exception as e:
        pytest.fail(f"nx.set_seed raised an exception: {e}")

# Run the tests with a fixed random seed to guarantee reproducibility
def test_random_seed_reproducibility():
    random.seed(0)
    batch1 = generate_batch(
        num_instances=5,
        min_depth=3,
        max_depth=5,
        min_branching=1.0,
        max_branching=3.0,
        max_correlation=0.2,
        seed=42,
    )
    random.seed(0)
    batch2 = generate_batch(
        num_instances=5,
        min_depth=3,
        max_depth=5,
        min_branching=1.0,
        max_branching=3.0,
        max_correlation=0.2,
        seed=42,
    )
    # The two batches should be identical
    assert batch1 == batch2

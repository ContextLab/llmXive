import json
import os
import random
import logging
import pathlib
from typing import List, Dict, Any

import pytest
import networkx as nx
import numpy as np

from code.graph_generator import generate_batch, _write_jsonl, _write_validation_metrics

logger = logging.getLogger(__name__)

# --- Schema Definition ---
# Based on T003 requirements and code/graph_generator.py implementation
REQUIRED_SCHEMA_KEYS = {
    "instance_id": str,
    "text": str,
    "ground_truth_path": list,
    "nesting_depth": int,
    "branching_factor": float,
    "graph_structure": dict,
    "is_orthogonal": bool,
    "is_acyclic": bool,
    "is_solvable": bool,
    "text_generation_method": str,
    "seed": (int, type(None)),
}

def validate_puzzle_schema(puzzle: Dict[str, Any]):
    """Validates that a puzzle instance conforms to the SyntheticPuzzle schema."""
    for key, expected_type in REQUIRED_SCHEMA_KEYS.items():
        assert key in puzzle, f"Missing required key: {key}"
        assert isinstance(puzzle[key], expected_type), (
            f"Key {key} has type {type(puzzle[key])}, expected {expected_type}"
        )
    
    # Deep check for graph_structure
    gs = puzzle["graph_structure"]
    assert "nodes" in gs and "edges" in gs, "graph_structure must contain 'nodes' and 'edges'"
    assert isinstance(gs["nodes"], list), "graph_structure['nodes'] must be a list"
    assert isinstance(gs["edges"], list), "graph_structure['edges'] must be a list"

def calculate_pearson_correlation(x: List[float], y: List[float]) -> float:
    """Helper to calculate Pearson correlation coefficient."""
    if len(x) < 2:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])

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
    for puzzle in batch:
        validate_puzzle_schema(puzzle)

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
    
    loaded = []
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            loaded.append(json.loads(line))
    
    assert len(loaded) == 5
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
    aux = []
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
    
    assert -1.0 <= metrics["correlation_coefficient"] <= 1.0

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
    depths = [p["nesting_depth"] for p in batch]
    branches = [p["branching_factor"] for p in batch]
    corr = calculate_pearson_correlation(depths, branches)
    
    for p in batch:
        assert p["is_orthogonal"] == (abs(corr) < 0.2)

def test_generated_dataset_integration():
    """
    Integration test: validate schema and orthogonalization on the actual 
    generated files (data/raw/synthetic_puzzles.jsonl and data/raw/aux_puzzles.jsonl).
    This test is designed to run after T003.
    """
    primary_path = pathlib.Path("data/raw/synthetic_puzzles.jsonl")
    aux_path = pathlib.Path("data/raw/aux_puzzles.jsonl")

    if not primary_path.exists():
        pytest.skip("Primary dataset not found. This test requires T003 to be completed.")

    # Load datasets
    all_puzzles = []
    for path in [primary_path, aux_path]:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        all_puzzles.append(json.loads(line))

    assert len(all_puzzles) > 0, "No puzzles found in generated dataset files."

    # 1. Validate Schema Conformance
    for puzzle in all_puzzles:
        validate_puzzle_schema(puzzle)

    # 2. Validate Stratified-Orthogonalization (|r| < 0.2)
    depths = [p["nesting_depth"] for p in all_puzzles]
    branches = [p["branching_factor"] for p in all_puzzles]
    
    correlation = calculate_pearson_correlation(depths, branches)
    logger.info(f"Integrated Dataset Correlation: {correlation:.4f}")
    
    assert abs(correlation) < 0.2, (
        f"Dataset orthogonalization failed: |r| = {abs(correlation):.4f}, expected < 0.2"
    )

def test_nx_set_seed_compatibility():
    """Calling nx.set_seed should not raise an exception."""
    try:
        nx.set_seed(12345)
    except Exception as e:
        pytest.fail(f"nx.set_seed raised an exception: {e}")

def test_random_seed_reproducibility():
    """Verify that the same seed produces identical batches."""
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
    assert batch1 == batch2
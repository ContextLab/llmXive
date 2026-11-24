import json
import os
import random
import logging
import pathlib
import subprocess
import sys
from typing import List, Dict, Any

import pytest
import networkx as nx
import numpy as np

from code.graph_generator import generate_set

logger = logging.getLogger(__name__)

# --- Schema Definition ---
# Based on T003 requirements and the actual implementation in code/graph_generator.py
REQUIRED_SCHEMA_KEYS = {
    "instance_id": str,
    "text": str,
    "ground_truth": str,
    "ground_truth_path": list,
    "nesting_depth": int,
    "branching_factor": float,
    "graph_structure": dict,
    "is_acyclic": bool,
    "is_solvable": bool,
    "text_generation_method": str,
    "is_orthogonal": bool,
    "seed": int,
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

def test_generate_set_basic():
    """Generate a small set and verify basic properties and schema."""
    batch = generate_set(
        count=10,
        depth_range=(3, 6),
        branch_range=(1.0, 5.0),
        seed=123,
    )
    assert len(batch) == 10
    for puzzle in batch:
        validate_puzzle_schema(puzzle)

def test_random_seed_reproducibility():
    """Verify that the same seed produces identical sets."""
    params = {
        "count": 5,
        "depth_range": (3, 5),
        "branch_range": (1.0, 3.0),
        "seed": 42,
    }
    batch1 = generate_set(**params)
    batch2 = generate_set(**params)
    assert batch1 == batch2

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
    depths = [float(p["nesting_depth"]) for p in all_puzzles]
    branches = [float(p["branching_factor"]) for p in all_puzzles]
    
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

def test_cli_generation_integration(tmp_path):
    """Run the generator via CLI and validate the produced JSONL."""
    output_file = tmp_path / "puzzles.jsonl"
    cmd = [
        sys.executable,
        str(pathlib.Path("code/graph_generator.py")),
        "--count", "10",
        "--depth-min", "1",
        "--depth-max", "3",
        "--branch-min", "1",
        "--branch-max", "2",
        "--output", str(output_file),
        "--seed", "123"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"CLI failed with exit {result.returncode}: {result.stderr}"

    # Load and validate the generated puzzles
    puzzles = []
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                puzzles.append(json.loads(line))

    assert len(puzzles) == 10, "Expected 10 puzzles from CLI generation"
    for puzzle in puzzles:
        validate_puzzle_schema(puzzle)

    # Verify Pearson correlation is below 0.2
    depths = [float(p["nesting_depth"]) for p in puzzles]
    branches = [float(p["branching_factor"]) for p in puzzles]
    corr = float(np.corrcoef(depths, branches)[0, 1])
    assert abs(corr) < 0.2, f"Correlation too high: {corr}"
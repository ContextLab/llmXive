"""
Tests for the synthetic puzzle generator.

These tests validate:
1. Schema conformance of each generated puzzle (SyntheticPuzzle).
2. That the generated batch respects the stratified orthogonalization
   constraint: the absolute Pearson correlation between `nesting_depth`
   and `branching_factor` must be less than 0.2.
"""

import math
import pytest
from typing import List, Dict

# Functions under test
from graph_generator import generate_batch

# Expected keys for a SyntheticPuzzle record
REQUIRED_KEYS = {
    "instance_id",
    "text",
    "ground_truth_path",
    "nesting_depth",
    "branching_factor",
    "graph_structure",
    "is_acyclic",
    "is_solvable",
    "text_generation_method",
    "is_orthogonal",
    "seed",
}

def _assert_puzzle_schema(puzzle: Dict) -> None:
    """Assert that a puzzle dictionary contains all required fields and sensible values."""
    missing = REQUIRED_KEYS - puzzle.keys()
    assert not missing, f"Puzzle missing required keys: {missing}"

    # Basic type checks
    assert isinstance(puzzle["instance_id"], str), "instance_id must be a string"
    assert isinstance(puzzle["text"], str) and puzzle["text"], "text must be a non‑empty string"
    assert isinstance(puzzle["ground_truth_path"], list), "ground_truth_path must be a list"
    assert isinstance(puzzle["nesting_depth"], int) and puzzle["nesting_depth"] > 0, "nesting_depth must be a positive int"
    assert isinstance(puzzle["branching_factor"], (int, float)) and puzzle["branching_factor"] > 0, "branching_factor must be positive"
    assert isinstance(puzzle["graph_structure"], dict), "graph_structure must be a dict"
    assert puzzle["is_acyclic"] is True, "graph must be acyclic"
    assert puzzle["is_solvable"] is True, "graph must be solvable"
    assert puzzle["text_generation_method"] == "template_based", "text generation method must be 'template_based'"
    assert puzzle["is_orthogonal"] is True, "puzzle must be marked orthogonal"
    assert isinstance(puzzle["seed"], int), "seed must be an int"

@pytest.mark.parametrize(
    "batch_size,min_depth,max_depth,min_branch,max_branch,max_corr",
    [
        (50, 3, 6, 1, 5, 0.2),   # typical primary batch
        (200, 7, 10, 1, 5, 0.2), # auxiliary batch with deeper graphs
    ],
)
def test_generate_batch_schema_and_orthogonalization(
    batch_size: int,
    min_depth: int,
    max_depth: int,
    min_branch: int,
    max_branch: int,
    max_corr: float,
) -> None:
    """
    Generate a batch and verify:
    * The correct number of puzzles are produced.
    * Each puzzle conforms to the SyntheticPuzzle schema.
    * The correlation between nesting depth and branching factor is below the threshold.
    """
    puzzles: List[Dict] = generate_batch(
        num_instances=batch_size,
        min_depth=min_depth,
        max_depth=max_depth,
        min_branching=min_branch,
        max_branching=max_branch,
        max_correlation=max_corr,
        logger=None,  # logger is optional; we don't need logging in tests
    )

    # Basic size check
    assert len(puzzles) == batch_size, f"Expected {batch_size} puzzles, got {len(puzzles)}"

    depths: List[int] = []
    branchings: List[float] = []

    for p in puzzles:
        _assert_puzzle_schema(p)
        depths.append(p["nesting_depth"])
        branchings.append(p["branching_factor"])

    # Compute Pearson correlation; use math.fsum for numerical stability
    if len(depths) > 1:
        mean_depth = sum(depths) / len(depths)
        mean_branch = sum(branchings) / len(branchings)

        cov = sum((d - mean_depth) * (b - mean_branch) for d, b in zip(depths, branchings))
        var_depth = sum((d - mean_depth) ** 2 for d in depths)
        var_branch = sum((b - mean_branch) ** 2 for b in branchings)

        # Guard against division by zero (should never happen with valid generation)
        if var_depth == 0 or var_branch == 0:
            corr = 0.0
        else:
            corr = cov / math.sqrt(var_depth * var_branch)

        assert (
            abs(corr) < max_corr
        ), f"Correlation {corr:.4f} exceeds orthogonalization threshold {max_corr}"
    else:
        pytest.fail("Not enough data points to compute correlation")
import pytest
import json
import os
import sys
import logging
from pathlib import Path
import numpy as np

# Add the code directory to the path to import the modeling module
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from utils.logging import setup_logging, get_logger
from config import get_config, set_random_seed

# Setup logging for the test
setup_logging()
logger = get_logger(__name__)

def test_permutation_null_distribution():
    """
    Integration test for permutation null distribution generation.
    
    This test verifies that the permutation test logic in code/04_predictive_modeling.py
    correctly generates a null distribution of R^2 scores by shuffling the target variable
    and saves the 95th percentile threshold to the expected artifact location.
    
    Prerequisites:
    - code/04_predictive_modeling.py must be executed successfully prior to this test
      to generate the output artifact.
    """
    # Define the expected output path relative to the project root
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "data" / "processed" / "null_threshold.json"
    
    # Check if the output file exists
    if not output_path.exists():
        pytest.skip(
            f"Output artifact not found at {output_path}. "
            "Please run 'python code/04_predictive_modeling.py' to generate the permutation null distribution first."
        )
    
    # Load and validate the JSON artifact
    try:
        with open(output_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to decode JSON from {output_path}: {e}")
    
    # Validate required keys exist
    assert 'threshold' in data, "Artifact missing required key: 'threshold'"
    assert 'null_scores' in data, "Artifact missing required key: 'null_scores'"
    assert 'n_permutations' in data, "Artifact missing required key: 'n_permutations'"
    assert 'random_seed' in data, "Artifact missing required key: 'random_seed'"
    
    # Validate data types and constraints
    threshold = data['threshold']
    null_scores = data['null_scores']
    n_permutations = data['n_permutations']
    
    assert isinstance(threshold, (int, float)), f"'threshold' must be numeric, got {type(threshold)}"
    assert isinstance(null_scores, list), f"'null_scores' must be a list, got {type(null_scores)}"
    assert len(null_scores) > 0, "'null_scores' list cannot be empty"
    assert len(null_scores) == n_permutations, f"Number of null scores ({len(null_scores)}) does not match n_permutations ({n_permutations})"
    
    # Validate that all scores are numeric
    for i, score in enumerate(null_scores):
        if not isinstance(score, (int, float)):
            pytest.fail(f"Score at index {i} is not numeric: {score} (type: {type(score)})")
    
    # Validate that the threshold is actually the 95th percentile of the scores
    # (allowing for a small floating point tolerance)
    expected_threshold = float(np.percentile(null_scores, 95))
    assert abs(threshold - expected_threshold) < 1e-6, (
        f"Threshold mismatch: stored={threshold}, calculated={expected_threshold}"
    )
    
    # Validate that the threshold is greater than the minimum score (logic check)
    assert threshold >= min(null_scores), "Threshold cannot be less than the minimum null score"
    assert threshold <= max(null_scores), "Threshold cannot be greater than the maximum null score"
    
    logger.info(
        f"Permutation null distribution test passed. "
        f"Threshold: {threshold:.4f}, N permutations: {n_permutations}"
    )
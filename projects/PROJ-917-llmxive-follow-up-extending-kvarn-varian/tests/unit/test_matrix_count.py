"""
Test that the synthetic attention dataset contains the expected number of matrices.
This verifies FR-001 compliance.
"""

import pytest
from pathlib import Path
import json

from config import get_config


def test_synthetic_dataset_matrix_count():
    """
    Ensure that the generated JSONL file contains exactly
    config.NUM_MATRICES entries (or the overridden count).
    """
    config = get_config()
    expected_count = config.NUM_MATRICES
    
    data_path = Path(__file__).resolve().parents[3] / "data" / "raw" / "synthetic_attention_matrices.jsonl"
    
    # The data generation step must have been run before this test.
    assert data_path.exists(), f"Dataset file not found at {data_path}"
    
    # Count the number of JSON lines
    with open(data_path, "r") as f:
        lines = [line for line in f if line.strip()]
    
    actual_count = len(lines)
    assert actual_count == expected_count, (
        f"Dataset contains {actual_count} matrices, "
        f"but expected {expected_count} (config.NUM_MATRICES)."
    )
    
    # Additionally, ensure each line is valid JSON and contains required keys
    required_keys = {
        "matrix_id",
        "mean",
        "var",
        "sparsity",
        "outlier_magnitude",
        "scaling_factor",
        "solver_converged",
        "generation_time_ms",
        "solver_time_ms",
        "seed_used",
    }
    
    for idx, line in enumerate(lines):
        record = json.loads(line)
        missing = required_keys - record.keys()
        assert not missing, f"Record {idx} missing keys: {missing}"
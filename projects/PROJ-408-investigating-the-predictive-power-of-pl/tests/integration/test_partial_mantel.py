"""
Integration test for Partial Mantel calculation (Task T023).

This test verifies that the partial Mantel test implementation correctly:
1. Loads phylogenetic and climate distance matrices
2. Computes a partial Mantel r-value
3. Produces results that differ from the standard Mantel r-value when climate signal exists
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pytest

# Ensure we can import from code/
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from stats_engine import load_distance_matrix, run_partial_mantel_test, run_mantel_test


@pytest.mark.integration
def test_partial_mantel_calculation():
    """
    Integration test for Partial Mantel calculation.
    
    Inputs:
      - data/processed/phylo_dist_matrix.csv
      - data/processed/climate_dist_matrix.csv
      - data/processed/mantel_results.json
    
    Output:
      - data/processed/partial_mantel_results.json
    
    Assertions:
      - partial_r is calculated and differs from standard_r by > 0.0 (if signal exists)
    """
    data_processed_dir = Path("data/processed")
    phylo_dist_path = data_processed_dir / "phylo_dist_matrix.csv"
    climate_dist_path = data_processed_dir / "climate_dist_matrix.csv"
    standard_mantel_path = data_processed_dir / "mantel_results.json"
    output_path = data_processed_dir / "partial_mantel_results.json"

    # Skip if input files don't exist (e.g., in CI without data)
    if not phylo_dist_path.exists() or not climate_dist_path.exists() or not standard_mantel_path.exists():
        pytest.skip("Input files for partial Mantel test not found. Run full pipeline first.")

    # Load matrices
    phylo_matrix = load_distance_matrix(phylo_dist_path)
    climate_matrix = load_distance_matrix(climate_dist_path)

    # Verify dimensions match
    assert phylo_matrix.shape == climate_matrix.shape, \
        f"Matrix dimension mismatch: phylo {phylo_matrix.shape} vs climate {climate_matrix.shape}"

    # Load standard Mantel results
    with open(standard_mantel_path, 'r') as f:
        standard_results = json.load(f)
    
    standard_r = standard_results['r']
    
    # Run partial Mantel test
    partial_r, partial_p, null_dist = run_partial_mantel_test(
        phylo_matrix, 
        climate_matrix,
        n_permutations=999
    )

    # Assertion 1: partial_r is calculated
    assert partial_r is not None, "partial_r is None"
    assert isinstance(partial_r, (int, float)), "partial_r is not a numeric type"
    assert -1.0 <= partial_r <= 1.0, f"partial_r {partial_r} out of valid range [-1, 1]"

    # Assertion 2: partial_r differs from standard_r if signal exists
    if abs(standard_r) > 0.05:
        diff = abs(partial_r - standard_r)
        # We expect some difference if climate explains part of the phylogenetic signal
        # The task says "asserts that partial_r differs from standard_r by > 0.0 (if signal exists)"
        # We'll check that the difference is non-zero (within floating point tolerance)
        assert diff > 1e-10, \
            f"Partial r ({partial_r}) equals standard r ({standard_r}) despite detectable signal"

    # Verify output file is written
    assert output_path.exists(), f"Output file {output_path} was not created"
    
    with open(output_path, 'r') as f:
        results = json.load(f)
    
    assert 'partial_r' in results, "partial_r missing from output"
    assert 'standard_r' in results, "standard_r missing from output"
    assert 'r_difference' in results, "r_difference missing from output"
    
    # Verify consistency
    assert abs(results['partial_r'] - partial_r) < 1e-10, "partial_r in output doesn't match computed value"
    assert abs(results['r_difference'] - (partial_r - standard_r)) < 1e-10, "r_difference calculation error"


@pytest.mark.integration
def test_partial_mantel_vs_standard():
    """
    Verify that partial Mantel test produces different results than standard Mantel
    when controlling for a confounding variable (climate).
    """
    data_processed_dir = Path("data/processed")
    phylo_dist_path = data_processed_dir / "phylo_dist_matrix.csv"
    climate_dist_path = data_processed_dir / "climate_dist_matrix.csv"

    if not phylo_dist_path.exists() or not climate_dist_path.exists():
        pytest.skip("Input files not found")

    phylo_matrix = load_distance_matrix(phylo_dist_path)
    climate_matrix = load_distance_matrix(climate_dist_path)

    # Run standard Mantel
    standard_r, standard_p, _ = run_mantel_test(phylo_matrix, n_permutations=999)
    
    # Run partial Mantel
    partial_r, partial_p, _ = run_partial_mantel_test(
        phylo_matrix, 
        climate_matrix,
        n_permutations=999
    )

    # The partial r should be different from standard r if climate explains variance
    # We don't assert direction (could be higher or lower)
    if abs(standard_r) > 0.05:
        assert abs(partial_r - standard_r) > 1e-10, \
            "Partial Mantel r should differ from standard Mantel r when controlling for climate"
    
    # Both p-values should be valid
    assert 0 <= standard_p <= 1, f"standard_p {standard_p} out of range"
    assert 0 <= partial_p <= 1, f"partial_p {partial_p} out of range"

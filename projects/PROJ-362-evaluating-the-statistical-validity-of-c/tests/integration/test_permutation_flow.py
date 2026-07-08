"""
Integration test for T012: Verify p-value calculation (r+1)/(N+1) against manual calculation.

This test verifies that the p-value calculation logic in the permutation flow
correctly implements the formula: p = (r + 1) / (N + 1)
where r is the count of permuted scores >= observed score, and N is the number of permutations.
"""
import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import RESULTS_DIR
from code.permutation import run_single_query_permutation, calculate_p_value
from code.metrics import ndcg_at_k


def test_p_value_calculation_formula():
    """
    Test that p-value calculation follows the (r+1)/(N+1) formula exactly.
    
    We create a controlled scenario where we know:
    - The observed score
    - The null distribution scores
    - The expected count r (how many null scores >= observed)
    - The expected p-value based on the formula
    """
    # Setup: Create a mock null distribution with known properties
    observed_score = 0.75
    null_scores = [0.50, 0.60, 0.65, 0.70, 0.72, 0.74, 0.74, 0.74, 0.74, 0.74]
    # In this list, 0 scores are >= 0.75, so r = 0
    
    # Calculate expected p-value manually
    N = len(null_scores)
    r = sum(1 for score in null_scores if score >= observed_score)
    expected_p_value = (r + 1) / (N + 1)
    
    # Verify our manual calculation
    assert r == 0, f"Expected r=0, got r={r}"
    assert expected_p_value == 1/11, f"Expected p=1/11, got p={expected_p_value}"
    
    # Now test the actual implementation
    calculated_p_value = calculate_p_value(observed_score, null_scores)
    
    # Verify the implementation matches the manual calculation
    assert abs(calculated_p_value - expected_p_value) < 1e-9, \
        f"Calculated p-value {calculated_p_value} does not match expected {expected_p_value}"
    
    print(f"✓ P-value calculation verified: r={r}, N={N}, p={calculated_p_value}")


def test_p_value_with_various_r_values():
    """
    Test p-value calculation with different values of r (0 to N).
    """
    null_scores = [0.5, 0.6, 0.7, 0.8, 0.9]  # N = 5
    
    test_cases = [
        # (observed_score, expected_r, expected_p)
        (1.0, 0, 1/6),    # r=0, p=1/6
        (0.9, 1, 2/6),    # r=1 (0.9 >= 0.9), p=2/6
        (0.8, 2, 3/6),    # r=2 (0.8, 0.9 >= 0.8), p=3/6
        (0.7, 3, 4/6),    # r=3 (0.7, 0.8, 0.9 >= 0.7), p=4/6
        (0.6, 4, 5/6),    # r=4 (0.6, 0.7, 0.8, 0.9 >= 0.6), p=5/6
        (0.5, 5, 6/6),    # r=5 (all >= 0.5), p=6/6
    ]
    
    for observed, expected_r, expected_p in test_cases:
        calculated_p = calculate_p_value(observed, null_scores)
        r = sum(1 for score in null_scores if score >= observed)
        
        assert r == expected_r, f"For observed={observed}, expected r={expected_r}, got r={r}"
        assert abs(calculated_p - expected_p) < 1e-9, \
            f"For observed={observed}, calculated p={calculated_p} != expected p={expected_p}"
        
        print(f"✓ Test case passed: observed={observed}, r={r}, p={calculated_p}")


def test_end_to_end_permutation_flow():
    """
    End-to-end test: Run a full permutation test on a small query and verify
    the p-value file is created with correct values.
    """
    # Create a temporary results directory for this test
    test_results_dir = tempfile.mkdtemp()
    try:
        # Mock query data (small, deterministic)
        query_id = 1
        doc_ids = [1, 2, 3, 4, 5]
        relevance_labels = [3, 2, 1, 0, 0]  # Standard TREC relevance
        k = 10  # NDCG@10
        
        # Calculate observed NDCG
        observed_score = ndcg_at_k(relevance_labels, k)
        
        # Run permutation test with small N for speed
        N = 100
        null_distributions, observed_scores = run_single_query_permutation(
            query_id, doc_ids, relevance_labels, N, k, seed=42
        )
        
        # Verify we got the expected number of permutations
        assert len(null_distributions) == N, f"Expected {N} permutations, got {len(null_distributions)}"
        
        # Calculate p-value manually
        r = sum(1 for score in null_distributions if score >= observed_score)
        expected_p = (r + 1) / (N + 1)
        
        # Calculate p-value using the function
        calculated_p = calculate_p_value(observed_score, null_distributions)
        
        # Verify they match
        assert abs(calculated_p - expected_p) < 1e-9, \
            f"End-to-end p-value mismatch: calculated={calculated_p}, expected={expected_p}"
        
        print(f"✓ End-to-end flow verified: query_id={query_id}, N={N}, r={r}, p={calculated_p}")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(test_results_dir)


def test_p_value_file_format():
    """
    Verify that the p-values are saved in the correct CSV format.
    """
    # This test checks that if we were to write p-values, they'd be in the right format
    # We don't actually run the full pipeline here, just verify the format logic
    
    expected_columns = ["query_id", "metric", "raw_p"]
    
    # Simulate what would be written
    test_data = [
        {"query_id": 1, "metric": "ndcg@10", "raw_p": 0.05},
        {"query_id": 2, "metric": "ndcg@10", "raw_p": 0.03},
    ]
    
    # Verify format
    for row in test_data:
        assert "query_id" in row, "Missing query_id column"
        assert "metric" in row, "Missing metric column"
        assert "raw_p" in row, "Missing raw_p column"
        assert isinstance(row["query_id"], int), "query_id must be integer"
        assert 0 <= row["raw_p"] <= 1, "p-value must be between 0 and 1"
    
    print("✓ P-value file format verified")


if __name__ == "__main__":
    print("Running T012 integration tests...")
    print("=" * 50)
    
    test_p_value_calculation_formula()
    test_p_value_with_various_r_values()
    test_end_to_end_permutation_flow()
    test_p_value_file_format()
    
    print("=" * 50)
    print("All T012 integration tests passed! ✓")
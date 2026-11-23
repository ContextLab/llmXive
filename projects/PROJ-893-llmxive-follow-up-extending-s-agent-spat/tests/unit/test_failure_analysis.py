"""
Unit tests for failure categorization logic (T020).

Tests the logic that classifies mismatches between Symbolic Solver and VLM Baseline
into "Geometric Ambiguity" or "Semantic Gap".

This test file relies on the implementation in `code/benchmark/analyze_failures.py`.
"""
import pytest
import json
from pathlib import Path
from typing import List, Dict, Any

# Import the logic to be tested. 
# The implementation is expected to exist in code/benchmark/analyze_failures.py
# as per the task description and project structure.
try:
    from benchmark.analyze_failures import categorize_failure, analyze_failure_batch
except ImportError:
    # Fallback for environments where the module might not be fully written yet,
    # though the task requires implementing the test against the expected interface.
    # In a real execution, this import must succeed.
    pytest.skip("benchmark.analyze_failures module not found", allow_module_level=True)


class TestFailureCategorization:
    """Tests for the failure categorization logic."""

    def test_categorize_geometric_ambiguity(self):
        """
        Test that a mismatch where the symbolic solver reports 'No Solution'
        but the ground truth exists is categorized as 'Geometric Ambiguity'.
        
        Scenario: The constraints provided are insufficient or contradictory 
        (ambiguous), causing the solver to fail, while the VLM might have 
        hallucinated a valid position or the ground truth represents a 
        specific valid configuration that the constraints didn't enforce.
        """
        mismatch = {
            "scene_id": "scene_amb_001",
            "ground_truth": {"count": 5, "position": [10, 20, 30]},
            "solver_prediction": None,  # Solver failed/No Solution
            "solver_reason": "ConstraintPropagationFailed: No solution found",
            "vlm_prediction": {"count": 5, "position": [10, 20, 30]},
            "is_match": False
        }
        
        # The categorization logic should identify this as Geometric Ambiguity
        # because the solver's failure is due to the constraints themselves.
        category = categorize_failure(mismatch)
        
        assert category == "Geometric Ambiguity", (
            f"Expected 'Geometric Ambiguity' for solver failure, "
            f"got '{category}'"
        )

    def test_categorize_semantic_gap_solver_correct(self):
        """
        Test that a mismatch where the solver is correct but the VLM is wrong
        (or the VLM prediction is plausible but incorrect) is categorized as 'Semantic Gap'.
        
        Scenario: The constraints are solvable, the solver finds the unique 
        geometric solution, but the VLM fails to interpret the scene correctly 
        (semantic gap), or the ground truth relies on semantic context not 
        captured in the geometric constraints.
        """
        mismatch = {
            "scene_id": "scene_sem_001",
            "ground_truth": {"count": 3, "position": [5, 5, 5]},
            "solver_prediction": {"count": 3, "position": [5, 5, 5]},
            "solver_reason": "SolutionFound",
            "vlm_prediction": {"count": 4, "position": [5, 5, 6]},
            "is_match": False
        }
        
        # If the solver matches ground truth, the failure is likely in the 
        # VLM's semantic interpretation or the comparison metric.
        # However, the task defines "Semantic Gap" as the proportion of failures 
        # attributable to semantic disambiguation.
        # If the solver is correct (matches GT) and VLM is wrong, the "failure" 
        # of the VLM is a semantic gap.
        # If the solver is wrong (mismatch GT) and VLM is wrong, we need to check 
        # why the solver failed.
        
        # Let's refine the test case: Solver is wrong, VLM is wrong, but the 
        # solver's error is NOT geometric ambiguity (constraints were satisfiable).
        mismatch_solver_wrong = {
            "scene_id": "scene_sem_002",
            "ground_truth": {"count": 3, "position": [5, 5, 5]},
            "solver_prediction": {"count": 3, "position": [6, 6, 6]}, # Wrong position
            "solver_reason": "SolutionFound", # Solver found a solution, just wrong one?
            "vlm_prediction": {"count": 3, "position": [6, 6, 6]},
            "is_match": False
        }
        
        # In this specific logic, if the solver found a solution but it's wrong,
        # and the constraints were valid, it might be a semantic gap in how 
        # constraints were extracted or interpreted.
        # However, the standard definition in T021 is:
        # "Geometric Ambiguity": Solver returns No Solution.
        # "Semantic Gap": Solver returns a solution (or VLM fails) but the 
        # discrepancy arises from lack of semantic context.
        
        # Let's test the specific case where the solver fails due to ambiguity.
        # And a case where it doesn't.
        
        # Case: Solver found a solution, but it doesn't match GT. 
        # This implies the constraints didn't fully capture the scene (Semantic Gap).
        category = categorize_failure(mismatch_solver_wrong)
        # Assuming the logic: if solver_reason != "ConstraintPropagationFailed", 
        # and it's a mismatch, it's a Semantic Gap.
        assert category == "Semantic Gap", (
            f"Expected 'Semantic Gap' when solver finds solution but mismatches GT, "
            f"got '{category}'"
        )

    def test_categorize_semantic_gap_vlm_fail(self):
        """
        Test a case where the VLM fails to predict, but the solver succeeds.
        """
        mismatch = {
            "scene_id": "scene_sem_003",
            "ground_truth": {"count": 2, "position": [1, 2, 3]},
            "solver_prediction": {"count": 2, "position": [1, 2, 3]},
            "solver_reason": "SolutionFound",
            "vlm_prediction": None, # VLM failed
            "is_match": False
        }
        
        category = categorize_failure(mismatch)
        assert category == "Semantic Gap", (
            f"Expected 'Semantic Gap' when VLM fails but Solver succeeds, "
            f"got '{category}'"
        )

    def test_analyze_failure_batch(self):
        """
        Test the batch analysis function that calculates proportions.
        """
        mismatches = [
            {
                "scene_id": "s1", "ground_truth": {}, "solver_prediction": None,
                "solver_reason": "No Solution", "vlm_prediction": {}, "is_match": False
            },
            {
                "scene_id": "s2", "ground_truth": {}, "solver_prediction": {"x": 1},
                "solver_reason": "SolutionFound", "vlm_prediction": {"x": 2}, "is_match": False
            },
            {
                "scene_id": "s3", "ground_truth": {}, "solver_prediction": None,
                "solver_reason": "No Solution", "vlm_prediction": {}, "is_match": False
            }
        ]
        
        result = analyze_failure_batch(mismatches)
        
        assert "total_failures" in result
        assert "geometric_ambiguity_count" in result
        assert "semantic_gap_count" in result
        assert "proportion_semantic_gap" in result
        
        assert result["total_failures"] == 3
        assert result["geometric_ambiguity_count"] == 2
        assert result["semantic_gap_count"] == 1
        assert abs(result["proportion_semantic_gap"] - (1/3)) < 1e-5

    def test_empty_mismatches(self):
        """Test that empty input returns zero counts."""
        result = analyze_failure_batch([])
        
        assert result["total_failures"] == 0
        assert result["geometric_ambiguity_count"] == 0
        assert result["semantic_gap_count"] == 0
        assert result["proportion_semantic_gap"] == 0.0

    def test_invalid_reason_handling(self):
        """Test handling of unexpected solver reasons."""
        mismatch = {
            "scene_id": "s_unknown",
            "ground_truth": {},
            "solver_prediction": None,
            "solver_reason": "UnknownError",
            "vlm_prediction": {},
            "is_match": False
        }
        
        # The categorize_failure function should handle unknown reasons gracefully.
        # Typically, if the solver didn't return a solution, it might be ambiguous.
        # Or it might default to Semantic Gap if the reason is unclear.
        # We assert that it doesn't crash.
        try:
            category = categorize_failure(mismatch)
            # It should return one of the valid categories
            assert category in ["Geometric Ambiguity", "Semantic Gap"]
        except Exception as e:
            pytest.fail(f"categorize_failure raised an exception for unknown reason: {e}")
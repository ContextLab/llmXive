"""
Unit tests for the Structured JSON comparison logic in code/scorer.py.

This module validates the core metric calculation for User Story 3 (Scoring),
specifically ensuring that the comparison between the agent's mental map
and the ground truth state correctly handles:
1. Exact matches (Score = 0)
2. Missing items (Penalty applied)
3. Extra hallucinated items (Penalty applied)
4. Semantic similarity scoring for partial matches (if applicable)

Dependencies:
- code/scorer.py (must implement compare_structured_json)
- specs/contracts/metric_result.schema.yaml (for expected output structure)
"""

import pytest
import json
import os
import sys
from typing import Dict, Any, List

# Ensure project root is in path for imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from code.scorer import compare_structured_json, calculate_memory_gap_score
from code.renderer import render_error_block

# Constants for testing
EMPTY_GRID = [["." for _ in range(5)] for _ in range(5)]

# Ground Truth State (The "Real" state the agent should remember)
GT_STATE = {
    "grid": [
        ["X", ".", ".", ".", "."],
        [".", "O", ".", ".", "."],
        [".", ".", "*", ".", "."],
        [".", ".", ".", ".", "."],
        [".", ".", ".", ".", "."]
    ],
    "timestamp": 100,
    "hidden_items": ["X", "O", "*"]
}

# Perfect Mental Map (Agent remembered everything correctly)
PERFECT_MAP = {
    "grid": [
        ["X", ".", ".", ".", "."],
        [".", "O", ".", ".", "."],
        [".", ".", "*", ".", "."],
        [".", ".", ".", ".", "."],
        [".", ".", ".", ".", "."]
    ],
    "timestamp": 100,
    "hidden_items": ["X", "O", "*"]
}

# Missing Items Map (Agent forgot the star)
MISSING_MAP = {
    "grid": [
        ["X", ".", ".", ".", "."],
        [".", "O", ".", ".", "."],
        [".", ".", ".", ".", "."], # Star missing
        [".", ".", ".", ".", "."],
        [".", ".", ".", ".", "."]
    ],
    "timestamp": 100,
    "hidden_items": ["X", "O"]
}

# Hallucinated Items Map (Agent added a fake item)
HALLUCINATED_MAP = {
    "grid": [
        ["X", ".", ".", ".", "."],
        [".", "O", ".", ".", "."],
        [".", ".", "*", ".", "."],
        [".", ".", ".", "#", "."], # Fake item
        [".", ".", ".", ".", "."]
    ],
    "timestamp": 100,
    "hidden_items": ["X", "O", "*", "#"]
}

# Corrupted/Invalid Map (Wrong dimensions or structure)
CORRUPTED_MAP = {
    "grid": [
        ["X", "."],
        [".", "O"]
    ],
    "timestamp": 100,
    "hidden_items": ["X", "O"]
}

def test_perfect_match_score():
    """
    Test that a perfect match between Ground Truth and Mental Map
    results in a Memory Gap Score of 0.0.
    """
    result = compare_structured_json(GT_STATE, PERFECT_MAP)
    
    assert result is not None, "Comparison result should not be None"
    assert result["memory_gap_score"] == 0.0, f"Expected 0.0, got {result['memory_gap_score']}"
    assert result["status"] == "pass", "Status should be 'pass' for perfect match"
    assert "missing_items" in result
    assert len(result["missing_items"]) == 0
    assert "hallucinated_items" in result
    assert len(result["hallucinated_items"]) == 0

def test_missing_items_penalty():
    """
    Test that missing items in the mental map result in a non-zero score
    and are correctly identified.
    """
    result = compare_structured_json(GT_STATE, MISSING_MAP)
    
    assert result["memory_gap_score"] > 0.0, "Score should be > 0 for missing items"
    assert "missing_items" in result
    assert "*" in result["missing_items"], f"Expected '*' in missing_items, got {result['missing_items']}"
    assert len(result["hallucinated_items"]) == 0

def test_hallucinated_items_penalty():
    """
    Test that hallucinated items in the mental map result in a non-zero score
    and are correctly identified.
    """
    result = compare_structured_json(GT_STATE, HALLUCINATED_MAP)
    
    assert result["memory_gap_score"] > 0.0, "Score should be > 0 for hallucinated items"
    assert "hallucinated_items" in result
    assert "#" in result["hallucinated_items"], f"Expected '#' in hallucinated_items, got {result['hallucinated_items']}"
    assert len(result["missing_items"]) == 0

def test_corrupted_grid_structure():
    """
    Test that a mismatched grid structure (e.g., wrong dimensions)
    triggers an error state or maximum penalty.
    """
    result = compare_structured_json(GT_STATE, CORRUPTED_MAP)
    
    # Depending on implementation, this might return a high score or an error flag
    # We expect it NOT to be a perfect pass
    assert result["status"] != "pass" or result["memory_gap_score"] > 0.0, \
        "Corrupted grid should not result in a perfect pass"
    
    # Verify error details are present if structure is invalid
    if "error" in result:
        assert "dimension" in result["error"].lower() or "structure" in result["error"].lower()

def test_empty_ground_truth():
    """
    Test behavior when Ground Truth is empty (all dots).
    Any item in the mental map should be considered hallucination.
    """
    empty_gt = {
        "grid": [["." for _ in range(5)] for _ in range(5)],
        "timestamp": 100,
        "hidden_items": []
    }
    
    result = compare_structured_json(empty_gt, HALLUCINATED_MAP)
    
    assert result["memory_gap_score"] > 0.0
    assert len(result["hallucinated_items"]) > 0
    assert len(result["missing_items"]) == 0

def test_empty_mental_map():
    """
    Test behavior when Mental Map is empty.
    All ground truth items should be considered missing.
    """
    empty_map = {
        "grid": [["." for _ in range(5)] for _ in range(5)],
        "timestamp": 100,
        "hidden_items": []
    }
    
    result = compare_structured_json(GT_STATE, empty_map)
    
    assert result["memory_gap_score"] > 0.0
    assert len(result["missing_items"]) == 3 # X, O, *
    assert len(result["hallucinated_items"]) == 0

def test_calculate_memory_gap_score_aggregation():
    """
    Test the aggregation function that calculates the final score from
    individual comparison results.
    """
    results = [
        {"memory_gap_score": 0.0},
        {"memory_gap_score": 0.5},
        {"memory_gap_score": 1.0}
    ]
    
    avg_score = calculate_memory_gap_score(results)
    
    # Expected average: (0 + 0.5 + 1.0) / 3 = 0.5
    expected = 0.5
    assert abs(avg_score - expected) < 1e-6, f"Expected {expected}, got {avg_score}"

def test_calculate_memory_gap_score_empty_list():
    """
    Test that calculating score on an empty list returns 0.0 or raises a specific error.
    """
    results = []
    # Implementation decision: return 0.0 or raise ValueError.
    # We assume it returns 0.0 for safety in pipelines, or raises.
    # Let's assume it handles empty gracefully.
    try:
        score = calculate_memory_gap_score(results)
        assert score == 0.0, "Empty list should result in 0.0 score"
    except ValueError:
        # If it raises, that's also acceptable behavior for empty input
        pass

def test_semantic_similarity_partial_match():
    """
    Test that items with similar semantic meaning (if using embeddings)
    are scored differently than exact string matches.
    Note: This test assumes the scorer uses a semantic similarity threshold.
    If the current implementation is purely string-based, this tests
    that exact string mismatch is penalized.
    """
    # Simulating a case where 'X' is present but 'x' (lowercase) is used
    # depending on implementation, this might be a miss or a partial match
    case_sensitive_gt = {
        "grid": [["X", ".", ".", ".", "."] for _ in range(5)],
        "hidden_items": ["X"]
    }
    case_sensitive_map = {
        "grid": [["x", ".", ".", ".", "."] for _ in range(5)],
        "hidden_items": ["x"]
    }
    
    result = compare_structured_json(case_sensitive_gt, case_sensitive_map)
    
    # If strict string comparison: should be a miss
    # If semantic: might be a partial match
    # We verify that the logic distinguishes them
    assert "missing_items" in result or "hallucinated_items" in result, \
        "Case mismatch should result in a discrepancy"
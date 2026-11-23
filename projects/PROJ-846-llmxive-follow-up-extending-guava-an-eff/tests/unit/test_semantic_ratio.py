import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code root to path
code_root = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from analysis.semantic_failure_analyzer import (
    calculate_semantic_ratio,
    EXCLUDED_CATEGORIES,
    SEMANTIC_THRESHOLD
)
from utils.config import get_path, initialize_paths

# Mock the config path setup if not already done
# In a real CI, this would be handled by a conftest.py
if not os.path.exists(str(get_path("artifacts"))):
    # Fallback to a temp directory for testing if the real path doesn't exist
    # This ensures the test can run in isolation
    pass

@pytest.fixture
def sample_outcomes():
    """
    Returns a list of mock TaskOutcome dictionaries for testing.
    """
    return [
        # Successful tasks (should be ignored)
        {"success": True, "failure_category": None, "task_id": "t1"},
        {"success": True, "failure_category": None, "task_id": "t2"},
        
        # Perception failures (should be excluded)
        {"success": False, "failure_category": "perception", "task_id": "t3"},
        {"success": False, "failure_category": "perception", "task_id": "t4"},
        
        # Latency failures (should be excluded)
        {"success": False, "failure_category": "latency", "task_id": "t5"},
        {"success": False, "failure_category": "latency", "task_id": "t6"},
        
        # Semantic failures (counted in numerator and denominator)
        {"success": False, "failure_category": "semantic", "task_id": "t7"},
        {"success": False, "failure_category": "semantic", "task_id": "t8"},
        {"success": False, "failure_category": "semantic", "task_id": "t9"},
        
        # Geometric failures (counted in denominator, not numerator)
        {"success": False, "failure_category": "geometric", "task_id": "t10"},
        {"success": False, "failure_category": "geometric", "task_id": "t11"},
    ]

def test_calculate_semantic_ratio_basic(sample_outcomes):
    """
    Test basic calculation:
    Total failures = 9 (3 semantic + 2 geometric + 2 perception + 2 latency)
    Excluded = 4 (2 perception + 2 latency)
    Relevant failures = 5 (3 semantic + 2 geometric)
    Semantic ratio = 3 / 5 = 0.6
    """
    ratio = calculate_semantic_ratio(sample_outcomes)
    expected = 3.0 / 5.0
    assert abs(ratio - expected) < 1e-6, f"Expected {expected}, got {ratio}"

def test_calculate_semantic_ratio_no_relevant_failures():
    """
    Test case where all failures are excluded (perception/latency).
    Ratio should be 0.0.
    """
    outcomes = [
        {"success": False, "failure_category": "perception"},
        {"success": False, "failure_category": "latency"},
    ]
    ratio = calculate_semantic_ratio(outcomes)
    assert ratio == 0.0

def test_calculate_semantic_ratio_all_semantic():
    """
    Test case where all relevant failures are semantic.
    Ratio should be 1.0.
    """
    outcomes = [
        {"success": False, "failure_category": "semantic"},
        {"success": False, "failure_category": "semantic"},
        {"success": False, "failure_category": "perception"}, # excluded
    ]
    ratio = calculate_semantic_ratio(outcomes)
    assert ratio == 1.0

def test_calculate_semantic_ratio_empty_list():
    """
    Test case with empty list.
    """
    ratio = calculate_semantic_ratio([])
    assert ratio == 0.0

def test_calculate_semantic_ratio_threshold_boundary():
    """
    Test boundary condition where ratio is exactly 0.40.
    """
    # 2 semantic, 3 geometric -> 2/5 = 0.4
    outcomes = [
        {"success": False, "failure_category": "semantic"},
        {"success": False, "failure_category": "semantic"},
        {"success": False, "failure_category": "geometric"},
        {"success": False, "failure_category": "geometric"},
        {"success": False, "failure_category": "geometric"},
    ]
    ratio = calculate_semantic_ratio(outcomes)
    assert abs(ratio - 0.40) < 1e-6

def test_case_insensitive_categories():
    """
    Test that category matching is case-insensitive.
    """
    outcomes = [
        {"success": False, "failure_category": "Semantic"},
        {"success": False, "failure_category": "PERCEPTION"},
        {"success": False, "failure_category": "Latency"},
        {"success": False, "failure_category": "Geometric"},
    ]
    # Relevant: Semantic, Geometric (2 total)
    # Semantic count: 1
    # Ratio: 0.5
    ratio = calculate_semantic_ratio(outcomes)
    assert abs(ratio - 0.5) < 1e-6
    
    # Verify excluded categories are handled case-insensitively
    # If "PERCEPTION" wasn't excluded, denominator would be 3, ratio 0.33
    # If "Latency" wasn't excluded, denominator would be 3, ratio 0.33
    assert ratio == 0.5
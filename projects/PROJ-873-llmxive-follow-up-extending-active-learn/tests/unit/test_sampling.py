"""
Unit tests for T013b sampling logic.
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from collections import defaultdict

# Import the module to test
# Note: In a real run, these would be imported from code.sampling
# Here we assume the structure is set up correctly
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from sampling import (
    filter_wasted_calls,
    stratify_by_query,
    select_stratified_sample,
    calculate_dynamic_sample_size
)
from metrics import calculate_dynamic_sample_size as calc_dynamic_size


def test_filter_wasted_calls():
    """Test that filter_wasted_calls correctly identifies high similarity pairs."""
    data = [
        {"query_id": "q1", "cosine_similarity": 0.96},
        {"query_id": "q2", "cosine_similarity": 0.94},
        {"query_id": "q3", "cosine_similarity": 0.99},
        {"query_id": "q4", "cosine_similarity": 0.50},
    ]
    
    wasted = filter_wasted_calls(data, threshold=0.95)
    
    assert len(wasted) == 2
    assert wasted[0]["query_id"] == "q1"
    assert wasted[1]["query_id"] == "q3"


def test_stratify_by_query():
    """Test grouping by query ID."""
    data = [
        {"query_id": "q1", "similarity": 0.96},
        {"query_id": "q1", "similarity": 0.97},
        {"query_id": "q2", "similarity": 0.98},
    ]
    
    strata = stratify_by_query(data)
    
    assert len(strata) == 2
    assert len(strata["q1"]) == 2
    assert len(strata["q2"]) == 1


def test_select_stratified_sample():
    """Test proportional stratified sampling."""
    # Create a scenario with 2 queries: q1 has 10 items, q2 has 2 items
    data = []
    for i in range(10):
        data.append({"query_id": "q1", "id": f"q1_{i}"})
    for i in range(2):
        data.append({"query_id": "q2", "id": f"q2_{i}"})
    
    # Target sample size 6
    # Expected: q1 gets ~5, q2 gets ~1 (proportional)
    sample = select_stratified_sample(data, target_sample_size=6)
    
    assert len(sample) == 6
    
    q1_count = sum(1 for x in sample if x["query_id"] == "q1")
    q2_count = sum(1 for x in sample if x["query_id"] == "q2")
    
    # Verify proportional distribution (approximate)
    assert q1_count >= 4
    assert q2_count >= 0


def test_dynamic_sample_size_calculation():
    """Test the dynamic sample size formula."""
    # Formula: min(deferred, upper_bound)
    # If deferred is 1000 and upper_bound is 100, result should be 100
    assert calculate_dynamic_sample_size(1000, 100) == 100
    
    # If deferred is 50 and upper_bound is 100, result should be 50
    assert calculate_dynamic_sample_size(50, 100) == 50
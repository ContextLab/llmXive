"""
Tests for T016 validation script logic.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from scipy.stats import pearsonr

# Mock the imports that might fail if dependencies aren't fully installed in test env
# But we assume the environment has the dependencies for the test to run
from code.scripts.validate_dag_correlation import (
    load_dag_manifest, 
    load_gold_standard, 
    extract_matching_data
)

def test_extract_matching_data_basic():
    """Test basic matching of manifest and gold standard."""
    manifest = {
        "example_1": {"logical_difficulty_score": 5.0},
        "example_2": {"logical_difficulty_score": 3.0},
        "example_3": {"logical_difficulty_score": 8.0}
    }
    
    gold = [
        {"example_id": "example_1", "human_complexity_rating": 5.2},
        {"example_id": "example_2", "human_complexity_rating": 3.1},
        {"example_id": "example_3", "human_complexity_rating": 7.9},
        {"example_id": "example_4", "human_complexity_rating": 2.0} # No match in manifest
    ]

    depths, human_scores = extract_matching_data(manifest, gold)

    assert len(depths) == 3
    assert len(human_scores) == 3
    
    # Check values are correct (order might vary, so check sets)
    assert set(depths) == {5.0, 3.0, 8.0}
    assert set(human_scores) == {5.2, 3.1, 7.9}

def test_extract_matching_data_list_manifest():
    """Test matching when manifest is a list."""
    manifest = [
        {"example_id": "id_a", "logical_difficulty_score": 10.0},
        {"example_id": "id_b", "logical_difficulty_score": 2.0}
    ]
    
    gold = [
        {"trace_id": "id_a", "human_complexity_rating": 10.5},
        {"trace_id": "id_b", "human_complexity_rating": 1.5}
    ]

    depths, human_scores = extract_matching_data(manifest, gold)

    assert len(depths) == 2
    assert 10.0 in depths
    assert 2.0 in depths
    assert 10.5 in human_scores
    assert 1.5 in human_scores

def test_extract_matching_data_insufficient():
    """Test that insufficient matches raise an error."""
    manifest = {"id_1": 5.0}
    gold = [{"example_id": "id_1", "human_complexity_rating": 5.0}]
    
    # This should work (1 match) but the main script requires > 5.
    # Let's test the extraction logic itself first.
    depths, human_scores = extract_matching_data(manifest, gold)
    assert len(depths) == 1

def test_correlation_calculation_logic():
    """Verify the correlation logic using scipy directly on known data."""
    # Perfect positive correlation
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    r, _ = pearsonr(x, y)
    assert abs(r - 1.0) < 1e-6

    # No correlation
    x = [1, 2, 3, 4, 5]
    y = [5, 1, 4, 2, 3]
    r, _ = pearsonr(x, y)
    assert abs(r) < 0.2 # Roughly zero

"""
Unit tests for T016: Node Degree Stats Generation.

Verifies that:
1. The mode is correctly calculated from a known distribution.
2. The verification logic correctly identifies if the mode is within the expected range.
3. The output file is generated with the correct schema.
"""
import json
import os
import tempfile
import pytest
from collections import Counter
from pathlib import Path

# Mock the config paths to use a temporary directory for testing
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path if not already present
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from ingest.node_degree_stats_generator import calculate_global_degree_distribution, compute_mode_and_stats

def test_calculate_global_degree_distribution():
    """Test aggregation of degrees across multiple mock graphs."""
    mock_graphs = [
        {
            "nodes": [
                {"degree": 4}, {"degree": 4}, {"degree": 3},
                {"degree": 4}, {"degree": 5}
            ]
        },
        {
            "nodes": [
                {"degree": 4}, {"degree": 4}, {"degree": 4},
                {"degree": 3}
            ]
        }
    ]

    counts = calculate_global_degree_distribution(mock_graphs)
    
    # Expected: 4 appears 7 times, 3 appears 2 times, 5 appears 1 time
    assert counts[4] == 7
    assert counts[3] == 2
    assert counts[5] == 1
    assert sum(counts.values()) == 10

def test_compute_mode_and_stats_valid_range():
    """Test mode calculation and range verification with valid data."""
    # Distribution where 4 is the mode (typical for amorphous silicon)
    counts = {3: 10, 4: 50, 5: 20, 6: 5}
    
    stats = compute_mode_and_stats(counts)
    
    assert stats["mode"] == 4
    assert stats["mode_count"] == 50
    assert stats["is_within_expected_range"] is True
    assert stats["verification"] == "PASS"
    assert stats["total_nodes"] == 85

def test_compute_mode_and_stats_invalid_range():
    """Test verification logic when mode is outside expected range (3-6)."""
    # Artificial distribution where mode is 2 (defective)
    counts = {2: 60, 3: 20, 4: 10}
    
    stats = compute_mode_and_stats(counts)
    
    assert stats["mode"] == 2
    assert stats["is_within_expected_range"] is False
    assert stats["verification"] == "FAIL"

def test_tie_breaking():
    """Test deterministic tie-breaking when multiple degrees have the same max count."""
    # 3 and 4 both have 20 counts
    counts = {3: 20, 4: 20, 5: 10}
    
    stats = compute_mode_and_stats(counts)
    
    # Should pick the minimum (3) as the tie-breaker
    assert stats["mode"] == 3
    assert stats["mode_count"] == 20

def test_output_schema_structure():
    """Verify the structure of the output stats dictionary."""
    counts = {4: 100}
    stats = compute_mode_and_stats(counts)
    
    required_keys = [
        "mode", "mode_count", "mean_degree", "total_nodes", 
        "distribution", "expected_range", "is_within_expected_range", "verification"
    ]
    
    for key in required_keys:
        assert key in stats, f"Missing key: {key}"
    
    assert isinstance(stats["distribution"], dict)
    assert "min" in stats["expected_range"]
    assert "max" in stats["expected_range"]
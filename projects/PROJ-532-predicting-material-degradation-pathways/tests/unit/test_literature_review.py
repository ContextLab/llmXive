"""
Unit tests for the Literature Review module.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

# Adjust import to match project structure if running from root
# Assuming tests are run with PYTHONPATH set to include 'code'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.literature_review import (
    extract_feature_importance,
    aggregate_importance_vectors,
    construct_literature_vector,
    REVIEW_PAPERS
)
from code import utils


def test_extract_feature_importance_ranking():
    """Test that features are scored 1/rank correctly."""
    paper = {
        "title": "Test Paper",
        "doi": "10.1000/test",
        "features": ["A", "B", "C"]
    }
    
    result = extract_feature_importance(paper)
    
    # Rank 1 (A) -> 1.0
    assert result["A"] == 1.0
    # Rank 2 (B) -> 0.5
    assert result["B"] == 0.5
    # Rank 3 (C) -> 0.333...
    assert abs(result["C"] - (1.0/3.0)) < 1e-6


def test_aggregate_importance_vectors_normalization():
    """Test that aggregation normalizes scores to 0-1."""
    papers = [
        {
            "title": "Paper 1",
            "doi": "10.1000/p1",
            "features": ["X", "Y"]
        },
        {
            "title": "Paper 2",
            "doi": "10.1000/p2",
            "features": ["Y", "Z"]
        }
    ]
    
    result = aggregate_importance_vectors(papers)
    
    # Check all values are between 0 and 1
    for score in result.values():
        assert 0.0 <= score <= 1.0
    
    # Check that max value is exactly 1.0 (due to normalization)
    assert max(result.values()) == 1.0


def test_construct_literature_vector_creates_file():
    """Test that the main function creates the JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_vector.json"
        
        # Set a fixed timestamp for deterministic testing
        os.environ["TIMESTAMP"] = "2023-01-01T00:00:00Z"
        
        result = construct_literature_vector(output_path)
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify JSON content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["source"] == "Literature Review"
        assert saved_data["papers_count"] == len(REVIEW_PAPERS)
        assert "vector" in saved_data
        assert saved_data["normalized"] is True
        assert len(saved_data["vector"]) > 0


def test_literature_vector_contains_expected_features():
    """Test that the aggregated vector contains features from the input papers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_vector.json"
        os.environ["TIMESTAMP"] = "2023-01-01T00:00:00Z"
        
        result = construct_literature_vector(output_path)
        vector = result["vector"]
        
        # These features appear in the fixed REVIEW_PAPERS list
        expected_features = {"Cr", "Ni", "Mo", "pH", "Temperature", "Fe", "Cl"}
        
        for feat in expected_features:
            assert feat in vector, f"Expected feature {feat} missing from vector"
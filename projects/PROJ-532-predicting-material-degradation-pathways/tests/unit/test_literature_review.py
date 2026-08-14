"""
Unit tests for the literature review module.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from literature_review import extract_feature_importance, aggregate_importance_vectors, construct_literature_vector, REVIEW_PAPERS

def test_extract_feature_importance():
    """Test that feature extraction correctly normalizes ranks to 0-1."""
    paper = {
        "title": "Test Paper",
        "doi": "10.1234/test",
        "features": ["A", "B", "C"]
    }
    result = extract_feature_importance(paper)
    
    assert "A" in result
    assert "B" in result
    assert "C" in result
    
    # Rank 1 -> 1.0, Rank 2 -> 0.5, Rank 3 -> 0.333...
    assert result["A"] == pytest.approx(1.0)
    assert result["B"] == pytest.approx(0.5)
    assert result["C"] == pytest.approx(1.0/3.0)

def test_aggregate_importance_vectors():
    """Test aggregation logic with two simple papers."""
    papers = [
        {"features": ["X", "Y"]},
        {"features": ["Y", "Z"]}
    ]
    
    result = aggregate_importance_vectors(papers)
    
    # X: 1.0 * 0.5 = 0.5
    # Y: (0.5 * 0.5) + (1.0 * 0.5) = 0.25 + 0.5 = 0.75
    # Z: 0.5 * 0.5 = 0.25
    
    # After normalization (max is 0.75):
    # X: 0.5/0.75 = 0.666...
    # Y: 1.0
    # Z: 0.25/0.75 = 0.333...
    
    assert "X" in result
    assert "Y" in result
    assert "Z" in result
    
    assert result["Y"] == pytest.approx(1.0)
    assert result["X"] > result["Z"]
    assert result["X"] == pytest.approx(2.0/3.0)
    assert result["Z"] == pytest.approx(1.0/3.0)

def test_construct_literature_vector_creates_file():
    """Test that construct_literature_vector actually writes the JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_vector.json"
        
        result = construct_literature_vector(output_path)
        
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            saved_data = json.load(f)
        
        assert saved_data["source"] == "Literature Review"
        assert saved_data["papers_count"] == 5
        assert len(saved_data["papers"]) == 5
        assert "vector" in saved_data
        assert saved_data["normalized"] is True
        assert "Cr" in saved_data["vector"]

def test_review_papers_defined():
    """Verify the fixed set of 5 papers is present."""
    assert len(REVIEW_PAPERS) == 5
    for paper in REVIEW_PAPERS:
        assert "title" in paper
        assert "doi" in paper
        assert "features" in paper
        assert len(paper["features"]) == 5

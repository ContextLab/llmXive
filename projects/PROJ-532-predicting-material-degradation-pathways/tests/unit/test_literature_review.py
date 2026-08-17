"""
Unit tests for the literature_review module.
"""
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path for imports if running standalone
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.literature_review import (
    load_dois_from_file,
    fetch_paper_metadata,
    extract_feature_importance,
    aggregate_importance_vectors,
    construct_literature_vector,
    KNOWN_FEATURE_RANKINGS
)
from code import utils

@pytest.fixture
def temp_dois_file(tmp_path):
    file_path = tmp_path / "literature_dois.txt"
    file_path.write_text("10.1016/j.corsci.2019.01.026\n10.1016/j.corsci.2013.06.024\n")
    return file_path

def test_load_dois_from_file(temp_dois_file):
    dois = load_dois_from_file(temp_dois_file)
    assert len(dois) == 2
    assert "10.1016/j.corsci.2019.01.026" in dois

def test_load_dois_from_file_missing():
    with pytest.raises(FileNotFoundError):
        load_dois_from_file(Path("nonexistent.txt"))

def test_extract_feature_importance_known_doi():
    doi = "10.1016/j.corsci.2019.01.026"
    weights = extract_feature_importance(doi, None)
    assert "Cr" in weights
    assert weights["Cr"] == 1.0  # Rank 1
    assert weights["Ni"] == 0.5  # Rank 2
    assert len(weights) == 5

def test_extract_feature_importance_unknown_doi():
    with pytest.raises(ValueError):
        extract_feature_importance("10.1000/unknown", None)

def test_aggregate_importance_vectors():
    # Mock data with different weights
    papers = [
        {
            "doi": "1",
            "citations": 10,
            "features": {"A": 1.0, "B": 0.5}
        },
        {
            "doi": "2",
            "citations": 10,
            "features": {"B": 1.0, "C": 0.5}
        }
    ]
    result = aggregate_importance_vectors(papers)
    # A: 1.0 * 0.5 = 0.5
    # B: (0.5 * 0.5) + (1.0 * 0.5) = 0.25 + 0.5 = 0.75
    # C: 0.5 * 0.5 = 0.25
    # Max is 0.75 (B).
    # Normalized: A=0.5/0.75, B=1.0, C=0.25/0.75
    assert "B" in result
    assert result["B"] == 1.0
    assert abs(result["A"] - (0.5/0.75)) < 0.0001

@patch('code.literature_review.requests.get')
def test_fetch_paper_metadata_success(mock_get):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "message": {
            "title": ["Test Paper"],
            "is-referenced-by-count": 42
        }
    }
    mock_get.return_value = mock_response

    meta = fetch_paper_metadata("10.1234/test")
    assert meta["title"] == "Test Paper"
    assert meta["citations"] == 42

@patch('code.literature_review.requests.get')
def test_fetch_paper_metadata_failure(mock_get):
    mock_get.side_effect = Exception("Network Error")
    meta = fetch_paper_metadata("10.1234/test")
    assert meta is None

def test_construct_literature_vector_integration(tmp_path):
    # Create a minimal dois file in tmp
    dois_file = tmp_path / "test_dois.txt"
    dois_file.write_text("10.1016/j.corsci.2019.01.026\n")
    
    output_file = tmp_path / "test_vector.json"
    
    # Patch load_dois_from_file to use our temp file
    with patch('code.literature_review.load_dois_from_file', return_value=["10.1016/j.corsci.2019.01.026"]):
        with patch('code.literature_review.fetch_paper_metadata', return_value={"title": "Test", "citations": 10}):
            result = construct_literature_vector(output_file)
    
    assert output_file.exists()
    assert result["papers_count"] == 1
    assert "vector" in result
    assert "Cr" in result["vector"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
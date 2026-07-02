"""
Unit tests for calculate_reliability.py (T007b).

Tests verify:
- Loading annotations correctly.
- Pairing logic for multiple annotators.
- Kappa calculation logic (using mock data).
- Report generation and file writing.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

# Import the module functions (assuming the file is named calculate_reliability.py)
# We need to import from the code.data package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.data.calculate_reliability import (
    load_annotations,
    prepare_ratings,
    compute_cohen_kappa,
    generate_report
)

@pytest.fixture
def sample_annotations():
    """Create a sample annotations list for testing."""
    return [
        {
            "comment_id": "c1",
            "annotations": [
                {"annotator_id": "A1", "label": "positive"},
                {"annotator_id": "A2", "label": "positive"}
            ]
        },
        {
            "comment_id": "c2",
            "annotations": [
                {"annotator_id": "A1", "label": "negative"},
                {"annotator_id": "A2", "label": "neutral"}
            ]
        },
        {
            "comment_id": "c3",
            "annotations": [
                {"annotator_id": "A1", "label": "neutral"},
                {"annotator_id": "A2", "label": "neutral"}
            ]
        }
    ]

@pytest.fixture
def temp_annotation_file(sample_annotations):
    """Create a temporary JSON file with sample annotations."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_annotations, f)
        temp_path = f.name
    yield Path(temp_path)
    os.unlink(temp_path)

def test_load_annotations_success(temp_annotation_file, sample_annotations):
    """Test that load_annotations correctly reads the JSON file."""
    data = load_annotations(temp_annotation_file)
    assert len(data) == len(sample_annotations)
    assert data[0]["comment_id"] == "c1"

def test_load_annotations_missing_file():
    """Test that load_annotations raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_annotations(Path("/nonexistent/path.json"))

def test_prepare_ratings(sample_annotations):
    """Test that prepare_ratings correctly pairs annotator labels."""
    ratings_a, ratings_b = prepare_ratings(sample_annotations)
    
    assert len(ratings_a) == 3
    assert len(ratings_b) == 3
    
    # Check specific pairs
    assert ratings_a[0] == "positive" and ratings_b[0] == "positive"
    assert ratings_a[1] == "negative" and ratings_b[1] == "neutral"
    assert ratings_a[2] == "neutral" and ratings_b[2] == "neutral"

def test_prepare_ratings_insufficient_annotators():
    """Test that prepare_ratings skips entries with <2 annotators."""
    data = [
        {
            "comment_id": "c1",
            "annotations": [
                {"annotator_id": "A1", "label": "positive"}
            ]
        },
        {
            "comment_id": "c2",
            "annotations": [
                {"annotator_id": "A1", "label": "positive"},
                {"annotator_id": "A2", "label": "negative"}
            ]
        }
    ]
    ratings_a, ratings_b = prepare_ratings(data)
    assert len(ratings_a) == 1  # Only c2 should be included
    assert ratings_a[0] == "positive"

def test_compute_cohen_kappa_perfect_agreement():
    """Test Kappa calculation with perfect agreement (Kappa should be 1.0)."""
    a = ["pos", "neg", "neu", "pos"]
    b = ["pos", "neg", "neu", "pos"]
    stats = compute_cohen_kappa(a, b)
    assert stats["kappa"] == 1.0
    assert stats["agreement_observed"] == 1.0

def test_compute_cohen_kappa_no_agreement():
    """Test Kappa calculation with no agreement (Kappa should be 0.0 or negative)."""
    # Create data where observed agreement is low but expected is non-zero
    # A: [A, A, A, A]
    # B: [B, B, B, B]
    # Observed = 0, Expected = 0 (if categories are disjoint and balanced? No, marginals matter)
    # Let's use a simple case:
    # A: [0, 0, 1, 1]
    # B: [1, 1, 0, 0]
    # Observed = 0.
    # Marginals: A has 2 of 0, 2 of 1. B has 2 of 0, 2 of 1.
    # Expected = (0.5*0.5) + (0.5*0.5) = 0.5.
    # Kappa = (0 - 0.5) / (1 - 0.5) = -1.0.
    
    a = [0, 0, 1, 1]
    b = [1, 1, 0, 0]
    stats = compute_cohen_kappa(a, b)
    assert np.isclose(stats["kappa"], -1.0)
    assert stats["agreement_observed"] == 0.0

def test_generate_report():
    """Test that generate_report produces the correct structure."""
    stats = {
        "kappa": 0.8,
        "n_pairs": 100,
        "agreement_observed": 0.9,
        "agreement_expected": 0.5,
        "categories": ["pos", "neg", "neu"]
    }
    report = generate_report(stats)
    
    assert report["status"] == "completed"
    assert report["metric"] == "Cohen's Kappa"
    assert report["results"]["kappa"] == 0.8
    assert report["validation"]["is_valid"] is True
    assert report["metadata"]["task_id"] == "T007b"

def test_empty_ratings_raises_error():
    """Test that compute_cohen_kappa raises ValueError for empty inputs."""
    with pytest.raises(ValueError):
        compute_cohen_kappa([], [])
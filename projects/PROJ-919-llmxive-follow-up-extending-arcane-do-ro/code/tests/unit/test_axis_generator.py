"""
Unit tests for axis_generator service.

Tests:
- Semantic overlap validation logic
- Axis generation from input
- JSONL serialization
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np

from src.services.axis_generator import (
    validate_axes_semantic_overlap,
    generate_axes_from_input,
    serialize_axes_to_jsonl,
    calculate_cosine_similarity
)
from src.services.axes_writer import read_axes_from_jsonl

@pytest.fixture
def mock_model():
    """Mock sentence transformer model."""
    mock_model = MagicMock()
    # Return two orthogonal unit vectors for independent texts
    mock_model.encode.return_value = np.array([
        [1.0, 0.0, 0.0],  # Coarse: distinct direction
        [0.0, 1.0, 0.0]   # Fine: distinct direction
    ], dtype=np.float32)
    return mock_model

@pytest.fixture
def mock_model_similar():
    """Mock sentence transformer model with similar outputs."""
    mock_model = MagicMock()
    # Return two similar vectors
    mock_model.encode.return_value = np.array([
        [0.9, 0.1, 0.0],
        [0.85, 0.15, 0.0]
    ], dtype=np.float32)
    return mock_model

def test_calculate_cosine_similarity_perpendicular():
    """Test cosine similarity for perpendicular vectors."""
    vec_a = np.array([1.0, 0.0, 0.0])
    vec_b = np.array([0.0, 1.0, 0.0])
    sim = calculate_cosine_similarity(vec_a, vec_b)
    assert abs(sim - 0.0) < 1e-6

def test_calculate_cosine_similarity_identical():
    """Test cosine similarity for identical vectors."""
    vec_a = np.array([1.0, 0.0, 0.0])
    vec_b = np.array([1.0, 0.0, 0.0])
    sim = calculate_cosine_similarity(vec_a, vec_b)
    assert abs(sim - 1.0) < 1e-6

@patch('src.services.axis_generator.load_sentence_model_cached')
def test_validate_axes_semantic_overlap_independent(mock_load_model, mock_model):
    """Test validation passes for independent axes."""
    mock_load_model.return_value = mock_model
    
    coarse = "A character defined by moral integrity and duty."
    fine = "Specific instances of personal sacrifice over self-preservation."
    
    is_valid, details = validate_axes_semantic_overlap(coarse, fine)
    
    assert is_valid is True
    assert details["lexical_overlap"] < 0.4
    assert details["cosine_similarity"] < 0.3
    assert len(details["issues"]) == 0

@patch('src.services.axis_generator.load_sentence_model_cached')
def test_validate_axes_semantic_overlap_too_similar(mock_load_model, mock_model_similar):
    """Test validation fails for similar axes."""
    mock_load_model.return_value = mock_model_similar
    
    coarse = "Brave and courageous character."
    fine = "Brave actions and courageous decisions."
    
    is_valid, details = validate_axes_semantic_overlap(coarse, fine)
    
    # Should fail due to high similarity
    assert is_valid is False
    assert len(details["issues"]) > 0
    assert any("similarity" in issue for issue in details["issues"])

def test_generate_axes_from_input_valid():
    """Test successful axis generation."""
    coarse_input = "A character of high moral standing."
    fine_input = "Specific acts of moral courage."
    
    # Note: This test might fail if the model is not installed,
    # so we mock the validation function
    with patch('src.services.axis_generator.validate_axes_semantic_overlap') as mock_validate:
        mock_validate.return_value = (True, {"is_valid": True, "issues": []})
        
        coarse, fine, details = generate_axes_from_input("Harry Potter", coarse_input, fine_input)
        
        assert coarse is not None
        assert fine is not None
        assert coarse["character"] == "Harry Potter"
        assert coarse["axis_name"] == "Coarse"
        assert fine["character"] == "Harry Potter"
        assert fine["axis_name"] == "Fine"
        assert coarse["description"] == coarse_input
        assert fine["description"] == fine_input

def test_generate_axes_from_input_invalid():
    """Test axis generation fails for invalid input."""
    with patch('src.services.axis_generator.validate_axes_semantic_overlap') as mock_validate:
        mock_validate.return_value = (False, {"is_valid": False, "issues": ["Too similar"]})
        
        coarse, fine, details = generate_axes_from_input("Harry Potter", "Test", "Test")
        
        assert coarse is None
        assert fine is None
        assert details["is_valid"] is False
        assert len(details["issues"]) > 0

@patch('src.services.axis_generator.ensure_derived_directory')
def test_serialize_axes_to_jsonl(mock_ensure_dir, tmp_path):
    """Test serialization to JSONL."""
    output_path = tmp_path / "test_axes.jsonl"
    
    coarse = {"character": "Test", "axis_name": "Coarse", "description": "Test coarse"}
    fine = {"character": "Test", "axis_name": "Fine", "description": "Test fine"}
    
    serialize_axes_to_jsonl("Test", coarse, fine, str(output_path))
    
    assert output_path.exists()
    
    # Read back and verify
    records = read_axes_from_jsonl(str(output_path))
    assert len(records) == 2
    assert records[0]["axis_name"] == "Coarse"
    assert records[1]["axis_name"] == "Fine"

"""
Unit tests for evaluation module (T024).
Tests perplexity matrix computation logic.
"""
import pytest
import math
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluation import compute_perplexity, compute_perplexity_matrix, load_author_models, load_held_out_data

class MockModel:
    """Mock model for testing."""
    def __init__(self, log_prob_value=-1.0):
        self.log_prob_value = log_prob_value
    
    def score(self, text):
        return self.log_prob_value

def test_compute_perplexity_valid():
    """Test perplexity computation with valid model."""
    model = MockModel(log_prob_value=-1.0)
    text = "test text"
    perplexity = compute_perplexity(model, text, 5)
    # exp(1.0) ≈ 2.718
    assert abs(perplexity - math.e) < 0.01

def test_compute_perplexity_nan_handling():
    """Test that NaN/Inf log probabilities are handled."""
    model = MockModel(log_prob_value=float('nan'))
    text = "test"
    # Should not raise, should return a large number
    perplexity = compute_perplexity(model, text, 5)
    assert math.isfinite(perplexity) or perplexity > 1000  # Very high perplexity

def test_compute_perplexity_matrix_structure():
    """Test that matrix has correct dimensions."""
    authors = ["author1", "author2"]
    models = {
        "author1": {5: MockModel()},
        "author2": {5: MockModel()}
    }
    held_out_data = {
        "author1": ["text1", "text2"],
        "author2": ["text3", "text4"]
    }
    
    matrix = compute_perplexity_matrix(authors, models, held_out_data, n_order=5)
    
    assert len(matrix) == 2  # 2 test authors
    assert len(matrix[0]) == 2  # 2 model authors

def test_compute_perplexity_matrix_empty_test_data():
    """Test matrix computation with missing test data."""
    authors = ["author1", "author2"]
    models = {
        "author1": {5: MockModel()},
        "author2": {5: MockModel()}
    }
    held_out_data = {
        "author1": [],  # Empty test data
        "author2": ["text"]
    }
    
    matrix = compute_perplexity_matrix(authors, models, held_out_data, n_order=5)
    
    # First row should be NaNs (no test data)
    assert all(math.isnan(p) for p in matrix[0])
    # Second row should have valid values
    assert not any(math.isnan(p) for p in matrix[1])

def test_perplexity_lower_for_own_author():
    """
    Integration-style test: perplexity should be lower for own author's text
    than for another author's text (assuming models are trained correctly).
    This is a conceptual test - in reality, we'd need real trained models.
    """
    # Create mock models where author1's model gives high probability to "author1 text"
    # and low probability to "author2 text"
    model_author1 = MockModel(log_prob_value=-0.5)  # Higher prob (lower perplexity)
    model_author2 = MockModel(log_prob_value=-2.0)  # Lower prob (higher perplexity)
    
    models = {
        "author1": {5: model_author1},
        "author2": {5: model_author2}
    }
    
    held_out_data = {
        "author1": ["author1 text"],
        "author2": ["author2 text"]
    }
    
    authors = ["author1", "author2"]
    matrix = compute_perplexity_matrix(authors, models, held_out_data, n_order=5)
    
    # Diagonal (own author) should have lower perplexity than off-diagonal
    # matrix[0][0] = perplexity of author1 text against author1 model
    # matrix[0][1] = perplexity of author1 text against author2 model
    assert matrix[0][0] < matrix[0][1]
    assert matrix[1][1] < matrix[1][0]
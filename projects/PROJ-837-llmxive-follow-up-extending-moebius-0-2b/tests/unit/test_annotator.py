import pytest
import numpy as np
import sys
from pathlib import Path
import tempfile
import csv

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.annotator import (
    generate_ci_scores, 
    validate_sample_size,
    validate_label_independence
)

class TestAnnotator:
    def test_generate_ci_scores_basic(self):
        """Test CI score generation"""
        np.random.seed(42)
        scores = generate_ci_scores(50)
        
        assert len(scores) == 50
        assert all(1 <= s <= 5 for s in scores)

    def test_generate_ci_scores_distribution(self):
        """Test that CI scores are uniformly distributed"""
        np.random.seed(123)
        scores = generate_ci_scores(1000)
        
        mean_score = np.mean(scores)
        # For uniform [1, 5], mean should be ~3.0
        assert 2.5 < mean_score < 3.5

    def test_generate_ci_scores_reproducibility(self):
        """Test that same seed produces same scores"""
        np.random.seed(999)
        scores1 = generate_ci_scores(50)
        
        np.random.seed(999)
        scores2 = generate_ci_scores(50)
        
        assert np.array_equal(scores1, scores2)

    def test_validate_sample_size_valid(self):
        """Test sample size validation with valid size"""
        is_valid, message = validate_sample_size(50)
        assert is_valid is True

    def test_validate_sample_size_invalid(self):
        """Test sample size validation with invalid size"""
        is_valid, message = validate_sample_size(10)
        assert is_valid is False
        assert "insufficient" in message.lower()

    def test_validate_sample_size_zero(self):
        """Test sample size validation with zero"""
        is_valid, message = validate_sample_size(0)
        assert is_valid is False

    def test_validate_label_independence_high_correlation(self):
        """Test independence validation with high correlation"""
        # Create highly correlated data
        np.random.seed(42)
        x = np.random.rand(100)
        y = x * 0.9 + 0.1  # Highly correlated
        
        is_independent, r, message = validate_label_independence(x, y)
        
        assert is_independent is False
        assert abs(r) > 0.8

    def test_validate_label_independence_low_correlation(self):
        """Test independence validation with low correlation"""
        np.random.seed(42)
        x = np.random.rand(100)
        y = np.random.rand(100)  # Uncorrelated
        
        is_independent, r, message = validate_label_independence(x, y)
        
        # Should pass independence check (low correlation)
        assert abs(r) < 0.3

    def test_validate_label_independence_threshold(self):
        """Test independence validation threshold"""
        np.random.seed(42)
        x = np.random.rand(100)
        y = x * 0.05 + np.random.rand(100) * 0.1  # Very low correlation
        
        is_independent, r, message = validate_label_independence(x, y)
        
        assert is_independent is True
        assert abs(r) < 0.1

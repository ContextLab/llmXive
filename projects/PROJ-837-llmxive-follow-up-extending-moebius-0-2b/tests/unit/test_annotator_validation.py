"""
Unit tests for annotator validation logic (T016).

Tests sample size validation and label independence checks.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import os

from data.annotator import (
    validate_sample_size,
    validate_label_independence,
    log_validation,
    MIN_SAMPLE_SIZE
)

class TestSampleSizeValidation:
    """Tests for validate_sample_size function."""
    
    def test_passes_with_sufficient_samples(self):
        """Should pass when sample size >= MIN_SAMPLE_SIZE."""
        annotations = [
            {'image_id': f'img_{i}', 'score': 3.0, 'rater_id': 'rater1'}
            for i in range(MIN_SAMPLE_SIZE)
        ]
        
        result = validate_sample_size(annotations)
        assert result is True
    
    def test_fails_with_insufficient_samples(self):
        """Should raise ValueError when sample size < MIN_SAMPLE_SIZE."""
        annotations = [
            {'image_id': f'img_{i}', 'score': 3.0, 'rater_id': 'rater1'}
            for i in range(MIN_SAMPLE_SIZE - 10)
        ]
        
        with pytest.raises(ValueError, match="Sample size validation failed"):
            validate_sample_size(annotations)
    
    def test_counts_unique_images(self):
        """Should count unique image_ids, not total annotations."""
        # Same image, multiple raters
        annotations = [
            {'image_id': 'img_1', 'score': 3.0, 'rater_id': 'rater1'},
            {'image_id': 'img_1', 'score': 3.5, 'rater_id': 'rater2'},
            {'image_id': 'img_1', 'score': 3.2, 'rater_id': 'rater3'},
        ]
        
        with pytest.raises(ValueError, match="Sample size validation failed"):
            validate_sample_size(annotations)
    
    def test_passes_with_duplicates_but_enough_unique(self):
        """Should pass if unique images meet threshold despite duplicates."""
        annotations = []
        for i in range(MIN_SAMPLE_SIZE):
            # Each image has 2 raters
            annotations.append({'image_id': f'img_{i}', 'score': 3.0, 'rater_id': 'rater1'})
            annotations.append({'image_id': f'img_{i}', 'score': 3.5, 'rater_id': 'rater2'})
        
        result = validate_sample_size(annotations)
        assert result is True

class TestLabelIndependenceValidation:
    """Tests for validate_label_independence function."""
    
    def test_passes_with_uncorrelated_data(self):
        """Should pass when scores and metrics are uncorrelated."""
        # Generate uncorrelated data
        np.random.seed(42)
        n = 100
        
        scores = [
            {'image_id': f'img_{i}', 'score': np.random.uniform(1, 5)}
            for i in range(n)
        ]
        metrics = [
            {'image_id': f'img_{i}', 'gradient_variance': np.random.uniform(0, 1)}
            for i in range(n)
        ]
        
        result = validate_label_independence(scores, metrics)
        assert result is True
    
    def test_fails_with_highly_correlated_data(self):
        """Should raise ValueError when scores correlate with metrics."""
        n = 100
        
        # Create highly correlated data
        base = np.random.uniform(0, 1, n)
        scores = [
            {'image_id': f'img_{i}', 'score': float(base[i] * 4 + 1)}
            for i in range(n)
        ]
        metrics = [
            {'image_id': f'img_{i}', 'gradient_variance': float(base[i])}
            for i in range(n)
        ]
        
        with pytest.raises(ValueError, match="Label independence check FAILED"):
            validate_label_independence(scores, metrics)
    
    def test_handles_missing_pairs_gracefully(self):
        """Should handle cases where some image_ids don't match."""
        scores = [
            {'image_id': 'img_1', 'score': 3.0},
            {'image_id': 'img_2', 'score': 3.5},
            {'image_id': 'img_3', 'score': 4.0},
        ]
        metrics = [
            {'image_id': 'img_1', 'gradient_variance': 0.5},
            # img_2 missing
            {'image_id': 'img_3', 'gradient_variance': 0.8},
        ]
        
        # Should pass with 2 paired samples (above threshold of 10? No, will warn but pass)
        # Actually with only 2 pairs, it will warn but not raise
        result = validate_label_independence(scores, metrics)
        # With <10 pairs, it returns True after warning
        assert result is True
    
    def test_uses_gradient_variance_by_default(self):
        """Should use gradient_variance when available."""
        n = 50
        scores = [
            {'image_id': f'img_{i}', 'score': 3.0}
            for i in range(n)
        ]
        metrics = [
            {'image_id': f'img_{i}', 'gradient_variance': 0.5, 'texture_entropy': 0.8}
            for i in range(n)
        ]
        
        result = validate_label_independence(scores, metrics)
        assert result is True

class TestLogValidation:
    """Tests for log_validation function."""
    
    def test_creates_file_and_appends(self):
        """Should create file if not exists and append message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'validation_log.txt'
            
            log_validation("Test message 1", log_path)
            log_validation("Test message 2", log_path)
            
            assert log_path.exists()
            content = log_path.read_text()
            assert "Test message 1" in content
            assert "Test message 2" in content
            assert content.count("Test message") == 2
    
    def test_creates_parent_directories(self):
        """Should create parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'subdir' / 'nested' / 'validation_log.txt'
            
            log_validation("Test message", log_path)
            
            assert log_path.exists()
            assert log_path.parent.exists()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

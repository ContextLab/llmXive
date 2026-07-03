"""
Unit tests for stratified subsampling logic in code/subsample.py.

These tests verify:
1. Target column detection priority
2. Class ratio preservation in stratified subsamples
3. Edge case handling for insufficient class counts
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from subsample import (
    detect_target_column,
    validate_class_counts,
    create_stratified_subsample,
    process_dataset,
    log_skipped_configuration
)


class TestTargetColumnDetection:
    """Tests for target column detection logic."""

    def test_priority_target(self):
        """Test that 'target' column is detected when present."""
        df = pd.DataFrame({
            'feature1': [1, 2, 3],
            'target': [0, 1, 0],
            'class': [1, 1, 0]
        })
        assert detect_target_column(df) == 'target'

    def test_priority_class(self):
        """Test that 'class' column is detected when 'target' is absent."""
        df = pd.DataFrame({
            'feature1': [1, 2, 3],
            'class': [0, 1, 0],
            'label': [1, 1, 0]
        })
        assert detect_target_column(df) == 'class'

    def test_priority_label(self):
        """Test that 'label' column is detected when 'target' and 'class' are absent."""
        df = pd.DataFrame({
            'feature1': [1, 2, 3],
            'label': [0, 1, 0],
            'other': [1, 1, 0]
        })
        assert detect_target_column(df) == 'label'

    def test_default_last_column(self):
        """Test that last column is used when no priority names exist."""
        df = pd.DataFrame({
            'feature1': [1, 2, 3],
            'feature2': [4, 5, 6],
            'outcome': [0, 1, 0]
        })
        assert detect_target_column(df) == 'outcome'


class TestStratifiedSubsampling:
    """Tests for stratified subsampling logic."""

    def test_class_ratio_preservation(self):
        """Test that class ratios are preserved in subsamples."""
        # Create balanced dataset (50% each class)
        n_samples = 100
        df = pd.DataFrame({
            'feature1': np.random.randn(n_samples),
            'target': [0] * 50 + [1] * 50
        })

        subsample = create_stratified_subsample(df, 'target', n=20, random_state=42)

        # Check class distribution
        class_counts = subsample['target'].value_counts()
        assert class_counts[0] == 10
        assert class_counts[1] == 10

    def test_stratified_sampling_unbalanced(self):
        """Test stratified sampling with imbalanced classes."""
        # Create imbalanced dataset (80% class 0, 20% class 1)
        n_samples = 100
        df = pd.DataFrame({
            'feature1': np.random.randn(n_samples),
            'target': [0] * 80 + [1] * 20
        })

        subsample = create_stratified_subsample(df, 'target', n=25, random_state=42)

        # Check class distribution (approximately 80/20)
        class_counts = subsample['target'].value_counts()
        # With 25 samples, we expect ~20 class 0 and ~5 class 1
        assert class_counts[0] + class_counts[1] == 25
        assert abs(class_counts[0] - 20) <= 2  # Allow small rounding variation

    def test_insufficient_samples(self):
        """Test that sampling fails gracefully with insufficient samples."""
        # Create dataset with only 3 samples of one class
        df = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5, 6],
            'target': [0, 0, 0, 1, 1, 1]
        })

        # Should return None for N=15 when min class count is 3
        result = create_stratified_subsample(df, 'target', n=15, random_state=42)
        assert result is None


class TestValidation:
    """Tests for validation logic."""

    def test_validate_class_counts_valid(self):
        """Test validation passes with sufficient class counts."""
        df = pd.DataFrame({
            'feature1': [1] * 20,
            'target': [0] * 10 + [1] * 10
        })
        is_valid, msg = validate_class_counts(df, 'target', n=15)
        assert is_valid is True
        assert msg == "Valid"

    def test_validate_class_counts_insufficient(self):
        """Test validation fails with insufficient class counts."""
        df = pd.DataFrame({
            'feature1': [1] * 10,
            'target': [0] * 8 + [1] * 2
        })
        is_valid, msg = validate_class_counts(df, 'target', n=15)
        assert is_valid is False
        assert "Min class count" in msg or "Minimum class count" in msg


class TestProcessDataset:
    """Tests for full dataset processing."""

    def test_process_balanced_dataset(self):
        """Test processing a balanced dataset."""
        df = pd.DataFrame({
            'feature1': np.random.randn(100),
            'target': [0] * 50 + [1] * 50
        })

        results = process_dataset(df, 'test_dataset', random_state=42)

        # Should have subsamples for N=15, 25, 40
        assert 15 in results
        assert 25 in results
        assert 40 in results

        # Check sizes
        assert len(results[15]) == 15
        assert len(results[25]) == 25
        assert len(results[40]) == 40

    def test_process_imbalanced_dataset(self):
        """Test processing an imbalanced dataset that triggers skips."""
        # Create dataset with only 4 samples of one class
        df = pd.DataFrame({
            'feature1': np.random.randn(50),
            'target': [0] * 46 + [1] * 4
        })

        results = process_dataset(df, 'test_imbalanced', random_state=42)

        # N=15, 25, 40 should all be skipped due to min class count < 5
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
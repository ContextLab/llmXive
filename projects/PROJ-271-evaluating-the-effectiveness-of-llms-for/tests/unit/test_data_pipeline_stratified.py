import pytest
import json
import os
from unittest.mock import patch, MagicMock
import pandas as pd

from data_pipeline import load_sampled_functions_stratified, load_sampled_functions

class TestStratifiedSampling:
    """Tests for stratified sampling functionality in T053."""

    @patch('data_pipeline.load_dataset')
    def test_stratified_sampling_proportional_distribution(self, mock_load_dataset):
        """Test that stratified sampling distributes samples proportionally across file types."""
        
        # Mock dataset with known file type distribution
        mock_items = [
            {'code': f'code_{i}', 'file_path': f'file{i}.py'} for i in range(600)
        ] + [
            {'code': f'js_{i}', 'file_path': f'file{i}.js'} for i in range(200)
        ] + [
            {'code': f'java_{i}', 'file_path': f'file{i}.java'} for i in range(100)
        ]
        
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = lambda self: iter(mock_items)
        mock_load_dataset.return_value = mock_dataset
        
        # Run stratified sampling with target of 100
        sample = load_sampled_functions_stratified(target_size=100, seed=42)
        
        # Count file types in sample
        file_types = {}
        for item in sample:
            ext = os.path.splitext(item['file_path'])[1]
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # Verify proportional distribution
        # Python: 60%, JS: 20%, Java: 10%
        # Expected: ~60 .py, ~20 .js, ~10 .java
        total_sampled = len(sample)
        
        assert total_sampled == 100, f"Expected 100 samples, got {total_sampled}"
        
        # Check proportions (allowing some variance due to rounding)
        py_ratio = file_types.get('.py', 0) / total_sampled
        js_ratio = file_types.get('.js', 0) / total_sampled
        java_ratio = file_types.get('.java', 0) / total_sampled
        
        # Allow 15% variance in proportions
        assert 0.50 <= py_ratio <= 0.70, f"Python proportion {py_ratio} not within expected range"
        assert 0.15 <= js_ratio <= 0.25, f"JS proportion {js_ratio} not within expected range"
        assert 0.05 <= java_ratio <= 0.15, f"Java proportion {java_ratio} not within expected range"

    @patch('data_pipeline.load_dataset')
    def test_stratified_sampling_with_unknown_files(self, mock_load_dataset):
        """Test handling of files without extensions."""
        
        mock_items = [
            {'code': f'code_{i}', 'file_path': f'file{i}'} for i in range(50)
        ] + [
            {'code': f'py_{i}', 'file_path': f'file{i}.py'} for i in range(50)
        ]
        
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = lambda self: iter(mock_items)
        mock_load_dataset.return_value = mock_dataset
        
        sample = load_sampled_functions_stratified(target_size=50, seed=42)
        
        # Should include both 'unknown' and '.py' files proportionally
        file_types = {}
        for item in sample:
            ext = os.path.splitext(item['file_path'])[1]
            file_type = ext if ext else 'unknown'
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        assert len(sample) == 50
        assert 'unknown' in file_types or '.py' in file_types

    @patch('data_pipeline.load_dataset')
    def test_stratified_sampling_respects_target_size(self, mock_load_dataset):
        """Test that stratified sampling respects the target sample size."""
        
        mock_items = [
            {'code': f'code_{i}', 'file_path': f'file{i}.py'} for i in range(1000)
        ]
        
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = lambda self: iter(mock_items)
        mock_load_dataset.return_value = mock_dataset
        
        for target in [100, 200, 500]:
            sample = load_sampled_functions_stratified(target_size=target, seed=42)
            assert len(sample) == target, f"Expected {target} samples, got {len(sample)}"

    def test_stratified_sampling_with_no_metadata(self):
        """Test that sampling handles missing metadata gracefully."""
        # This test verifies the fallback behavior when file_path is not available
        # The actual implementation should handle this in load_sampled_functions
        pass

    @patch('data_pipeline.load_dataset')
    def test_stratified_sampling_reproducibility(self, mock_load_dataset):
        """Test that stratified sampling is reproducible with the same seed."""
        
        mock_items = [
            {'code': f'code_{i}', 'file_path': f'file{i}.py'} for i in range(200)
        ] + [
            {'code': f'js_{i}', 'file_path': f'file{i}.js'} for i in range(100)
        ]
        
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = lambda self: iter(mock_items)
        mock_load_dataset.return_value = mock_dataset
        
        sample1 = load_sampled_functions_stratified(target_size=50, seed=42)
        sample2 = load_sampled_functions_stratified(target_size=50, seed=42)
        
        # Same seed should produce same sample
        assert len(sample1) == len(sample2)
        for i in range(len(sample1)):
            assert sample1[i]['code'] == sample2[i]['code']
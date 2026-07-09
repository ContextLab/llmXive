"""
Tests for time-based train/test splitting functionality.

Tests FR-008: Held-out dataset split for statistical validation.
"""

import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from code.data.split import TimeBasedSplitter, run_split
from utils.memory_monitor import MemoryExceededError


class TestTimeBasedSplitter:
    """Unit tests for TimeBasedSplitter class."""

    def test_split_indices_basic(self):
        """Test basic index splitting."""
        splitter = TimeBasedSplitter(train_ratio=0.8)
        train_idx, test_idx = splitter.split_indices(100)
        
        assert len(train_idx) == 80
        assert len(test_idx) == 20
        assert set(train_idx).isdisjoint(set(test_idx))
        assert len(train_idx) + len(test_idx) == 100
    
    def test_split_indices_with_timestamps(self):
        """Test splitting with explicit timestamps."""
        splitter = TimeBasedSplitter(train_ratio=0.7)
        
        # Create timestamps that are not in order
        timestamps = np.array([5, 2, 8, 1, 9, 3, 7, 4, 6, 0])
        train_idx, test_idx = splitter.split_indices(10, timestamps)
        
        # After sorting by timestamp, first 7 should be train, last 3 test
        sorted_indices = np.argsort(timestamps)
        expected_train = sorted_indices[:7]
        expected_test = sorted_indices[7:]
        
        assert set(train_idx) == set(expected_train)
        assert set(test_idx) == set(expected_test)
    
    def test_split_indices_invalid_ratio(self):
        """Test that invalid ratios raise errors."""
        with pytest.raises(ValueError):
            TimeBasedSplitter(train_ratio=0.0)
        
        with pytest.raises(ValueError):
            TimeBasedSplitter(train_ratio=1.0)
        
        with pytest.raises(ValueError):
            TimeBasedSplitter(train_ratio=-0.1)
    
    def test_split_indices_too_few_samples(self):
        """Test splitting with insufficient samples."""
        splitter = TimeBasedSplitter()
        
        with pytest.raises(ValueError):
            splitter.split_indices(1)
        
        with pytest.raises(ValueError):
            splitter.split_indices(0)
    
    def test_split_arrays(self):
        """Test splitting multiple arrays consistently."""
        splitter = TimeBasedSplitter(train_ratio=0.6)
        
        arr1 = np.random.rand(100, 10)
        arr2 = np.random.rand(100, 5)
        
        (train1, test1), (train2, test2) = splitter.split_arrays(arr1, arr2)
        
        assert train1.shape[0] == 60
        assert test1.shape[0] == 40
        assert train2.shape[0] == 60
        assert test2.shape[0] == 40
        
        # Verify indices are consistent
        assert np.all(train1[:, 0] == arr1[train_idx, 0])
    
    def test_split_dataframe(self):
        """Test splitting a DataFrame."""
        splitter = TimeBasedSplitter(train_ratio=0.75)
        
        df = pd.DataFrame({
            'id': range(100),
            'value': np.random.rand(100),
            'timestamp': pd.date_range('2023-01-01', periods=100, freq='H')
        })
        
        train_df, test_df = splitter.split_dataframe(df, time_column='timestamp')
        
        assert len(train_df) == 75
        assert len(test_df) == 25
        assert train_df['id'].is_monotonic_increasing
        assert test_df['id'].is_monotonic_increasing
    
    def test_split_dataframe_no_time_column(self):
        """Test splitting without explicit time column."""
        splitter = TimeBasedSplitter(train_ratio=0.5)
        
        df = pd.DataFrame({
            'id': range(10),
            'value': range(10)
        })
        
        train_df, test_df = splitter.split_dataframe(df)
        
        assert len(train_df) == 5
        assert len(test_df) == 5
        assert list(train_df['id']) == [0, 1, 2, 3, 4]
        assert list(test_df['id']) == [5, 6, 7, 8, 9]

    def test_save_split_metadata(self):
        """Test saving split metadata."""
        splitter = TimeBasedSplitter(train_ratio=0.8)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = splitter.save_split_metadata(
                tmpdir,
                n_train=80,
                n_test=20,
                train_ratio=0.8,
                split_info={'extra': 'data'}
            )
            
            assert os.path.exists(path)
            
            with open(path, 'r') as f:
                metadata = json.load(f)
            
            assert metadata['train_ratio'] == 0.8
            assert metadata['n_train'] == 80
            assert metadata['n_test'] == 20
            assert metadata['extra'] == 'data'
            assert 'timestamp' in metadata

class TestRunSplit:
    """Integration tests for run_split function."""

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample CSV file for testing."""
        df = pd.DataFrame({
            'id': range(100),
            'value': np.random.rand(100),
            'timestamp': pd.date_range('2023-01-01', periods=100, freq='H')
        })
        csv_path = tmp_path / "sample_data.csv"
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    def test_run_split_csv(self, sample_csv, tmp_path):
        """Test splitting a CSV file."""
        output_dir = tmp_path / "splits"
        
        result = run_split(
            input_path=sample_csv,
            output_dir=str(output_dir),
            train_ratio=0.8
        )
        
        assert 'train' in result
        assert 'test' in result
        assert 'metadata' in result
        
        assert os.path.exists(result['train'])
        assert os.path.exists(result['test'])
        assert os.path.exists(result['metadata'])
        
        # Verify split sizes
        train_df = pd.read_csv(result['train'])
        test_df = pd.read_csv(result['test'])
        
        assert len(train_df) == 80
        assert len(test_df) == 20
    
    def test_run_split_with_time_column(self, sample_csv, tmp_path):
        """Test splitting with explicit time column."""
        output_dir = tmp_path / "splits"
        
        result = run_split(
            input_path=sample_csv,
            output_dir=str(output_dir),
            train_ratio=0.7,
            time_column='timestamp'
        )
        
        train_df = pd.read_csv(result['train'])
        test_df = pd.read_csv(result['test'])
        
        assert len(train_df) == 70
        assert len(test_df) == 30
        
        # Verify temporal ordering (all train timestamps < all test timestamps)
        max_train_time = train_df['timestamp'].max()
        min_test_time = test_df['timestamp'].min()
        
        assert max_train_time < min_test_time
    
    def test_run_split_nonexistent_file(self, tmp_path):
        """Test splitting a non-existent file."""
        with pytest.raises(FileNotFoundError):
            run_split(
                input_path=str(tmp_path / "nonexistent.csv"),
                output_dir=str(tmp_path / "splits")
            )

class TestSplitValidation:
    """Tests for split validation requirements (FR-008)."""

    def test_majority_to_minority_ratio(self, tmp_path):
        """Verify majority-to-minority ratio is maintained."""
        df = pd.DataFrame({
            'id': range(200),
            'value': np.random.rand(200)
        })
        csv_path = tmp_path / "data.csv"
        df.to_csv(csv_path, index=False)
        
        splitter = TimeBasedSplitter(train_ratio=0.8)
        train_df, test_df = splitter.split_dataframe(df)
        
        # Train should be majority (>= 50%)
        assert len(train_df) > len(test_df)
        
        # Verify ratio is approximately correct
        actual_ratio = len(train_df) / len(df)
        assert abs(actual_ratio - 0.8) < 0.01

    def test_no_temporal_leakage(self, tmp_path):
        """Verify no temporal leakage between train and test sets."""
        timestamps = pd.date_range('2023-01-01', periods=100, freq='H')
        df = pd.DataFrame({
            'id': range(100),
            'value': np.random.rand(100),
            'timestamp': timestamps
        })
        csv_path = tmp_path / "time_data.csv"
        df.to_csv(csv_path, index=False)
        
        splitter = TimeBasedSplitter(train_ratio=0.8)
        train_df, test_df = splitter.split_dataframe(df, time_column='timestamp')
        
        # All training timestamps must be earlier than all test timestamps
        max_train_time = train_df['timestamp'].max()
        min_test_time = test_df['timestamp'].min()
        
        assert max_train_time < min_test_time, \
            "Temporal leakage detected: train set contains future data"

    def test_split_metadata_contains_validation_info(self, tmp_path):
        """Verify split metadata contains required validation information."""
        df = pd.DataFrame({'id': range(50), 'value': np.random.rand(50)})
        csv_path = tmp_path / "data.csv"
        df.to_csv(csv_path, index=False)
        
        result = run_split(
            input_path=str(csv_path),
            output_dir=str(tmp_path / "splits"),
            train_ratio=0.8
        )
        
        with open(result['metadata'], 'r') as f:
            metadata = json.load(f)
        
        # Check required fields for validation
        assert 'split_type' in metadata
        assert metadata['split_type'] == 'time_based'
        assert 'train_ratio' in metadata
        assert 'n_train' in metadata
        assert 'n_test' in metadata
        assert 'total_samples' in metadata
        assert metadata['total_samples'] == metadata['n_train'] + metadata['n_test']
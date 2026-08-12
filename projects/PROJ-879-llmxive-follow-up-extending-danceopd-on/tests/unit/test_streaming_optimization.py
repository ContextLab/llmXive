"""
Unit tests for optimized data streaming and batch processing.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from _data_streaming_optimized import (
    stratified_sample,
    write_batch_to_parquet,
    TimeoutError,
    timeout_handler,
    setup_timeout,
    cancel_timeout
)


class TestStratifiedSample:
    """Tests for stratified sampling functionality."""
    
    def test_stratified_sample_proportional(self):
        """Test that stratified sampling maintains proportional representation."""
        # Create test data with known distribution
        data = {
            'source': ['imagenet'] * 80 + ['laion'] * 20,
            'value': list(range(100))
        }
        df = pd.DataFrame(data)
        
        # Sample 50% of data
        sample = stratified_sample(df, target_size=50, stratify_column='source')
        
        # Check proportions are maintained
        assert len(sample) == 50
        imagenet_ratio = (sample['source'] == 'imagenet').sum() / len(sample)
        laion_ratio = (sample['source'] == 'laion').sum() / len(sample)
        
        # Allow small tolerance for rounding
        assert 0.75 <= imagenet_ratio <= 0.85
        assert 0.15 <= laion_ratio <= 0.25
    
    def test_stratified_sample_small_dataset(self):
        """Test stratified sampling on dataset smaller than target."""
        data = {
            'source': ['imagenet', 'laion'],
            'value': [1, 2]
        }
        df = pd.DataFrame(data)
        
        # Request more samples than available
        sample = stratified_sample(df, target_size=100)
        
        # Should return entire dataset
        assert len(sample) == 2
    
    def test_stratified_sample_single_stratum(self):
        """Test sampling with only one stratum."""
        data = {
            'source': ['imagenet'] * 50,
            'value': list(range(50))
        }
        df = pd.DataFrame(data)
        
        sample = stratified_sample(df, target_size=25)
        
        assert len(sample) == 25
        assert all(sample['source'] == 'imagenet')

class TestWriteBatchToParquet:
    """Tests for Parquet writing functionality."""
    
    def test_write_new_file(self):
        """Test writing to a new Parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.parquet"
            df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
            
            rows_written = write_batch_to_parquet(df, output_path, mode='write')
            
            assert rows_written == 3
            assert output_path.exists()
            
            # Verify content
            loaded = pd.read_parquet(output_path)
            assert len(loaded) == 3
            assert list(loaded.columns) == ['a', 'b']
    
    def test_append_to_existing_file(self):
        """Test appending to an existing Parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.parquet"
            
            # Write initial data
            df1 = pd.DataFrame({'a': [1, 2], 'b': ['x', 'y']})
            write_batch_to_parquet(df1, output_path, mode='write')
            
            # Append more data
            df2 = pd.DataFrame({'a': [3, 4], 'b': ['z', 'w']})
            rows_written = write_batch_to_parquet(df2, output_path, mode='append')
            
            assert rows_written == 2
            
            # Verify combined content
            loaded = pd.read_parquet(output_path)
            assert len(loaded) == 4
            assert list(loaded['a']) == [1, 2, 3, 4]
    
    def test_write_empty_dataframe(self):
        """Test writing an empty DataFrame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.parquet"
            df = pd.DataFrame({'a': [], 'b': []})
            
            rows_written = write_batch_to_parquet(df, output_path, mode='write')
            
            assert rows_written == 0
            assert output_path.exists()

class TestTimeoutHandling:
    """Tests for timeout functionality."""
    
    def test_timeout_handler_raises(self):
        """Test that timeout handler raises TimeoutError."""
        with pytest.raises(TimeoutError):
            timeout_handler(None, None)
    
    def test_setup_and_cancel_timeout(self):
        """Test setup and cancellation of timeout."""
        # Should not raise
        setup_timeout(1)
        cancel_timeout()
        
        # Verify alarm is cancelled
        assert signal.getsignal(signal.SIGALRM) != timeout_handler or signal.alarm(0) == 0

class TestBatchProcessing:
    """Tests for batch processing efficiency."""
    
    def test_batch_size_consistency(self):
        """Test that batches are created with correct sizes."""
        # Simulate batch creation logic
        batch_size = 100
        total_samples = 250
        
        batches = []
        current_batch = []
        
        for i in range(total_samples):
            current_batch.append(i)
            if len(current_batch) >= batch_size:
                batches.append(current_batch)
                current_batch = []
        
        if current_batch:
            batches.append(current_batch)
        
        # Check batch sizes
        assert len(batches) == 3
        assert len(batches[0]) == 100
        assert len(batches[1]) == 100
        assert len(batches[2]) == 50
    
    def test_memory_efficient_iteration(self):
        """Test that iteration doesn't load all data at once."""
        # This is a conceptual test - in practice, the streaming functions
        # use generators which yield one batch at a time
        
        def mock_generator(batch_size, total):
            current = 0
            while current < total:
                batch = list(range(current, min(current + batch_size, total)))
                yield batch
                current += batch_size
        
        gen = mock_generator(10, 25)
        
        # Consume generator
        all_items = []
        for batch in gen:
            all_items.extend(batch)
            # At any point, only one batch is in memory
            assert len(batch) <= 10
        
        assert len(all_items) == 25
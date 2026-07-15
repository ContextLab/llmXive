"""
Unit tests for data streaming functionality.
"""
import os
import tempfile
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from _data_streaming import (
    load_imagenet_sample,
    load_laion_sample,
    write_samples_to_parquet,
    save_partial_state,
    run_data_streaming,
    MAX_RUNTIME_SECONDS
)

class TestDataStreaming:
    """Test cases for data streaming functions."""
    
    def test_save_partial_state_creates_file(self):
        """Test that partial state is saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            partial_log = os.path.join(tmpdir, "partial_state.json")
            
            # Mock the save function to use our temp directory
            with patch('_data_streaming.PARTIAL_LOG', partial_log):
                save_partial_state(
                    processed_rows=100,
                    source="test_source",
                    start_time=1234567890.0,
                    elapsed=100.0,
                    remaining_time=20000.0
                )
                
                assert os.path.exists(partial_log)
                
                import json
                with open(partial_log, 'r') as f:
                    state = json.load(f)
                
                assert state['processed_rows'] == 100
                assert state['source'] == 'test_source'
                assert state['status'] == 'partial'
                assert 'elapsed_seconds' in state
                assert 'remaining_seconds' in state

    def test_write_samples_to_parquet(self):
        """Test writing samples to parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_samples.parquet")
            
            # Create test DataFrame
            df = pd.DataFrame({
                'id': [1, 2, 3],
                'label': ['cat', 'dog', 'bird'],
                'image': ['img1', 'img2', 'img3']
            })
            
            write_samples_to_parquet(df, output_path, "test")
            
            assert os.path.exists(output_path)
            
            # Read back and verify
            loaded_df = pd.read_parquet(output_path)
            assert len(loaded_df) == 3
            assert list(loaded_df.columns) == ['id', 'label', 'image']

    @patch('_data_streaming.load_dataset')
    def test_load_imagenet_sample_success(self, mock_load_dataset):
        """Test successful loading of ImageNet samples."""
        # Mock dataset
        mock_dataset = MagicMock()
        mock_batch = {
            'id': ['1', '2', '3'],
            'label': [0, 1, 2],
            'image': ['img1', 'img2', 'img3']
        }
        mock_dataset.__iter__ = MagicMock(return_value=iter([mock_batch, mock_batch]))
        mock_load_dataset.return_value = mock_dataset
        
        df = load_imagenet_sample(target_rows=5, batch_size=3)
        
        assert df is not None
        assert len(df) <= 5
        assert 'id' in df.columns
        assert 'label' in df.columns
        assert 'image' in df.columns

    @patch('_data_streaming.load_dataset')
    def test_load_laion_sample_success(self, mock_load_dataset):
        """Test successful loading of LAION samples."""
        # Mock dataset
        mock_dataset = MagicMock()
        mock_batch = {
            'url': ['url1', 'url2'],
            'caption': ['cap1', 'cap2'],
            'image': ['img1', 'img2'],
            'nsfw': [False, False],
            'pwatermark': [False, False]
        }
        mock_dataset.__iter__ = MagicMock(return_value=iter([mock_batch, mock_batch]))
        mock_load_dataset.return_value = mock_dataset
        
        df = load_laion_sample(target_rows=3, batch_size=2)
        
        assert df is not None
        assert len(df) <= 3
        assert 'url' in df.columns
        assert 'caption' in df.columns
        assert 'image' in df.columns

    @patch('_data_streaming.load_dataset')
    def test_load_imagenet_empty_dataset(self, mock_load_dataset):
        """Test handling of empty ImageNet dataset."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset
        
        df = load_imagenet_sample(target_rows=5, batch_size=3)
        
        assert df is None

    def test_timeout_handler(self):
        """Test timeout handler raises TimeoutError."""
        import signal
        
        def handler(signum, frame):
            raise TimeoutError("Test timeout")
        
        original_handler = signal.signal(signal.SIGALRM, handler)
        try:
            signal.alarm(0)  # Cancel any existing alarm
            signal.alarm(1)  # Set alarm for 1 second
            time.sleep(2)  # Should trigger timeout
            pytest.fail("Expected TimeoutError to be raised")
        except TimeoutError:
            pass  # Expected
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, original_handler)

    @patch('_data_streaming.load_imagenet_sample')
    @patch('_data_streaming.load_laion_sample')
    def test_run_data_streaming_success(self, mock_laion, mock_imagenet):
        """Test successful data streaming run."""
        # Mock successful loads
        imagenet_df = pd.DataFrame({'id': [1, 2], 'label': [0, 1], 'image': ['img1', 'img2']})
        laion_df = pd.DataFrame({'url': ['url1', 'url2'], 'caption': ['c1', 'c2'], 
                               'image': ['img1', 'img2'], 'nsfw': [False, False],
                               'pwatermark': [False, False]})
        
        mock_imagenet.return_value = imagenet_df
        mock_laion.return_value = laion_df
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('_data_streaming.OUTPUT_DIR', tmpdir):
                success, message = run_data_streaming()
                
                assert success is True
                assert "completed successfully" in message.lower()

    @patch('_data_streaming.load_imagenet_sample')
    def test_run_data_streaming_imagenet_failure(self, mock_imagenet):
        """Test data streaming fails when ImageNet loading fails."""
        mock_imagenet.return_value = None
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('_data_streaming.OUTPUT_DIR', tmpdir):
                success, message = run_data_streaming()
                
                assert success is False
                assert "failed to load imagenet" in message.lower()

    @patch('_data_streaming.load_laion_sample')
    def test_run_data_streaming_laion_failure(self, mock_laion):
        """Test data streaming fails when LAION loading fails."""
        imagenet_df = pd.DataFrame({'id': [1, 2], 'label': [0, 1], 'image': ['img1', 'img2']})
        
        with patch('_data_streaming.load_imagenet_sample', return_value=imagenet_df):
            mock_laion.return_value = None
            
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch('_data_streaming.OUTPUT_DIR', tmpdir):
                    success, message = run_data_streaming()
                    
                    assert success is False
                    assert "failed to load laion" in message.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

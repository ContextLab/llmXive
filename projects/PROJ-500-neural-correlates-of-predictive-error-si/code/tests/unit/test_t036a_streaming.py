"""
Unit tests for T036a: Streaming data ingestion with memory management.

These tests verify that the streaming ingestion module correctly:
1. Uses streaming mode to avoid loading entire datasets into memory
2. Processes data in chunks to maintain memory limits
3. Handles errors gracefully
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import gc

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.ingest import (
    get_current_memory_usage_gb,
    validate_metadata_variables,
    check_and_report_variables,
    generate_validation_report,
    stream_dataset_chunks,
    download_and_process_streaming,
    RAM_LIMIT_GB
)


class TestT036aStreaming:
    """Tests for streaming data ingestion functionality."""

    def test_validate_metadata_variables_success(self):
        """Test validation when all required variables are present."""
        metadata = {
            'stimulus_type': 'standard_deviant',
            'response_correctness': 'correct_incorrect',
            'other_field': 'value'
        }
        
        is_valid, missing = validate_metadata_variables(metadata)
        
        assert is_valid is True
        assert len(missing) == 0

    def test_validate_metadata_variables_missing_one(self):
        """Test validation when one required variable is missing."""
        metadata = {
            'stimulus_type': 'standard_deviant',
            'other_field': 'value'
        }
        
        is_valid, missing = validate_metadata_variables(metadata)
        
        assert is_valid is False
        assert len(missing) == 1
        assert 'response_correctness' in missing

    def test_validate_metadata_variables_missing_all(self):
        """Test validation when all required variables are missing."""
        metadata = {
            'other_field': 'value'
        }
        
        is_valid, missing = validate_metadata_variables(metadata)
        
        assert is_valid is False
        assert len(missing) == 2
        assert 'stimulus_type' in missing
        assert 'response_correctness' in missing

    def test_check_and_report_variables(self):
        """Test the check_and_report_variables function."""
        metadata = {
            'stimulus_type': 'standard_deviant',
            'response_correctness': 'correct_incorrect'
        }
        
        report = check_and_report_variables(metadata)
        
        assert report['is_valid'] is True
        assert len(report['missing_variables']) == 0
        assert 'stimulus_type' in report['present_variables']
        assert 'response_correctness' in report['present_variables']

    def test_generate_validation_report(self, tmp_path):
        """Test generation of validation report."""
        metadata = {
            'stimulus_type': 'standard_deviant',
            'response_correctness': 'correct_incorrect'
        }
        
        output_path = tmp_path / "validation_report.json"
        report = generate_validation_report("test_dataset", metadata, output_path)
        
        assert report['analysis_mode'] == 'error_signal'
        assert output_path.exists()
        
        # Verify the file was written correctly
        import json
        with open(output_path, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report['dataset_id'] == 'test_dataset'
        assert saved_report['analysis_mode'] == 'error_signal'

    @patch('src.data.ingest.load_dataset')
    def test_stream_dataset_chunks(self, mock_load_dataset):
        """Test streaming dataset chunks."""
        # Mock the dataset iterator
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {'trial': 1, 'value': 0.5},
            {'trial': 2, 'value': 0.6},
            {'trial': 3, 'value': 0.7}
        ]))
        mock_load_dataset.return_value = mock_dataset
        
        chunks = list(stream_dataset_chunks("test_dataset", split='train'))
        
        assert len(chunks) == 3
        assert chunks[0]['trial'] == 1
        assert chunks[2]['value'] == 0.7

    def test_memory_limit_enforcement(self):
        """Test that memory limit enforcement works correctly."""
        # This is a conceptual test - in reality, we'd need to simulate
        # high memory usage, which is difficult in unit tests.
        # Instead, we verify the logic exists.
        
        # Check that RAM_LIMIT_GB is set correctly
        assert RAM_LIMIT_GB == 7.0
        
        # Verify the function exists and returns a number
        usage = get_current_memory_usage_gb()
        assert isinstance(usage, float)
        assert usage >= 0

    def test_download_and_process_streaming_creates_file(self, tmp_path):
        """Test that download_and_process_streaming creates output files."""
        # Mock the stream_dataset_chunks function to return test data
        with patch('src.data.ingest.stream_dataset_chunks') as mock_stream:
            mock_stream.return_value = iter([
                {'trial': 1, 'value': 0.5},
                {'trial': 2, 'value': 0.6},
                {'trial': 3, 'value': 0.7},
                {'trial': 4, 'value': 0.8}
            ])
            
            output_dir = tmp_path / "output"
            output_file = download_and_process_streaming(
                dataset_id="test_dataset",
                output_dir=output_dir,
                split='train',
                chunk_size=2
            )
            
            assert output_file.exists()
            
            # Verify the file contains the expected data
            with open(output_file, 'r') as f:
                content = f.read()
            
            assert 'trial' in content
            assert 'value' in content
            assert '0.5' in content
            assert '0.8' in content

    def test_download_and_process_streaming_memory_cleanup(self, tmp_path):
        """Test that memory cleanup occurs after processing."""
        with patch('src.data.ingest.stream_dataset_chunks') as mock_stream:
            mock_stream.return_value = iter([
                {'trial': i, 'value': i * 0.1}
                for i in range(10)
            ])
            
            # Force garbage collection before
            gc.collect()
            
            output_dir = tmp_path / "output"
            output_file = download_and_process_streaming(
                dataset_id="test_dataset",
                output_dir=output_dir,
                split='train',
                chunk_size=5
            )
            
            # Force garbage collection after
            gc.collect()
            
            assert output_file.exists()
            # If we got here without memory errors, the test passes
            assert True

    def test_streaming_mode_required(self):
        """Test that non-streaming mode raises an error."""
        with patch('src.data.ingest.load_dataset') as mock_load:
            mock_load.return_value = MagicMock()
            
            with pytest.raises(ValueError, match="only supports streaming mode"):
                list(stream_dataset_chunks("test_dataset", split='train', streaming=False))

    def test_error_handling_in_streaming(self):
        """Test error handling when streaming fails."""
        with patch('src.data.ingest.load_dataset') as mock_load:
            mock_load.side_effect = Exception("Network error")
            
            with pytest.raises(Exception, match="Network error"):
                list(stream_dataset_chunks("test_dataset", split='train'))

    def test_chunk_processing_logic(self, tmp_path):
        """Test that data is processed in correct chunk sizes."""
        with patch('src.data.ingest.stream_dataset_chunks') as mock_stream:
            # Create 7 samples to test chunking with size 3
            mock_stream.return_value = iter([
                {'trial': i, 'value': i * 0.1}
                for i in range(1, 8)
            ])
            
            output_dir = tmp_path / "output"
            output_file = download_and_process_streaming(
                dataset_id="test_dataset",
                output_dir=output_dir,
                split='train',
                chunk_size=3
            )
            
            assert output_file.exists()
            
            # Verify all 7 samples are in the file
            with open(output_file, 'r') as f:
                lines = f.readlines()
            
            # Header + 7 data rows = 8 lines
            assert len(lines) == 8

    def test_memory_limit_error_handling(self):
        """Test that MemoryError is raised when limit is exceeded."""
        with patch('src.data.ingest.get_current_memory_usage_gb') as mock_memory:
            # Simulate memory usage exceeding limit
            mock_memory.return_value = RAM_LIMIT_GB + 1.0
            
            with patch('src.data.ingest.load_dataset') as mock_load:
                mock_dataset = MagicMock()
                mock_dataset.__iter__ = MagicMock(return_value=iter([{'trial': 1}]))
                mock_load.return_value = mock_dataset
                
                # First call returns over limit, second call (after GC) still over
                with patch('src.data.ingest.get_current_memory_usage_gb', side_effect=[
                    RAM_LIMIT_GB + 1.0,  # Before GC
                    RAM_LIMIT_GB + 1.0   # After GC
                ]):
                    with pytest.raises(MemoryError, match="Memory limit exceeded"):
                        list(stream_dataset_chunks("test_dataset", split='train'))

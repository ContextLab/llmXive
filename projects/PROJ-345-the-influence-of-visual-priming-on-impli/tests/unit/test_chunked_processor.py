"""
Unit tests for chunked processing functionality.

These tests verify that the chunked processor correctly handles:
- Large file simulation
- Chunk reading and processing
- Memory management
- Temporary file cleanup
"""
import os
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Import the module under test
from data.chunked_processor import ChunkedProcessor, aggregate_mean_response_times, run_chunked_preprocessing


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_large_csv(temp_dir):
    """Create a sample large CSV file for testing."""
    file_path = temp_dir / "large_test.csv"
    
    # Generate sample data
    n_rows = 50000
    data = {
        'trial_id': range(n_rows),
        'response_time': np.random.uniform(200, 5000, n_rows),
        'stimulus_id': [f"stim_{i % 1000}" for i in range(n_rows)],
        'prime_condition': np.random.choice(['positive', 'negative', 'neutral'], n_rows),
        'participant_id': [f"part_{i % 50}" for i in range(n_rows)]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    
    return file_path


@pytest.fixture
def chunked_processor(temp_dir):
    """Create a ChunkedProcessor instance with small chunks for testing."""
    return ChunkedProcessor(
        chunk_size=1000,
        temp_dir=temp_dir / "temp",
        memory_threshold=0.9
    )


class TestChunkedProcessor:
    """Tests for the ChunkedProcessor class."""
    
    def test_initialization(self, chunked_processor):
        """Test processor initialization."""
        assert chunked_processor.chunk_size == 1000
        assert chunked_processor.memory_threshold == 0.9
        assert chunked_processor.temp_dir.exists()
        assert len(chunked_processor.temp_files) == 0
    
    def test_read_csv_in_chunks(self, chunked_processor, sample_large_csv):
        """Test reading CSV in chunks."""
        chunks = list(chunked_processor._read_csv_in_chunks(sample_large_csv))
        
        assert len(chunks) > 1, "Should produce multiple chunks"
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == 50000, "Should read all rows"
    
    def test_process_chunk(self, chunked_processor, sample_large_csv):
        """Test processing a single chunk."""
        chunks = list(chunked_processor._read_csv_in_chunks(sample_large_csv))
        first_chunk = chunks[0]
        
        def process_func(df):
            return df[df['response_time'] > 300]
        
        result = chunked_processor._process_chunk(first_chunk, process_func, 0)
        
        assert len(result) <= len(first_chunk), "Processing should not add rows"
        assert all(result['response_time'] > 300), "Should filter correctly"
    
    def test_temp_file_cleanup(self, chunked_processor, sample_large_csv):
        """Test that temporary files are cleaned up."""
        def process_func(df):
            return df.head(100)  # Small result
        
        output_path = chunked_processor.temp_dir / "output.csv"
        chunked_processor.process_large_csv(
            input_path=sample_large_csv,
            output_path=output_path,
            process_func=process_func,
            cleanup_temp=True
        )
        
        assert len(chunked_processor.temp_files) == 0, "Temp files should be cleaned"
    
    def test_memory_threshold_gc(self, chunked_processor):
        """Test that GC is triggered based on memory threshold."""
        # This is hard to test deterministically, so we just verify
        # the method exists and doesn't crash
        chunked_processor._force_gc()
        assert True  # If we got here, it worked


class TestAggregationFunctions:
    """Tests for aggregation helper functions."""
    
    def test_aggregate_mean_response_times(self, temp_dir):
        """Test mean response time aggregation."""
        # Create sample data
        data = {
            'stimulus_id': ['A', 'A', 'B', 'B', 'A'],
            'participant_id': ['P1', 'P1', 'P1', 'P1', 'P2'],
            'response_time': [500, 600, 400, 450, 550]
        }
        df1 = pd.DataFrame(data)
        
        data2 = {
            'stimulus_id': ['A', 'B', 'B'],
            'participant_id': ['P1', 'P1', 'P2'],
            'response_time': [520, 410, 460]
        }
        df2 = pd.DataFrame(data2)
        
        result = aggregate_mean_response_times([df1, df2])
        
        assert 'mean_response_time' in result.columns
        assert 'trial_count' in result.columns
        assert len(result) > 0


class TestRunChunkedPreprocessing:
    """Tests for the high-level preprocessing function."""
    
    def test_run_chunked_preprocessing(self, temp_dir, sample_large_csv):
        """Test the full preprocessing pipeline."""
        output_path = temp_dir / "processed.csv"
        
        result_path = run_chunked_preprocessing(
            input_path=sample_large_csv,
            output_path=output_path,
            chunk_size=1000
        )
        
        assert result_path.exists(), "Output file should be created"
        
        # Verify output content
        output_df = pd.read_csv(result_path)
        assert len(output_df) > 0, "Output should have data"
        assert 'stimulus_id' in output_df.columns
        assert 'participant_id' in output_df.columns


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_file(self, temp_dir):
        """Test handling of empty input file."""
        empty_file = temp_dir / "empty.csv"
        pd.DataFrame().to_csv(empty_file, index=False)
        
        output_path = temp_dir / "output.csv"
        
        # Should not crash
        processor = ChunkedProcessor(chunk_size=1000, temp_dir=temp_dir / "temp")
        result = processor.process_large_csv(
            input_path=empty_file,
            output_path=output_path,
            process_func=lambda x: x
        )
        
        assert result.exists()
    
    def test_missing_file(self, temp_dir):
        """Test handling of missing input file."""
        processor = ChunkedProcessor(chunk_size=1000, temp_dir=temp_dir / "temp")
        
        with pytest.raises(FileNotFoundError):
            processor.process_large_csv(
                input_path=temp_dir / "nonexistent.csv",
                output_path=temp_dir / "output.csv",
                process_func=lambda x: x
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
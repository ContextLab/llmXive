import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import pyarrow as pa
import pyarrow.parquet as pq

from data_loader import load_stress_curves_streaming, process_stress_curves_in_chunks

@pytest.fixture
def temp_stress_curve_file():
    """Create a temporary stress curve parquet file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file_path = tmpdir / 'stress_curves.parquet'
        
        # Create test data
        data = {
            'clip_id': [f'clip_{i}' for i in range(5000)],
            'distortion_vector_id': [f'vector_{i % 10}' for i in range(5000)],
            'snr': np.random.uniform(-10, 20, 5000),
            'rt60': np.random.uniform(0.1, 1.0, 5000),
            'sss': np.random.uniform(0.0, 1.0, 5000),
            'wer': np.random.uniform(0.0, 1.0, 5000)
        }
        df = pd.DataFrame(data)
        
        # Save to parquet
        df.to_parquet(file_path)
        
        yield file_path

def test_load_stress_curves_streaming(temp_stress_curve_file):
    """Test that stress curves can be loaded in chunks."""
    chunk_size = 1000
    total_rows = 0
    
    chunks = list(load_stress_curves_streaming(temp_stress_curve_file, chunk_size))
    
    assert len(chunks) > 0, "No chunks returned"
    
    for i, chunk in enumerate(chunks):
        assert isinstance(chunk, pd.DataFrame), f"Chunk {i} is not a DataFrame"
        assert len(chunk) <= chunk_size, f"Chunk {i} exceeds chunk size"
        total_rows += len(chunk)
    
    assert total_rows == 5000, f"Expected 5000 rows, got {total_rows}"

def test_process_stress_curves_in_chunks(temp_stress_curve_file):
    """Test that stress curves can be processed in chunks."""
    def dummy_processor(df):
        """Dummy processor that adds a computed column."""
        df['computed'] = df['sss'] * 100
        return df[['clip_id', 'computed']]
    
    config = {
        'derived_path': str(temp_stress_curve_file.parent)
    }
    
    result = process_stress_curves_in_chunks(config, dummy_processor)
    
    assert isinstance(result, pd.DataFrame), "Result is not a DataFrame"
    assert len(result) == 5000, f"Expected 5000 rows, got {len(result)}"
    assert 'computed' in result.columns, "Computed column missing"
    assert all(result['computed'] >= 0) and all(result['computed'] <= 100), "Computed values out of range"

def test_memory_streaming_wrapper_handles_empty_file():
    """Test that empty files are handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        file_path = tmpdir / 'empty.parquet'
        
        # Create empty parquet file
        empty_df = pd.DataFrame(columns=['clip_id', 'sss'])
        empty_df.to_parquet(file_path)
        
        config = {
            'derived_path': str(tmpdir)
        }
        
        result = process_stress_curves_in_chunks(config, lambda df: df)
        
        assert isinstance(result, pd.DataFrame), "Result is not a DataFrame"
        assert len(result) == 0, "Expected empty result"

def test_memory_streaming_wrapper_handles_missing_file():
    """Test that missing files raise appropriate error."""
    config = {
        'derived_path': '/nonexistent/path'
    }
    
    with pytest.raises(FileNotFoundError):
        process_stress_curves_in_chunks(config, lambda df: df)
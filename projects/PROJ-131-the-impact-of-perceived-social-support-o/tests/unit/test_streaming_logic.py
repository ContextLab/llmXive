"""
Unit tests for streaming logic in code/data/ingestion.py.

These tests verify that the chunked processing yields identical statistics
to full-load processing on a sample subset, ensuring correctness of the
streaming implementation for large datasets.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.ingestion import load_cyber_data

def generate_test_data(n_rows=1000, n_cols=10):
    """Generate a synthetic DataFrame for testing."""
    data = {
        f"col_{i}": np.random.randn(n_rows) for i in range(n_cols)
    }
    df = pd.DataFrame(data)
    return df

def test_streaming_vs_full_load_statistics():
    """
    Test that streaming load produces identical statistics to full load.
    """
    # Create a temporary CSV file with test data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        df_test = generate_test_data(n_rows=500, n_cols=5)
        df_test.to_csv(tmp.name, index=False)
        temp_path = Path(tmp.name)

    try:
        # Load full data
        df_full = load_cyber_data(temp_path, streaming=False)
        
        # Load in chunks
        chunks = list(load_cyber_data(temp_path, streaming=True, chunk_size=100))
        df_streamed = pd.concat(chunks, ignore_index=True)
        
        # Verify shapes match
        assert df_full.shape == df_streamed.shape, "Shapes do not match"
        
        # Verify statistics match (mean, std)
        for col in df_full.columns:
            assert np.isclose(df_full[col].mean(), df_streamed[col].mean()), f"Mean mismatch for {col}"
            assert np.isclose(df_full[col].std(), df_streamed[col].std()), f"Std mismatch for {col}"
            
        print("Streaming logic test passed: Statistics match between full and chunked load.")
        
    finally:
        # Cleanup
        if temp_path.exists():
            os.remove(temp_path)

def test_streaming_iterator_behavior():
    """
    Test that the streaming function returns an iterator.
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        df_test = generate_test_data(n_rows=200, n_cols=3)
        df_test.to_csv(tmp.name, index=False)
        temp_path = Path(tmp.name)

    try:
        result = load_cyber_data(temp_path, streaming=True, chunk_size=50)
        
        # Check if it's an iterator/generator
        assert hasattr(result, '__iter__'), "Result should be an iterator"
        
        # Consume and check length
        chunks = list(result)
        assert len(chunks) > 0, "Should have at least one chunk"
        total_rows = sum(len(c) for c in chunks)
        assert total_rows == 200, "Total rows in chunks should match original"
        
        print("Streaming iterator test passed.")
        
    finally:
        if temp_path.exists():
            os.remove(temp_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
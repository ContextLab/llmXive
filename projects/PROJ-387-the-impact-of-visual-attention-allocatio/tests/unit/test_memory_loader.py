"""
Unit tests for memory loader utilities.
"""
import os
import sys
import tempfile
import pandas as pd
import pytest

# Add project root to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis.memory_loader import get_available_ram_gb, load_data_chunked, load_data_streaming

def test_get_available_ram_gb():
    """Test that RAM estimation returns a positive float."""
    ram = get_available_ram_gb()
    assert isinstance(ram, float)
    assert ram > 0

def test_load_data_chunked():
    """Test chunked loading of a CSV file."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("id,value\n")
        for i in range(100):
            f.write(f"{i},{i*2}\n")
        temp_path = f.name

    try:
        chunks = list(load_data_chunked(temp_path, chunk_size=10))
        assert len(chunks) == 10
        assert all(isinstance(chunk, pd.DataFrame) for chunk in chunks)
        total_rows = sum(len(c) for c in chunks)
        assert total_rows == 100
    finally:
        os.unlink(temp_path)

def test_load_data_streaming_small():
    """Test streaming load for a file that fits in memory."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("id,value\n")
        for i in range(50):
            f.write(f"{i},{i*2}\n")
        temp_path = f.name

    try:
        df = load_data_streaming(temp_path, target_ram_gb=1.0)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 50
    finally:
        os.unlink(temp_path)

def test_load_data_streaming_missing_file():
    """Test that streaming load raises error for missing file."""
    with pytest.raises(FileNotFoundError):
        load_data_streaming("/nonexistent/path/file.csv")
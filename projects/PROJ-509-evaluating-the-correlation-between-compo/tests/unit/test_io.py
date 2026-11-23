import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.io import get_memory_usage_gb, should_use_chunked_reading, read_csv_chunked


def test_get_memory_usage_gb():
    """Test memory usage calculation."""
    mem = get_memory_usage_gb()
    assert mem > 0
    assert isinstance(mem, float)


def test_should_use_chunked_reading():
    """Test chunked reading decision."""
    # This should return a boolean
    result = should_use_chunked_reading(threshold_gb=1000.0)
    assert isinstance(result, bool)


def test_read_csv_chunked(tmp_path):
    """Test chunked CSV reading."""
    # Create a test CSV
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"a": range(100), "b": range(100, 200)})
    df.to_csv(csv_path, index=False)

    chunks = list(read_csv_chunked(csv_path, chunk_size=10))
    assert len(chunks) == 10
    assert all(len(c) == 10 for c in chunks)

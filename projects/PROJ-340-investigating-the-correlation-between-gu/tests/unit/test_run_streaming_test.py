"""
Unit tests for T064: run_streaming_test.py
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from run_streaming_test import run_streaming_execution_test, get_memory_peak_gb

@pytest.fixture
def temp_large_proxy():
    """Create a temporary large proxy CSV file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        csv_path = tmpdir_path / "large_proxy.csv"

        # Generate a synthetic large dataset (simulating T070 output)
        # N=10000 rows to ensure chunking happens
        n_rows = 10000
        data = {
            "subject_id": [f"sub_{i}" for i in range(n_rows)],
            "taxa_1": np.random.normal(0, 1, n_rows),
            "taxa_2": np.random.normal(0, 1, n_rows),
            "sleep_duration": np.random.normal(7, 1, n_rows),
            "age": np.random.randint(20, 80, n_rows)
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        yield str(csv_path)

def test_streaming_creates_output(temp_large_proxy):
    """Verify that the streaming test creates the filtered parquet file."""
    # Run test with a small chunk size to force multiple chunks
    report = run_streaming_execution_test(
        proxy_path=temp_large_proxy,
        chunk_size=100, # Force 100 chunks
        max_memory_gb=7.0
    )

    assert report["status"] == "PASSED"
    assert report["chunks_processed"] > 1
    assert report["output_file"] is not None
    assert os.path.exists(report["output_file"])

    # Verify the parquet file is readable
    df = pd.read_parquet(report["output_file"])
    assert "subject_id" in df.columns
    assert len(df) > 0

def test_streaming_memory_check(temp_large_proxy):
    """Verify that memory reporting works."""
    report = run_streaming_execution_test(
        proxy_path=temp_large_proxy,
        chunk_size=1000,
        max_memory_gb=7.0
    )

    assert report["memory_peak_gb"] >= 0.0
    assert report["memory_peak_gb"] < 7.0 # Should pass with small test data

def test_streaming_fails_on_memory_limit(temp_large_proxy):
    """Verify that the test fails if memory limit is set too low."""
    # Set an impossibly low limit
    report = run_streaming_execution_test(
        proxy_path=temp_large_proxy,
        chunk_size=1000,
        max_memory_gb=0.001 # 1MB
    )

    assert report["status"] == "FAILED"
    assert "Memory limit exceeded" in report["error"]
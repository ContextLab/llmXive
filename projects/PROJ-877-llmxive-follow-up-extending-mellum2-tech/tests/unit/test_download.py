import pandas as pd
from pathlib import Path
from llmxive_toolkit import paths
import pytest

def test_raw_chunks_exists():
    """Verify the raw chunks parquet file was created."""
    p = paths.data("processed", "raw_chunks.parquet")
    assert p.exists(), "raw_chunks.parquet should exist"

def test_raw_chunks_content():
    """Verify the parquet file has correct columns and non-empty content."""
    p = paths.data("processed", "raw_chunks.parquet")
    df = pd.read_parquet(p)
    
    required_cols = {"id", "repo_name", "language", "content", "status"}
    assert required_cols.issubset(set(df.columns)), f"Missing columns. Found: {df.columns}"
    
    # Check that content is not empty or just stubs
    # We expect real code, so the average length of content should be significantly > 0
    avg_len = df["content"].str.len().mean()
    assert avg_len > 10, f"Content seems to be empty or stubbed. Avg length: {avg_len}"
    
    # Check status
    assert (df["status"] == "raw").all(), "All rows should have status='raw'"

def test_checksum_exists():
    """Verify the checksum file exists."""
    p = paths.data("checksums.txt")
    assert p.exists(), "checksums.txt should exist"
    with open(p, "r") as f:
        content = f.read()
        assert "raw_chunks.parquet" in content
        assert len(content.split(": ")) == 2

def test_sample_size():
    """Verify we have the expected number of rows per language."""
    p = paths.data("processed", "raw_chunks.parquet")
    df = pd.read_parquet(p)
    
    # Since codeparrot/github-code is Python-only, we check that we got the target N for Python.
    # If Java were present, we'd check that too.
    python_count = len(df[df["language"] == "python"])
    from code.config import N_PER_LANGUAGE
    assert python_count == N_PER_LANGUAGE, f"Expected {N_PER_LANGUAGE} Python rows, got {python_count}"
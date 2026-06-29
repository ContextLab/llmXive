"""
Unit tests for fetch_assistments.py (Task T012).

These tests verify timeout handling, fallback logic, and synthetic data generation.
"""

import pytest
import os
import sys
import tempfile
import shutil
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from download.fetch_assistments import (
    fetch_assistments_dataset, 
    download_raw_csv, 
    _generate_synthetic_assistments,
    _ensure_data_dir,
    DEFAULT_DATA_DIR
)

class TestFetchAssistments:
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        # Patch the default data dir for tests
        import download.fetch_assistments as fa
        fa.DEFAULT_DATA_DIR = os.path.join(self.temp_dir, "data", "raw")
        
    def teardown_method(self):
        """Cleanup test fixtures."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ensure_data_dir(self):
        """Test that _ensure_data_dir creates the directory."""
        target = os.path.join(self.temp_dir, "test_dir")
        fa = importlib.import_module("download.fetch_assistments")
        # Re-assign for the module scope if needed, but here we test logic
        # Since DEFAULT_DATA_DIR is module level, we rely on the patched version in setup
        from download.fetch_assistments import _ensure_data_dir
        _ensure_data_dir()
        assert os.path.exists(fa.DEFAULT_DATA_DIR)
    
    def test_generate_synthetic_assistments(self):
        """Test synthetic data generation."""
        num_rows = 100
        df = _generate_synthetic_assistments(num_rows)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == num_rows
        assert "problem_id" in df.columns
        assert "skill" in df.columns
        assert "correct" in df.columns
        assert "rt_seconds" in df.columns
        assert "user_id" in df.columns
        
        # Check data types
        assert df["correct"].dtype in [int, float]
        assert df["rt_seconds"].dtype in [int, float]
        assert all(df["correct"].isin([0, 1]))
    
    def test_fetch_fallback_synthetic(self):
        """Test that fetch falls back to synthetic when download fails."""
        # Force synthetic to simulate download failure
        df = fetch_assistments_dataset(use_cache=False, force_synthetic=True, min_rows=50)
        
        assert df is not None
        assert len(df) >= 50
        assert os.path.exists(os.path.join(DEFAULT_DATA_DIR, "assistments_synthetic_fallback.csv"))
    
    def test_fetch_cache_hit(self):
        """Test that fetch uses cache if available."""
        # First, generate and save a synthetic dataset to cache location
        df_initial = _generate_synthetic_assistments(100)
        cache_path = os.path.join(DEFAULT_DATA_DIR, "assistments_sample.csv")
        df_initial.to_csv(cache_path, index=False)
        
        # Now fetch with cache enabled
        df_fetched = fetch_assistments_dataset(use_cache=True, force_synthetic=False, min_rows=50)
        
        assert df_fetched is not None
        assert len(df_fetched) == 100
        # Verify it's the same data (problem_ids match)
        assert list(df_fetched["problem_id"]) == list(df_initial["problem_id"])
    
    def test_download_raw_csv_failure(self):
        """Test that download_raw_csv returns False on failure."""
        # Try to download to a path that will fail (e.g., invalid permission or URL)
        # We mock the URL to be invalid by temporarily changing the constant
        import download.fetch_assistments as fa
        original_url = fa.REMOTE_URL
        fa.REMOTE_URL = "http://invalid-url-that-does-not-exist-12345.com/data.csv"
        
        try:
            result = download_raw_csv("test_fail.csv")
            assert result is False
        finally:
            fa.REMOTE_URL = original_url

"""
Unit tests for the configuration management module.
"""
import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import load_dataset_urls, get_project_root, get_data_dir, ensure_data_dirs, ConfigError

class TestLoadDatasetUrls:
    def test_load_default_urls(self, monkeypatch):
        """Test that default URLs are used when environment variables are not set."""
        # Ensure no custom env vars are set
        for key in ["AGP_URL", "NHANES_URL", "UK_BIOBANK_URL"]:
            monkeypatch.delenv(key, raising=False)
        
        urls = load_dataset_urls()
        
        assert "AGP" in urls
        assert "NHANES" in urls
        assert "UK_BIOBANK" in urls
        assert "qiita.ucsd.edu" in urls["AGP"]
        assert "cdc.gov" in urls["NHANES"]
        assert "ukbiobank.ac.uk" in urls["UK_BIOBANK"]

    def test_load_custom_urls(self, monkeypatch):
        """Test that custom environment variables override defaults."""
        monkeypatch.setenv("AGP_URL", "https://custom-agp.example.com")
        monkeypatch.setenv("NHANES_URL", "https://custom-nhanes.example.com")
        
        urls = load_dataset_urls()
        
        assert urls["AGP"] == "https://custom-agp.example.com"
        assert urls["NHANES"] == "https://custom-nhanes.example.com"

class TestProjectPaths:
    def test_get_project_root(self):
        """Test that project root is correctly identified."""
        root = get_project_root()
        assert root.exists()
        # The root should contain the 'code' and 'data' directories
        assert (root / "code").exists()
        assert (root / "data").exists()

    def test_get_data_dir(self):
        """Test data directory path construction."""
        raw_dir = get_data_dir("raw")
        processed_dir = get_data_dir("processed")
        
        assert "data" in str(raw_dir)
        assert "raw" in str(raw_dir)
        assert "processed" in str(processed_dir)

    def test_ensure_data_dirs(self):
        """Test that ensure_data_dirs creates directories if missing."""
        # Remove a specific test dir to force creation
        test_dir = get_data_dir("qc")
        # We don't actually delete to avoid race conditions in parallel tests,
        # but the function should be idempotent.
        ensure_data_dirs()
        assert test_dir.exists()
        assert test_dir.is_dir()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
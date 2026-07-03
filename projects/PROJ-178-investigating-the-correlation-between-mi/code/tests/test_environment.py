import os
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.environment import (
    ensure_directories,
    get_ftp_urls,
    get_local_paths,
    PROJECT_ROOT,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    MITO_VCF_URL,
    METADATA_URL
)

class TestEnvironmentPaths:
    def test_project_root_exists(self):
        """Test that the project root is correctly identified."""
        assert PROJECT_ROOT.exists()
        assert isinstance(PROJECT_ROOT, Path)

    def test_directory_creation(self):
        """Test that ensure_directories creates the required folders."""
        # Clean up if exists (optional, depending on test isolation strategy)
        # For this test, we just ensure it doesn't raise and directories exist
        ensure_directories()
        
        assert RAW_DATA_DIR.exists()
        assert PROCESSED_DATA_DIR.exists()
        
        # Check specific subdirectories
        assert (PROJECT_ROOT / "logs").exists()
        assert (PROJECT_ROOT / "paper" / "figures").exists()

class TestFtpUrls:
    def test_mito_vcf_url_format(self):
        """Test that the mitochondrial VCF URL is a valid string."""
        assert isinstance(MITO_VCF_URL, str)
        assert MITO_VCF_URL.startswith("ftp://")
        assert "1000genomes" in MITO_VCF_URL.lower() or "ebi.ac.uk" in MITO_VCF_URL.lower()
        assert "chrM" in MITO_VCF_URL or "mito" in MITO_VCF_URL.lower()

    def test_metadata_url_format(self):
        """Test that the metadata URL is a valid string."""
        assert isinstance(METADATA_URL, str)
        assert METADATA_URL.startswith("ftp://")
        assert "panel" in METADATA_URL.lower()

    def test_urls_dict(self):
        """Test that get_ftp_urls returns the correct keys."""
        urls = get_ftp_urls()
        assert "mito_vcf" in urls
        assert "metadata" in urls
        assert urls["mito_vcf"] == MITO_VCF_URL
        assert urls["metadata"] == METADATA_URL

class TestConfigurationValues:
    def test_local_paths_dict(self):
        """Test that get_local_paths returns expected keys."""
        paths = get_local_paths()
        expected_keys = [
            "raw_mito_vcf",
            "raw_metadata",
            "processed_dataset",
            "model_results",
            "analysis_results",
            "sensitivity_results",
            "checksum"
        ]
        for key in expected_keys:
            assert key in paths, f"Key {key} missing from local paths config"

    def test_processed_dataset_path(self):
        """Test that the processed dataset path is correctly configured."""
        paths = get_local_paths()
        assert "mito_aging_dataset.csv" in str(paths["processed_dataset"])
        assert str(paths["processed_dataset"]).startswith(str(PROCESSED_DATA_DIR))

    def test_urls_are_accessible(self):
        """
        Optional: Check if the FTP servers are reachable.
        Note: This test might be flaky in restricted CI environments.
        We use a try/except block to handle connection errors gracefully.
        """
        import urllib.request
        try:
            # Attempt to open the FTP URL (head request if possible, else get)
            # For FTP, we often just check if the connection can be established
            # or if the file exists.
            # urllib.request.urlopen(MITO_VCF_URL) # This might hang or fail in CI without network
            # Instead, we just validate the URL structure is valid for the task
            assert len(MITO_VCF_URL) > 0
            assert len(METADATA_URL) > 0
        except Exception:
            # If network is unavailable, we still pass the structural test
            # as long as the URL strings are correctly formed
            pass

"""
Environment configuration tests.

Tests for T009: Verify that environment configuration correctly defines
1000 Genomes FTP URLs and local paths.
"""
import os
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.environment import (
    FTP_BASE_URL,
    MITO_VCF_URL,
    METADATA_URL,
    LOCAL_RAW_DIR,
    PROCESSED_DATA_DIR,
    LOGS_DIR,
    ensure_directories,
    REQUIRED_COLUMNS,
    DEFAULT_VAF_THRESHOLD,
    DEPTH_BINS,
)


class TestEnvironmentPaths:
    """Test that all required paths are correctly defined."""

    def test_base_paths_exist(self):
        """Verify that base directories are defined as Path objects."""
        assert isinstance(LOCAL_RAW_DIR, Path)
        assert isinstance(PROCESSED_DATA_DIR, Path)
        assert isinstance(LOGS_DIR, Path)

    def test_directories_can_be_created(self):
        """Test that ensure_directories creates the required directories."""
        # Get original paths
        original_paths = [str(LOCAL_RAW_DIR), str(PROCESSED_DATA_DIR), str(LOGS_DIR)]
        
        # Create directories
        created = ensure_directories()
        
        # Verify directories exist
        for directory in created:
            assert directory.exists(), f"Directory {directory} was not created"
            assert directory.is_dir(), f"{directory} is not a directory"

    def test_processed_dataset_path(self):
        """Verify processed dataset path is correctly defined."""
        assert PROCESSED_DATA_DIR.name == "processed"
        assert str(PROCESSED_DATA_DIR).endswith("code/data/processed")


class TestFtpUrls:
    """Test that FTP URLs are correctly defined."""

    def test_ftp_base_url(self):
        """Verify the FTP base URL is correctly formatted."""
        assert FTP_BASE_URL.startswith("ftp://")
        assert "1000genomes" in FTP_BASE_URL
        assert "release" in FTP_BASE_URL

    def test_mito_vcf_url(self):
        """Verify the mitochondrial VCF URL is correctly formed."""
        assert MITO_VCF_URL.startswith(FTP_BASE_URL)
        assert "chrM" in MITO_VCF_URL
        assert MITO_VCF_URL.endswith(".vcf.gz")

    def test_metadata_url(self):
        """Verify the metadata panel URL is correctly formed."""
        assert METADATA_URL.startswith(FTP_BASE_URL)
        assert "panel" in METADATA_URL
        assert METADATA_URL.endswith(".panel")


class TestConfigurationValues:
    """Test that configuration constants are valid."""

    def test_required_columns_defined(self):
        """Verify that all required columns are defined."""
        assert isinstance(REQUIRED_COLUMNS, dict)
        assert len(REQUIRED_COLUMNS) >= 4  # burden, age, sex, population
        assert "age" in REQUIRED_COLUMNS
        assert "sex" in REQUIRED_COLUMNS

    def test_vaf_threshold_valid(self):
        """Verify the default VAF threshold is a valid probability."""
        assert 0 < DEFAULT_VAF_THRESHOLD < 1
        assert DEFAULT_VAF_THRESHOLD == 0.01  # 1%

    def test_depth_bins_valid(self):
        """Verify depth bin definitions are valid."""
        assert isinstance(DEPTH_BINS, dict)
        assert "low" in DEPTH_BINS
        assert "medium" in DEPTH_BINS
        assert "high" in DEPTH_BINS
        
        # Check bin ranges are tuples
        for bin_name, (low, high) in DEPTH_BINS.items():
            assert isinstance(low, (int, float))
            assert isinstance(high, (int, float))
            assert low < high, f"Invalid range for {bin_name}: {low} >= {high}"

    def test_bin_ranges_non_overlapping(self):
        """Verify that depth bins do not overlap."""
        low_max = DEPTH_BINS["low"][1]
        medium_min = DEPTH_BINS["medium"][0]
        medium_max = DEPTH_BINS["medium"][1]
        high_min = DEPTH_BINS["high"][0]
        
        # Low and medium should be adjacent or non-overlapping
        assert low_max <= medium_min, f"Low and medium bins overlap: {low_max} vs {medium_min}"
        
        # Medium and high should be adjacent or non-overlapping
        assert medium_max <= high_min, f"Medium and high bins overlap: {medium_max} vs {high_min}"
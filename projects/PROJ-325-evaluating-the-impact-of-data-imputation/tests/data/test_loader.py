"""
Tests for code/data/loader.py
"""

import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from code.data.loader import (
    check_design_columns,
    detect_missingness,
    DataFetchError,
    MissingDesignColumnsError,
    ensure_directories
)


class TestDesignColumnChecks:
    """Tests for design column validation logic."""

    def test_all_design_columns_present(self):
        """Test when all required design columns are present."""
        df = pd.DataFrame({
            'weight': [1.0, 2.0, 3.0],
            'psu': [1, 2, 3],
            'strata': [1, 1, 2],
            'value': [10, 20, 30]
        })
        
        all_present, missing = check_design_columns(df, ['weight', 'psu', 'strata'])
        
        assert all_present is True
        assert len(missing) == 0

    def test_missing_psu_column(self):
        """Test detection of missing PSU column."""
        df = pd.DataFrame({
            'weight': [1.0, 2.0, 3.0],
            'strata': [1, 1, 2],
            'value': [10, 20, 30]
        })
        
        all_present, missing = check_design_columns(df, ['weight', 'psu', 'strata'])
        
        assert all_present is False
        assert 'psu' in missing

    def test_missing_strata_column(self):
        """Test detection of missing strata column."""
        df = pd.DataFrame({
            'weight': [1.0, 2.0, 3.0],
            'psu': [1, 2, 3],
            'value': [10, 20, 30]
        })
        
        all_present, missing = check_design_columns(df, ['weight', 'psu', 'strata'])
        
        assert all_present is False
        assert 'strata' in missing


class TestMissingnessDetection:
    """Tests for missingness detection logic."""

    def test_low_missingness(self):
        """Test detection when missingness is below threshold."""
        df = pd.DataFrame({
            'value': [1.0, 2.0, 3.0, 4.0, 5.0]  # 0% missing
        })
        
        has_high_missingness = detect_missingness(df, 'value', threshold=0.1)
        
        assert has_high_missingness is False

    def test_high_missingness(self):
        """Test detection when missingness is above threshold."""
        df = pd.DataFrame({
            'value': [1.0, None, None, 4.0, None]  # 60% missing
        })
        
        has_high_missingness = detect_missingness(df, 'value', threshold=0.1)
        
        assert has_high_missingness is True

    def test_exactly_threshold_missingness(self):
        """Test detection at exactly the threshold."""
        # 10% missing (1 out of 10)
        df = pd.DataFrame({
            'value': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, None]
        })
        
        has_high_missingness = detect_missingness(df, 'value', threshold=0.1)
        
        # Should be False since it's exactly at threshold, not above
        assert has_high_missingness is False

    def test_nonexistent_column(self):
        """Test detection for non-existent column."""
        df = pd.DataFrame({
            'value': [1.0, 2.0, 3.0]
        })
        
        has_high_missingness = detect_missingness(df, 'nonexistent', threshold=0.1)
        
        assert has_high_missingness is False


class TestDirectoryCreation:
    """Tests for directory creation."""

    def test_ensure_directories_creates_folders(self, tmp_path):
        """Test that ensure_directories creates required folders."""
        # Change to temp directory for testing
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            ensure_directories()
            
            # Check that directories were created
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "raw" / "cache").exists()
            assert (tmp_path / "data" / "processed").exists()
            assert (tmp_path / "state").exists()
        finally:
            os.chdir(original_cwd)
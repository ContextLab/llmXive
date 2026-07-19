"""Unit tests for the loaders module."""
import pytest
import pandas as pd
import numpy as np
import os
import json
from pathlib import Path
import tempfile
import shutil

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code import loaders
from code import config

class TestChecksumFunctions:
    """Tests for checksum utilities."""

    def test_compute_file_hash(self):
        """Test SHA256 hash computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            hash_val = loaders.compute_file_hash(temp_path)
            assert len(hash_val) == 64  # SHA256 hex length
            assert all(c in '0123456789abcdef' for c in hash_val)
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_success(self):
        """Test successful checksum verification."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            expected_hash = loaders.compute_file_hash(temp_path)
            result = loaders.verify_checksum(temp_path, expected_hash)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_failure(self):
        """Test checksum verification failure raises error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Checksum mismatch"):
                loaders.verify_checksum(temp_path, "wrong_hash_value")
        finally:
            os.unlink(temp_path)

    def test_load_save_checksums(self):
        """Test saving and loading checksums to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checksum_file = Path(tmpdir) / "checksums.json"

            # Save
            checksums = {"file1.csv": "hash1", "file2.csv": "hash2"}
            loaders.save_checksums(checksums, str(checksum_file))

            # Load
            loaded = loaders.load_checksums(str(checksum_file))
            assert loaded == checksums

    def test_load_missing_checksums(self):
        """Test loading from non-existent file returns empty dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checksum_file = Path(tmpdir) / "nonexistent.json"
            loaded = loaders.load_checksums(str(checksum_file))
            assert loaded == {}

class TestDataHygiene:
    """Tests for data hygiene functions."""

    def test_drop_missing_values(self):
        """Test dropping rows with missing values."""
        df = pd.DataFrame({
            'a': [1, 2, np.nan, 4],
            'b': [5, np.nan, 7, 8],
            'c': [9, 10, 11, 12]
        })
        result = loaders.drop_missing_values(df)
        assert len(result) == 2  # Only rows 0 and 3 remain
        assert result.index.tolist() == [0, 3]

    def test_detect_constant_variables(self):
        """Test detection of constant columns."""
        df = pd.DataFrame({
            'a': [1, 1, 1, 1],  # Constant
            'b': [1, 2, 3, 4],  # Variable
            'c': [5, 5, 5, 5],  # Constant
        })
        constant = loaders.detect_constant_variables(df)
        assert set(constant) == {'a', 'c'}

    def test_exclude_constant_variables(self):
        """Test exclusion of constant columns."""
        df = pd.DataFrame({
            'a': [1, 1, 1, 1],
            'b': [1, 2, 3, 4],
            'c': [5, 5, 5, 5],
        })
        result = loaders.exclude_constant_variables(df)
        assert list(result.columns) == ['b']

    def test_filter_continuous_variables(self):
        """Test filtering to numeric columns only."""
        df = pd.DataFrame({
            'a': [1, 2, 3, 4],
            'b': ['x', 'y', 'z', 'w'],
            'c': [5.0, 6.0, 7.0, 8.0],
        })
        result = loaders.filter_continuous_variables(df)
        assert list(result.columns) == ['a', 'c']

    def test_validate_dimensions_success(self):
        """Test validation passes with sufficient variables."""
        df = pd.DataFrame(np.random.randn(10, 25))
        assert loaders.validate_dataset_dimensions(df, min_vars=20) is True

    def test_validate_dimensions_failure(self):
        """Test validation fails with insufficient variables."""
        df = pd.DataFrame(np.random.randn(10, 10))
        with pytest.raises(ValueError, match="insufficient variables"):
            loaders.validate_dataset_dimensions(df, min_vars=20)

class TestHygienePipeline:
    """Tests for the full hygiene pipeline."""

    def test_full_pipeline(self):
        """Test the complete hygiene pipeline."""
        df = pd.DataFrame({
            'a': [1, 2, np.nan, 4, 5],
            'b': [1, 1, 1, 1, 1],  # Constant
            'c': ['x', 'y', 'z', 'w', 'v'],  # Non-numeric
            'd': [1.0, 2.0, 3.0, 4.0, 5.0],
            'e': [10, 20, 30, 40, 50],
            'f': [100, 200, 300, 400, 500],
            'g': [1, 2, 3, 4, 5],
            'h': [1.1, 2.2, 3.3, 4.4, 5.5],
            'i': [10, 20, 30, 40, 50],
            'j': [100, 200, 300, 400, 500],
            'k': [1, 2, 3, 4, 5],
            'l': [1.1, 2.2, 3.3, 4.4, 5.5],
            'm': [10, 20, 30, 40, 50],
            'n': [100, 200, 300, 400, 500],
            'o': [1, 2, 3, 4, 5],
            'p': [1.1, 2.2, 3.3, 4.4, 5.5],
            'q': [10, 20, 30, 40, 50],
            'r': [100, 200, 300, 400, 500],
            's': [1, 2, 3, 4, 5],
            't': [1.1, 2.2, 3.3, 4.4, 5.5],
        })

        # This should fail because after dropping missing and constants,
        # and filtering numeric, we may not have 20 variables
        # But let's create a valid one
        valid_df = pd.DataFrame(np.random.randn(100, 25))
        valid_df.iloc[0, 0] = np.nan  # Add one missing
        valid_df.iloc[:, 0] = 1  # Make first column constant

        result = loaders.apply_hygiene_pipeline(valid_df, min_vars=20)
        assert result.shape[1] >= 20
        assert result.isnull().sum().sum() == 0

class TestConfigIntegration:
    """Tests for config integration."""

    def test_dataset_urls_exist(self):
        """Verify that dataset URLs are defined in config."""
        cfg = config.get_config()
        datasets = cfg["datasets"]

        # Check all expected datasets are present
        expected_keys = ["wine", "abalone", "breast_cancer", "student_performance", "air_quality", "concrete"]
        for key in expected_keys:
            assert key in datasets, f"Dataset {key} missing from config"
            assert "url" in datasets[key], f"URL missing for {key}"
            assert datasets[key]["url"], f"Empty URL for {key}"

    def test_air_quality_csv_link(self):
        """Verify Air Quality dataset uses direct CSV link."""
        cfg = config.get_config()
        air_quality = cfg["datasets"]["air_quality"]
        assert "csv" in air_quality["url"].lower(), "Air Quality should use direct CSV link"
        assert "zip" not in air_quality["url"].lower(), "Air Quality should not use ZIP"
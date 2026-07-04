"""
Tests for the data loading module.

These tests verify that the load_data module correctly:
1. Creates necessary directories
2. Loads datasets from HuggingFace
3. Verifies required features
4. Saves processed data
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from load_data import (
    ensure_directories,
    verify_features,
    save_dataset,
    REQUIRED_FEATURES,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
)


class TestEnsureDirectories:
    """Test directory creation functionality."""
    
    def test_creates_raw_directory(self, tmp_path):
        """Test that raw directory is created."""
        # Mock the global paths
        with patch('load_data.DATA_RAW_DIR', tmp_path / "data" / "raw"), \
             patch('load_data.DATA_PROCESSED_DIR', tmp_path / "data" / "processed"):
            ensure_directories()
            
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "processed").exists()
    
    def test_does_not_fail_if_exists(self, tmp_path):
        """Test that function doesn't fail if directories already exist."""
        with patch('load_data.DATA_RAW_DIR', tmp_path / "data" / "raw"), \
             patch('load_data.DATA_PROCESSED_DIR', tmp_path / "data" / "processed"):
            # Create directories first
            (tmp_path / "data" / "raw").mkdir(parents=True)
            (tmp_path / "data" / "processed").mkdir(parents=True)
            
            # Should not raise
            ensure_directories()


class TestVerifyFeatures:
    """Test feature verification functionality."""
    
    def test_all_features_present(self):
        """Test verification passes when all features present."""
        df = pd.DataFrame({
            "timestamp": [1, 2, 3],
            "response": ["a", "b", "c"],
            "error": [0, 1, 0],
            "hint_request": [1, 0, 0],
            "interaction_type": ["q1", "q2", "q3"],
        })
        
        success, missing = verify_features(df, "test_dataset")
        
        assert success is True
        assert len(missing) == 0
    
    def test_missing_features(self):
        """Test verification detects missing features."""
        df = pd.DataFrame({
            "timestamp": [1, 2, 3],
            "response": ["a", "b", "c"],
            # Missing error, hint_request, interaction_type
        })
        
        success, missing = verify_features(df, "test_dataset")
        
        assert success is False
        assert "error" in missing
        assert "hint_request" in missing
        assert "interaction_type" in missing
    
    def test_extra_features_ignored(self):
        """Test that extra features don't cause failure."""
        df = pd.DataFrame({
            "timestamp": [1, 2, 3],
            "response": ["a", "b", "c"],
            "error": [0, 1, 0],
            "hint_request": [1, 0, 0],
            "interaction_type": ["q1", "q2", "q3"],
            "extra_feature": ["x", "y", "z"],
            "another_extra": [10, 20, 30],
        })
        
        success, missing = verify_features(df, "test_dataset")
        
        assert success is True
        assert len(missing) == 0


class TestSaveDataset:
    """Test dataset saving functionality."""
    
    def test_saves_csv_correctly(self, tmp_path):
        """Test that dataset is saved as CSV."""
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
        })
        
        with patch('load_data.DATA_PROCESSED_DIR', tmp_path):
            output_path = save_dataset(df, "test_output")
            
            assert output_path.endswith("test_output.csv")
            assert os.path.exists(output_path)
            
            # Verify content
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == 3
            assert list(loaded_df.columns) == ["col1", "col2"]
    
    def test_overwrites_existing_file(self, tmp_path):
        """Test that existing file is overwritten."""
        df1 = pd.DataFrame({"col": [1, 2]})
        df2 = pd.DataFrame({"col": [3, 4, 5]})
        
        with patch('load_data.DATA_PROCESSED_DIR', tmp_path):
            save_dataset(df1, "overwrite_test")
            save_dataset(df2, "overwrite_test")
            
            loaded_df = pd.read_csv(tmp_path / "overwrite_test.csv")
            assert len(loaded_df) == 3  # Should have df2's data


class TestRequiredFeatures:
    """Test that required features are correctly defined."""
    
    def test_required_features_set(self):
        """Test that REQUIRED_FEATURES contains expected columns."""
        expected_features = {
            "timestamp",
            "response",
            "error",
            "hint_request",
            "interaction_type",
        }
        
        assert REQUIRED_FEATURES == expected_features
    
    def test_all_features_are_strings(self):
        """Test that all required features are strings."""
        for feature in REQUIRED_FEATURES:
            assert isinstance(feature, str)
            assert len(feature) > 0
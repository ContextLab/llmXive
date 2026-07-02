"""
Unit tests for code/config.py
"""
import pytest
import json
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import (
    dataset_config, 
    DATASET_IDS_PRIMARY, 
    WINDOW_SIZES, 
    TR_DEFAULT,
    DatasetConfig,
    get_data_path,
    get_derived_path,
    ensure_dirs
)

class TestDatasetConfig:
    """Tests for the DatasetConfig class and fallback logic."""

    def test_initial_ids_match_primary(self):
        """Verify that the default config starts with primary dataset IDs."""
        # Create a fresh instance to avoid state pollution from global
        fresh_config = DatasetConfig()
        assert fresh_config.current_ids == DATASET_IDS_PRIMARY

    def test_register_validation_failure_removes_id(self):
        """Test that registering a failure removes the ID from the active list."""
        test_config = DatasetConfig(initial_ids=["ds000030", "ds000208"])
        initial_count = len(test_config.current_ids)
        
        test_config.register_validation_failure(
            "ds000030", 
            "ERR_DATA_MISSING", 
            "Missing 'musical_genre'"
        )
        
        assert "ds000030" not in test_config.current_ids
        assert len(test_config.current_ids) == initial_count - 1

    def test_fallback_switches_to_verified_dataset(self):
        """Test that if primary fails, the system switches to a fallback."""
        # Force a scenario where primary fails and we need a fallback
        test_config = DatasetConfig(initial_ids=["ds000030"])
        
        # Mock the failure of the only primary dataset
        test_config.register_validation_failure(
            "ds000030",
            "ERR_DATA_MISSING",
            "Missing 'musical_genre'"
        )
        
        # The config should have switched to a fallback (e.g., ds000117)
        assert len(test_config.current_ids) > 0
        assert "ds000030" not in test_config.current_ids
        # Verify the new ID is in the verified list
        from config import VERIFIED_DATASETS
        assert test_config.current_ids[0] in VERIFIED_DATASETS

    def test_to_json_serializes_correctly(self):
        """Test JSON serialization of config state."""
        test_config = DatasetConfig()
        json_str = test_config.to_json()
        data = json.loads(json_str)
        
        assert "current_ids" in data
        assert "errors" in data
        assert "fallbacks_available" in data

class TestHyperparameters:
    """Tests for global hyperparameter constants."""

    def test_window_sizes_defined(self):
        assert isinstance(WINDOW_SIZES, list)
        assert all(isinstance(w, int) for w in WINDOW_SIZES)
        assert len(WINDOW_SIZES) > 0

    def test_tr_default_valid(self):
        assert isinstance(TR_DEFAULT, float)
        assert TR_DEFAULT > 0

class TestPathHelpers:
    """Tests for path generation functions."""

    def test_ensure_dirs_creates_structure(self):
        """Verify that ensure_dirs creates the required directories."""
        # We test this by checking if the function runs without error
        # and that the main data directory exists afterwards.
        from config import DATA_DIR
        ensure_dirs()
        assert DATA_DIR.exists()

    def test_get_data_path_returns_pathlib(self):
        path = get_data_path("test_subdir")
        assert isinstance(path, Path)
        assert "data" in str(path)

    def test_get_derived_path_returns_pathlib(self):
        path = get_derived_path("results.json")
        assert isinstance(path, Path)
        assert "derived" in str(path)

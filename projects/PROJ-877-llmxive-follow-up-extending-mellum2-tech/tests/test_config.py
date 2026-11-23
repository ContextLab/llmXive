"""
Tests for the config module.
"""
import pytest
from pathlib import Path
import os
import tempfile

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import get_project_root, get_config, set_seed, validate_required_env_vars

class TestGetProjectRoot:
    """Test cases for get_project_root function."""
    
    def test_returns_path_object(self):
        """Test that the function returns a Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        
    def test_returns_existing_directory(self):
        """Test that the returned path exists."""
        root = get_project_root()
        assert root.exists()

class TestGetConfig:
    """Test cases for get_config function."""
    
    def test_returns_dict(self):
        """Test that the function returns a dictionary."""
        config = get_config()
        assert isinstance(config, dict)
        
    def test_contains_expected_keys(self):
        """Test that the config contains expected keys."""
        config = get_config()
        expected_keys = [
            "project_root",
            "hf_token",
            "hf_dataset_name",
            "max_workers",
            "timeout_seconds",
            "seed",
            "batch_size",
            "device"
        ]
        for key in expected_keys:
            assert key in config, f"Missing key: {key}"

class TestSetSeed:
    """Test cases for set_seed function."""
    
    def test_sets_seed_without_error(self):
        """Test that set_seed runs without error."""
        set_seed(42)
        # If we get here, it succeeded
        
    def test_sets_different_seed(self):
        """Test that we can set a different seed."""
        set_seed(123)
        # Just verifying no error

class TestValidateRequiredEnvVars:
    """Test cases for validate_required_env_vars function."""
    
    def test_passes_with_empty_list(self):
        """Test that an empty list passes validation."""
        assert validate_required_env_vars([]) is True
        
    def test_fails_with_missing_vars(self):
        """Test that missing variables cause an error."""
        # Create a variable that definitely doesn't exist
        with pytest.raises(ValueError):
            validate_required_env_vars(["NON_EXISTENT_VAR_XYZ"])
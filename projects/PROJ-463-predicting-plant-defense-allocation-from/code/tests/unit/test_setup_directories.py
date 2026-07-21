import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.setup_directories import setup_data_directories
from src.utils.config import Config, reset_config, get_config


class TestDirectorySetup:
    """Unit tests for directory setup functionality."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """Set up a temporary config directory for each test."""
        # Create a temporary directory for testing
        self.test_data_root = tmp_path / "test_data"
        self.test_data_root.mkdir()
        
        # Create a temporary config file
        config_file = tmp_path / "config.json"
        config_data = {
            "data_path": str(self.test_data_root),
            "seed": 42,
            "thresholds": {
                "cv_reduction": 0.2,
                "replicates_min": 2
            },
            "housekeeping_genes": [
                "ACT", "ACT7", "GAPDH", "UBQ10", "EF1a", "TUB6", "TUB1",
                "PP2A", "SAND"
            ],
            "trait_synthesis_genes": [
                "CYP79D16", "CYP79D15", "CYP79D17", "CYP83A1", "CYP83B1"
            ]
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        # Initialize config with our test config
        reset_config()
        config = get_config()
        config.config_file = str(config_file)
        config.data_path = str(self.test_data_root)
        
        yield
        
        # Cleanup happens automatically with tmp_path

    def test_setup_creates_required_directories(self):
        """Test that setup_data_directories creates all required directories."""
        # Ensure directories don't exist yet
        for dir_name in ["raw", "processed", "traits", "manifests", "synthetic"]:
            dir_path = self.test_data_root / dir_name
            assert not dir_path.exists(), f"Directory {dir_path} should not exist before setup"
        
        # Run the setup
        setup_data_directories()
        
        # Verify all directories were created
        for dir_name in ["raw", "processed", "traits", "manifests", "synthetic"]:
            dir_path = self.test_data_root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} should exist after setup"
            assert dir_path.is_dir(), f"{dir_path} should be a directory"

    def test_setup_idempotent(self):
        """Test that running setup multiple times doesn't cause errors."""
        # Run setup twice
        setup_data_directories()
        setup_data_directories()
        
        # Verify all directories still exist
        for dir_name in ["raw", "processed", "traits", "manifests", "synthetic"]:
            dir_path = self.test_data_root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} should exist after multiple setups"

    def test_setup_with_existing_directories(self):
        """Test that setup handles pre-existing directories correctly."""
        # Create one directory manually
        existing_dir = self.test_data_root / "raw"
        existing_dir.mkdir()
        
        # Run setup
        setup_data_directories()
        
        # Verify the existing directory still exists and is a directory
        assert existing_dir.exists()
        assert existing_dir.is_dir()
        
        # Verify other directories were created
        for dir_name in ["processed", "traits", "manifests", "synthetic"]:
            dir_path = self.test_data_root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} should be created"

    def test_setup_creates_nested_directories(self):
        """Test that setup creates parent directories if needed."""
        # Remove the base data path to test parent creation
        # Note: This is a bit tricky since the config points to test_data_root
        # We'll test by creating a config that points to a nested path
        
        nested_path = self.test_data_root / "nested" / "data"
        config = get_config()
        config.data_path = str(nested_path)
        
        # Run setup - should create parent directories
        setup_data_directories()
        
        # Verify the full path exists
        assert nested_path.exists()
        assert nested_path.is_dir()
        
        # Verify subdirectories exist
        for dir_name in ["raw", "processed", "traits", "manifests", "synthetic"]:
            dir_path = nested_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} should exist"

    def test_setup_fails_on_permission_error(self):
        """Test that setup raises appropriate error on permission issues."""
        # Create a read-only directory to simulate permission error
        readonly_dir = self.test_data_root / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        config = get_config()
        config.data_path = str(readonly_dir)
        
        # Attempt to setup - should raise an error
        with pytest.raises(RuntimeError):
            setup_data_directories()
        
        # Cleanup
        readonly_dir.chmod(0o755)  # Make writable for cleanup
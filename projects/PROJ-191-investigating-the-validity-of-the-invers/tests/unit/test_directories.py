"""
Unit tests for directory management utilities.

Tests ensure that directory creation is robust, idempotent, and handles
edge cases correctly.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.directories import ensure_data_directories, REQUIRED_DATA_DIRS, ADDITIONAL_DIRS

class TestEnsureDataDirectories:
    """Tests for the ensure_data_directories function."""
    
    def test_creates_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        result = ensure_data_directories(tmp_path)
        
        # Check all required dirs exist
        for rel_dir in REQUIRED_DATA_DIRS:
            expected_path = tmp_path / rel_dir
            assert expected_path.exists(), f"Directory {rel_dir} was not created"
            assert expected_path.is_dir(), f"{rel_dir} exists but is not a directory"
        
        # Check returned list contains the paths
        assert len(result) >= len(REQUIRED_DATA_DIRS)
        
    def test_creates_additional_directories(self, tmp_path):
        """Verify that additional directories are created when provided."""
        additional = ["data/processed/bootstrap_resamples", "data/results/figures"]
        result = ensure_data_directories(tmp_path, additional_dirs=additional)
        
        for rel_dir in additional:
            expected_path = tmp_path / rel_dir
            assert expected_path.exists(), f"Additional directory {rel_dir} was not created"
        
    def test_idempotent(self, tmp_path):
        """Verify that calling the function multiple times is safe."""
        # First call
        first_result = ensure_data_directories(tmp_path)
        
        # Second call - should not raise errors
        second_result = ensure_data_directories(tmp_path)
        
        # Both should have same directories
        first_paths = set(str(p) for p in first_result)
        second_paths = set(str(p) for p in second_result)
        assert first_paths == second_paths
        
    def test_creates_nested_parents(self, tmp_path):
        """Verify that parent directories are created if they don't exist."""
        # Start with empty tmp_path, no subdirs exist
        result = ensure_data_directories(tmp_path)
        
        # Verify deep nested directory exists
        deep_dir = tmp_path / "data" / "processed"
        assert deep_dir.exists()
        
    def test_handles_existing_directories(self, tmp_path):
        """Verify that existing directories don't cause errors."""
        # Pre-create some directories
        (tmp_path / "data" / "raw").mkdir(parents=True)
        
        # Should not raise
        result = ensure_data_directories(tmp_path)
        
        # Directory should still exist
        assert (tmp_path / "data" / "raw").exists()
        
    def test_returns_path_objects(self, tmp_path):
        """Verify that the function returns Path objects, not strings."""
        result = ensure_data_directories(tmp_path)
        
        for p in result:
            assert isinstance(p, Path), f"Expected Path object, got {type(p)}"
            
    def test_uses_relative_paths(self, tmp_path):
        """Verify that directories are created relative to project root."""
        result = ensure_data_directories(tmp_path)
        
        for p in result:
            # All paths should be under tmp_path
            assert str(p).startswith(str(tmp_path)), \
                f"Path {p} is not under project root {tmp_path}"
                
    def test_empty_project_root(self, tmp_path):
        """Test with a fresh, empty project root."""
        # tmp_path is guaranteed to be empty initially
        result = ensure_data_directories(tmp_path)
        
        # Should create all required directories
        assert len(result) > 0
        for rel_dir in REQUIRED_DATA_DIRS:
            assert (tmp_path / rel_dir).exists()

class TestRequiredDirsConstant:
    """Tests for the REQUIRED_DATA_DIRS constant."""
    
    def test_contains_raw(self):
        """Verify 'data/raw' is in required dirs."""
        assert "data/raw" in REQUIRED_DATA_DIRS
        
    def test_contains_processed(self):
        """Verify 'data/processed' is in required dirs."""
        assert "data/processed" in REQUIRED_DATA_DIRS
        
    def test_contains_results(self):
        """Verify 'data/results' is in required dirs."""
        assert "data/results" in REQUIRED_DATA_DIRS

class TestAdditionalDirsConstant:
    """Tests for the ADDITIONAL_DIRS constant."""
    
    def test_contains_bootstrap_resamples(self):
        """Verify bootstrap resamples dir is in additional dirs."""
        assert "data/processed/bootstrap_resamples" in ADDITIONAL_DIRS
        
    def test_contains_figures(self):
        """Verify figures dir is in additional dirs."""
        assert "data/results/figures" in ADDITIONAL_DIRS

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
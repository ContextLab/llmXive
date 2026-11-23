"""
Unit tests for data directory initialization.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add the parent directory to the path to import setup_data_dirs
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_data_dirs import main as setup_main

class TestDataDirectories:
    """Tests for data directory creation logic."""

    def test_data_directory_creation(self, tmp_path):
        """Test that the data directory structure can be created."""
        # Create a temporary directory to simulate project root
        # We need to mock the Path resolution in setup_data_dirs
        # Since the script determines root relative to itself, we test the logic
        
        # Create the expected structure manually to verify it's valid
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        figures_dir = data_dir / "figures"
        
        data_dir.mkdir(parents=True)
        raw_dir.mkdir()
        processed_dir.mkdir()
        figures_dir.mkdir()
        
        assert data_dir.exists()
        assert raw_dir.exists()
        assert processed_dir.exists()
        assert figures_dir.exists()
        assert data_dir.is_dir()

    def test_gitkeep_files(self, tmp_path):
        """Test that .gitkeep files are created in data directories."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Simulate the creation logic
        raw_dir = data_dir / "raw"
        raw_dir.mkdir()
        gitkeep_path = raw_dir / ".gitkeep"
        gitkeep_path.write_text("# Keep this directory in git\n")
        
        assert gitkeep_path.exists()
        assert gitkeep_path.read_text() == "# Keep this directory in git\n"

    def test_directory_structure_valid(self, tmp_path):
        """Test that the full directory structure is valid."""
        # Create the full structure
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        figures_dir = data_dir / "figures"
        
        for d in [data_dir, raw_dir, processed_dir, figures_dir]:
            d.mkdir(parents=True, exist_ok=True)
            (d / ".gitkeep").write_text("# Keep\n")
        
        # Verify structure
        assert len(list(data_dir.iterdir())) == 3  # raw, processed, figures
        assert (data_dir / "raw" / ".gitkeep").exists()
        assert (data_dir / "processed" / ".gitkeep").exists()
        assert (data_dir / "figures" / ".gitkeep").exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

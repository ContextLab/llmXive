import os
import pytest
from pathlib import Path

from utils.setup_data_dirs import create_project_structure


class TestDataStructureIntegration:
    """Integration test to verify the actual data directory structure is created."""

    def test_full_structure_created(self):
        """Run the setup function and verify all required directories exist."""
        # This test runs the actual function in the project context.
        # It relies on T001a having created the base 'data' directory.
        # If T001a is not run, this might create it too, which is fine.
        
        created_paths = create_project_structure()
        
        assert len(created_paths) == 3
        
        for path_str in created_paths:
            path = Path(path_str)
            assert path.exists(), f"Created path {path} does not exist"
            assert path.is_dir(), f"Created path {path} is not a directory"
        
        # Verify specific names
        base = Path(created_paths[0]).parent
        assert (base / "raw").exists()
        assert (base / "processed").exists()
        assert (base / "aggregated").exists()
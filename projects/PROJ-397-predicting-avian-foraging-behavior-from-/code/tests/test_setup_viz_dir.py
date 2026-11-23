"""
Unit tests for the viz directory initialization (T001c).

Verifies that the viz directory and .gitkeep file are created correctly.
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from utils.config import get_project_root, get_viz_dir
from setup_viz_dir import main

class TestSetupVizDir(unittest.TestCase):
    """Test cases for the viz directory initialization."""

    def test_viz_directory_exists(self):
        """Verify that the viz directory exists after initialization."""
        viz_dir = get_viz_dir()
        self.assertTrue(os.path.isdir(viz_dir), 
                        f"Viz directory should exist at {viz_dir}")

    def test_gitkeep_file_exists(self):
        """Verify that the .gitkeep file exists in the viz directory."""
        viz_dir = get_viz_dir()
        gitkeep_path = os.path.join(viz_dir, '.gitkeep')
        self.assertTrue(os.path.isfile(gitkeep_path),
                        f".gitkeep file should exist at {gitkeep_path}")

    def test_gitkeep_file_not_empty(self):
        """Verify that the .gitkeep file has content."""
        viz_dir = get_viz_dir()
        gitkeep_path = os.path.join(viz_dir, '.gitkeep')
        with open(gitkeep_path, 'r') as f:
            content = f.read()
        self.assertGreater(len(content), 0,
                           ".gitkeep file should not be empty")

    def test_main_function_returns_zero(self):
        """Verify that the main function returns 0 on success."""
        result = main()
        self.assertEqual(result, 0, "main() should return 0 on success")

if __name__ == '__main__':
    unittest.main()
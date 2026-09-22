"""
Unit tests to verify the existence and structure of required data directories.
This test ensures T004 has been correctly implemented.
"""
import os
import unittest
from pathlib import Path

class TestDirectoryStructure(unittest.TestCase):
    """Tests for the data directory structure created in T004."""

    @classmethod
    def setUpClass(cls):
        """Set up the base path for the project."""
        # Assuming tests run from project root or parent of 'data'
        cls.project_root = Path(__file__).resolve().parent.parent.parent
        cls.data_root = cls.project_root / "data"

    def test_raw_directory_exists(self):
        """Verify data/raw/ directory exists."""
        raw_dir = self.data_root / "raw"
        self.assertTrue(raw_dir.exists(), f"Directory {raw_dir} does not exist.")
        self.assertTrue(raw_dir.is_dir(), f"{raw_dir} is not a directory.")

    def test_raw_gitkeep_exists(self):
        """Verify data/raw/.gitkeep exists."""
        gitkeep = self.data_root / "raw" / ".gitkeep"
        self.assertTrue(gitkeep.exists(), f"File {gitkeep} does not exist.")
        self.assertTrue(gitkeep.is_file(), f"{gitkeep} is not a file.")

    def test_intermediate_directory_exists(self):
        """Verify data/intermediate/ directory exists."""
        intermediate_dir = self.data_root / "intermediate"
        self.assertTrue(intermediate_dir.exists(), f"Directory {intermediate_dir} does not exist.")
        self.assertTrue(intermediate_dir.is_dir(), f"{intermediate_dir} is not a directory.")

    def test_intermediate_gitkeep_exists(self):
        """Verify data/intermediate/.gitkeep exists."""
        gitkeep = self.data_root / "intermediate" / ".gitkeep"
        self.assertTrue(gitkeep.exists(), f"File {gitkeep} does not exist.")
        self.assertTrue(gitkeep.is_file(), f"{gitkeep} is not a file.")

    def test_results_directory_exists(self):
        """Verify data/results/ directory exists."""
        results_dir = self.data_root / "results"
        self.assertTrue(results_dir.exists(), f"Directory {results_dir} does not exist.")
        self.assertTrue(results_dir.is_dir(), f"{results_dir} is not a directory.")

    def test_results_gitkeep_exists(self):
        """Verify data/results/.gitkeep exists."""
        gitkeep = self.data_root / "results" / ".gitkeep"
        self.assertTrue(gitkeep.exists(), f"File {gitkeep} does not exist.")
        self.assertTrue(gitkeep.is_file(), f"{gitkeep} is not a file.")

    def test_directories_are_tracked_by_git(self):
        """
        Verify that .gitkeep files are present, implying intent to track.
        (Actual git tracking verification requires a git repo context).
        """
        gitkeeps = [
            self.data_root / "raw" / ".gitkeep",
            self.data_root / "intermediate" / ".gitkeep",
            self.data_root / "results" / ".gitkeep"
        ]
        for gp in gitkeeps:
            self.assertTrue(gp.exists(), f"Missing .gitkeep at {gp} to enable Git tracking.")

if __name__ == '__main__':
    unittest.main()
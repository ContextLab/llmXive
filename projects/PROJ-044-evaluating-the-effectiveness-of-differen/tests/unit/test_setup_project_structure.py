"""
Tests for the project structure setup script.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
# We need to adjust the import path if running from tests/
# Assuming the test runner adds the parent directory to sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project_structure import create_directories, generate_tree_output


class TestProjectSetup:
    def test_create_directories(self, tmp_path):
        """Test that create_directories creates the expected folders."""
        expected_dirs = [
            "code/data",
            "code/training",
            "code/analysis",
            "code/models",
            "tests/unit",
            "tests/integration",
            "data/raw",
            "data/partitions",
            "results",
            "artifacts",
        ]

        create_directories(tmp_path)

        for dir_path in expected_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"

    def test_generate_tree_output(self, tmp_path):
        """Test that generate_tree_output creates the tree file."""
        # Create some dummy structure first
        (tmp_path / "code").mkdir()
        (tmp_path / "code" / "data").mkdir()
        
        output_file = tmp_path / "tree_output.txt"
        generate_tree_output(tmp_path, output_file)

        assert output_file.exists(), "tree_output.txt was not created"
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        assert "code" in content, "Tree output does not contain 'code'"
        assert "data" in content, "Tree output does not contain 'data'"
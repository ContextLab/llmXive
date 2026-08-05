"""
Unit tests for the project structure setup script.
"""
import os
import tempfile
from pathlib import Path
import pytest
from code.setup_project_structure import create_directories, generate_tree_output

class TestCreateDirectories:
    def test_creates_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        required_dirs = [
            "code/data", "code/training", "code/analysis", "code/models",
            "tests/unit", "tests/integration", "data/raw", "data/partitions",
            "results", "artifacts"
        ]
        
        create_directories(tmp_path)
        
        for dir_name in required_dirs:
            full_path = tmp_path / dir_name
            assert full_path.exists(), f"Directory {dir_name} was not created"
            assert full_path.is_dir(), f"{dir_name} is not a directory"

    def test_idempotent_creation(self, tmp_path):
        """Test that running create_directories twice does not cause errors."""
        create_directories(tmp_path)
        # Run again - should not raise
        create_directories(tmp_path)
        
        # Verify directories still exist
        assert (tmp_path / "code/data").exists()

class TestGenerateTreeOutput:
    def test_generates_tree_file(self, tmp_path):
        """Test that tree output file is generated."""
        # Create a dummy directory structure first
        (tmp_path / "code" / "data").mkdir(parents=True)
        
        output_file = tmp_path / "tree_output.txt"
        generate_tree_output(tmp_path, output_file)
        
        assert output_file.exists(), "Tree output file was not created"
        assert output_file.stat().st_size > 0, "Tree output file is empty"
        
        content = output_file.read_text()
        assert "code" in content, "Tree output does not contain expected directory name"

    def test_tree_output_content(self, tmp_path):
        """Test that tree output contains expected content."""
        (tmp_path / "results").mkdir()
        (tmp_path / "artifacts").mkdir()
        
        output_file = tmp_path / "tree_output.txt"
        generate_tree_output(tmp_path, output_file)
        
        content = output_file.read_text()
        # Check for at least one directory name in the output
        assert any(name in content for name in ["code", "data", "tests", "results", "artifacts"]), \
            "Tree output does not contain expected directory names"
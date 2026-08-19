import os
import tempfile
from pathlib import Path
import pytest
import shutil

# Import the functions to test
from setup_project_structure import create_directories, generate_tree_output

def test_create_directories():
    """Test that create_directories creates the expected folder hierarchy."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # Call the function
        create_directories(base_path)
        
        # Define expected directories
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
            "artifacts"
        ]
        
        # Verify each directory exists
        for dir_path in expected_dirs:
            full_path = base_path / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

def test_generate_tree_output():
    """Test that generate_tree_output creates the verification file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        output_file = base_path / "tree_output.txt"
        
        # Create a dummy directory structure first
        (base_path / "test_dir").mkdir()
        
        # Call the function
        generate_tree_output(base_path, output_file)
        
        # Verify the file exists and has content
        assert output_file.exists(), "Tree output file was not created"
        assert output_file.stat().st_size > 0, "Tree output file is empty"
        
        # Verify content contains the base path
        content = output_file.read_text()
        assert str(base_path) in content or "test_dir" in content, \
            "Tree output does not contain expected directory information"

def test_full_workflow():
    """Test the full workflow of creating directories and generating tree output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        output_file = base_path / "tree_output.txt"
        
        # Create directories
        create_directories(base_path)
        
        # Generate tree output
        generate_tree_output(base_path, output_file)
        
        # Verify both operations succeeded
        assert output_file.exists()
        assert (base_path / "code" / "data").exists()
        assert (base_path / "results").exists()
        assert (base_path / "artifacts").exists()
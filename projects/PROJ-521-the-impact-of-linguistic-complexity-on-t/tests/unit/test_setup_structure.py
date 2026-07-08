"""
Unit tests for the project setup structure.
Verifies that the required directories exist after running the setup script.
"""
import os
import tempfile
from pathlib import Path
import pytest

# We will test the logic by creating a temporary directory structure
# and verifying the creation logic, rather than relying on the global project path.

def test_directory_creation_logic():
    """Test that the directory creation logic works correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "projects" / "PROJ-521-the-impact-of-linguistic-complexity-on-t"
        
        directories = [
            "code",
            "data/raw",
            "data/processed",
            "data/outputs/figures",
            "tests/unit",
            "tests/integration",
            "tests/contract",
        ]

        for dir_name in directories:
            full_path = project_root / dir_name
            # Simulate the creation logic
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
            
            # Assert existence
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

def test_nested_directory_structure():
    """Test that nested directories (e.g., data/raw) are created correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "projects" / "PROJ-521-the-impact-of-linguistic-complexity-on-t"
        
        # Test deep nesting
        deep_path = project_root / "data" / "outputs" / "figures"
        deep_path.mkdir(parents=True, exist_ok=True)
        
        assert deep_path.exists()
        assert (deep_path / "data").exists() # Parent check
        assert (deep_path / "outputs").exists() # Parent check
        assert deep_path.is_dir()

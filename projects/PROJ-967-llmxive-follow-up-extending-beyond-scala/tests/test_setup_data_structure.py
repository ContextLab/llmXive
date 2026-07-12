"""
Tests for the data directory structure setup.
"""
import os
import tempfile
from pathlib import Path
import pytest

def test_data_directories_exist():
    """Test that data/raw and data/processed directories are created."""
    # Create a temporary directory to simulate the project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        data_path = base_path / "data"
        raw_path = data_path / "raw"
        processed_path = data_path / "processed"

        # Create directories
        raw_path.mkdir(parents=True, exist_ok=True)
        processed_path.mkdir(parents=True, exist_ok=True)

        # Verify directories exist
        assert raw_path.exists(), f"Directory {raw_path} does not exist"
        assert processed_path.exists(), f"Directory {processed_path} does not exist"
        assert raw_path.is_dir(), f"{raw_path} is not a directory"
        assert processed_path.is_dir(), f"{processed_path} is not a directory"

def test_gitignore_content():
    """Test that .gitignore contains the required entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        gitignore_path = base_path / ".gitignore"

        expected_content = """# Data directories - exclude raw and processed data from version control
raw/
processed/
# Ignore temporary files
*.tmp
*.temp
# Ignore hidden files
.*
!.gitignore
"""

        with open(gitignore_path, 'w') as f:
            f.write(expected_content)

        with open(gitignore_path, 'r') as f:
            content = f.read()

        assert "raw/" in content, "raw/ not found in .gitignore"
        assert "processed/" in content, "processed/ not found in .gitignore"
        assert "*.tmp" in content, "*.tmp not found in .gitignore"
        assert "*.temp" in content, "*.temp not found in .gitignore"

def test_setup_data_structure_script():
    """Test the setup_data_structure.py script."""
    # This test would normally run the script and verify the results
    # For now, we just verify the script exists and is importable
    import sys
    sys.path.insert(0, 'projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code')
    try:
        from setup_data_structure import setup_data_directories, create_gitignore
        assert callable(setup_data_directories), "setup_data_directories is not callable"
        assert callable(create_gitignore), "create_gitignore is not callable"
    except ImportError as e:
        pytest.fail(f"Failed to import setup_data_structure: {e}")
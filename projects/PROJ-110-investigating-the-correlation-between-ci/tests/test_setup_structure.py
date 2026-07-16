import os
from pathlib import Path
import pytest
import tempfile
import shutil

from setup_structure import create_directories


def test_create_directories_creates_required_folders():
    """Test that create_directories creates data/raw, data/processed, and contracts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = create_directories()
            
            # Verify directories exist
            assert (Path(temp_dir) / "data" / "raw").exists()
            assert (Path(temp_dir) / "data" / "processed").exists()
            assert (Path(temp_dir) / "contracts").exists()
            
            # Verify .gitkeep files exist
            assert (Path(temp_dir) / "data" / "raw" / ".gitkeep").exists()
            assert (Path(temp_dir) / "data" / "processed" / ".gitkeep").exists()
            assert (Path(temp_dir) / "contracts" / ".gitkeep").exists()
            
            # Verify return value is the project root
            assert result == Path(temp_dir)
        finally:
            os.chdir(original_cwd)


def test_create_directories_idempotent():
    """Test that running create_directories multiple times doesn't fail."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            # Run twice
            create_directories()
            create_directories()
            
            # Verify directories still exist
            assert (Path(temp_dir) / "data" / "raw").exists()
            assert (Path(temp_dir) / "data" / "processed").exists()
            assert (Path(temp_dir) / "contracts").exists()
        finally:
            os.chdir(original_cwd)


def test_create_directories_with_nested_path():
    """Test that create_directories creates nested directories if they don't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Ensure parent directories don't exist
            shutil.rmtree(Path(temp_dir) / "data", ignore_errors=True)
            shutil.rmtree(Path(temp_dir) / "contracts", ignore_errors=True)
            
            create_directories()
            
            # Verify directories were created
            assert (Path(temp_dir) / "data" / "raw").exists()
            assert (Path(temp_dir) / "data" / "processed").exists()
            assert (Path(temp_dir) / "contracts").exists()
        finally:
            os.chdir(original_cwd)
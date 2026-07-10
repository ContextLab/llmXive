"""
Unit tests for directory structure management.
"""
import os
import tempfile
from pathlib import Path

import pytest

from code.data.structure import (
    create_directory_structure,
    validate_directory_structure,
    get_data_paths,
)


def test_create_directory_structure():
    """Test that all required directories are created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        created = create_directory_structure(tmpdir)

        # Check that all expected directories were created
        root = Path(tmpdir)
        for dir_name in ["data/raw", "data/processed", "data/validation"]:
            assert (root / dir_name).is_dir()

        # Check .gitkeep files exist
        assert (root / "data/raw/.gitkeep").exists()
        assert (root / "data/processed/.gitkeep").exists()
        assert (root / "data/validation/.gitkeep").exists()


def test_validate_directory_structure():
    """Test validation of existing directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initially should fail
        assert validate_directory_structure(tmpdir) is False

        # Create structure
        create_directory_structure(tmpdir)

        # Now should pass
        assert validate_directory_structure(tmpdir) is True


def test_get_data_paths():
    """Test retrieval of data directory paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        create_directory_structure(tmpdir)

        paths = get_data_paths(tmpdir)

        assert "raw" in paths
        assert "processed" in paths
        assert "validation" in paths

        assert paths["raw"].is_dir()
        assert paths["processed"].is_dir()
        assert paths["validation"].is_dir()
import os
import tempfile
from pathlib import Path

import pytest

from config import get_path
from ensure_docs_dir import ensure_docs_directory


class TestEnsureDocsDirectory:
    """Tests for the ensure_docs_directory function."""

    def test_creates_docs_directory(self, tmp_path):
        """Verify that the function creates the docs directory if it doesn't exist."""
        # Mock get_path to return our temp directory
        original_get_path = get_path
        import ensure_docs_dir
        ensure_docs_dir.get_path = lambda: tmp_path

        try:
            docs_dir = tmp_path / "docs"
            assert not docs_dir.exists()

            result = ensure_docs_directory()

            assert result is True
            assert docs_dir.exists()
            assert docs_dir.is_dir()
        finally:
            # Restore original function
            ensure_docs_dir.get_path = original_get_path

    def test_verifies_existing_docs_directory(self, tmp_path):
        """Verify that the function returns True if the docs directory already exists."""
        original_get_path = get_path
        import ensure_docs_dir
        ensure_docs_dir.get_path = lambda: tmp_path

        try:
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()

            result = ensure_docs_directory()

            assert result is True
            assert docs_dir.exists()
        finally:
            ensure_docs_dir.get_path = original_get_path

    def test_raises_on_unwritable_directory(self, tmp_path):
        """Verify that the function raises an error if the directory cannot be written to."""
        original_get_path = get_path
        import ensure_docs_dir
        ensure_docs_dir.get_path = lambda: tmp_path

        try:
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            # Make directory read-only
            os.chmod(docs_dir, 0o444)

            with pytest.raises(RuntimeError, match="not writable"):
                ensure_docs_directory()
        finally:
            # Restore permissions and function
            os.chmod(docs_dir, 0o755)
            ensure_docs_dir.get_path = original_get_path

    def test_raises_on_non_directory_path(self, tmp_path):
        """Verify that the function raises an error if a file exists at the docs path."""
        original_get_path = get_path
        import ensure_docs_dir
        ensure_docs_dir.get_path = lambda: tmp_path

        try:
            docs_file = tmp_path / "docs"
            docs_file.touch()

            with pytest.raises(RuntimeError, match="not a directory"):
                ensure_docs_directory()
        finally:
            ensure_docs_dir.get_path = original_get_path
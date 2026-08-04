import os
import tempfile
import shutil
import pytest
from code.setup_data_dirs import ensure_gitkeep

class TestEnsureGitkeep:
    def test_creates_directory_and_gitkeep(self, tmp_path):
        """Test that ensure_gitkeep creates the directory and .gitkeep file."""
        target_dir = tmp_path / "new_subdir"
        assert not target_dir.exists()

        result = ensure_gitkeep(str(target_dir))

        assert result is True
        assert target_dir.exists()
        assert (target_dir / ".gitkeep").exists()

    def test_skips_existing_gitkeep(self, tmp_path):
        """Test that ensure_gitkeep does not overwrite existing .gitkeep."""
        target_dir = tmp_path / "existing_subdir"
        target_dir.mkdir()
        gitkeep_file = target_dir / ".gitkeep"
        gitkeep_file.write_text("original content")

        result = ensure_gitkeep(str(target_dir))

        assert result is True
        assert gitkeep_file.read_text() == "original content"

    def test_handles_nested_paths(self, tmp_path):
        """Test that ensure_gitkeep handles nested directory paths."""
        target_dir = tmp_path / "level1" / "level2" / "level3"
        assert not target_dir.exists()

        result = ensure_gitkeep(str(target_dir))

        assert result is True
        assert target_dir.exists()
        assert (target_dir / ".gitkeep").exists()

    def test_creates_empty_file(self, tmp_path):
        """Test that the created .gitkeep file is empty."""
        target_dir = tmp_path / "empty_test"
        ensure_gitkeep(str(target_dir))
        gitkeep_file = target_dir / ".gitkeep"

        assert gitkeep_file.stat().st_size == 0

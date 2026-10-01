import os
import tempfile
import shutil
import pytest
from code.setup_data_dirs import ensure_gitkeep, main

class TestEnsureGitkeep:
    def test_creates_directory_and_gitkeep(self, tmp_path):
        """Test that ensure_gitkeep creates the directory and .gitkeep file if they don't exist."""
        target_dir = tmp_path / "test_subdir"
        assert not target_dir.exists()

        ensure_gitkeep(str(target_dir))

        assert target_dir.exists()
        assert target_dir.is_dir()
        gitkeep_file = target_dir / ".gitkeep"
        assert gitkeep_file.exists()
        assert gitkeep_file.is_file()
        assert gitkeep_file.stat().st_size == 0

    def test_uses_existing_directory(self, tmp_path):
        """Test that ensure_gitkeep does not fail if the directory already exists."""
        target_dir = tmp_path / "existing_dir"
        target_dir.mkdir()
        gitkeep_file = target_dir / ".gitkeep"
        gitkeep_file.write_text("existing content")

        ensure_gitkeep(str(target_dir))

        assert target_dir.exists()
        assert gitkeep_file.exists()
        assert gitkeep_file.read_text() == "existing content"

    def test_creates_nested_directories(self, tmp_path):
        """Test that ensure_gitkeep creates nested directories if needed."""
        target_dir = tmp_path / "level1" / "level2" / "level3"
        assert not target_dir.exists()

        ensure_gitkeep(str(target_dir))

        assert target_dir.exists()
        gitkeep_file = target_dir / ".gitkeep"
        assert gitkeep_file.exists()

class TestMain:
    def test_main_creates_standard_data_dirs(self):
        """Test that main() creates the standard data subdirectories with .gitkeep files."""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            try:
                result = main()
                assert result == 0

                expected_dirs = [
                    os.path.join("data", "raw"),
                    os.path.join("data", "generated"),
                    os.path.join("data", "results"),
                ]

                for dir_path in expected_dirs:
                    assert os.path.isdir(dir_path)
                    gitkeep_path = os.path.join(dir_path, ".gitkeep")
                    assert os.path.isfile(gitkeep_path)
                    assert os.path.getsize(gitkeep_path) == 0
            finally:
                os.chdir(original_cwd)

    def test_main_handles_existing_dirs(self):
        """Test that main() succeeds even if directories already exist."""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            try:
                # Pre-create the directories
                os.makedirs(os.path.join("data", "raw"))
                os.makedirs(os.path.join("data", "generated"))
                os.makedirs(os.path.join("data", "results"))

                result = main()
                assert result == 0

                # Verify .gitkeep files were created
                expected_gitkeeps = [
                    os.path.join("data", "raw", ".gitkeep"),
                    os.path.join("data", "generated", ".gitkeep"),
                    os.path.join("data", "results", ".gitkeep"),
                ]
                for path in expected_gitkeeps:
                    assert os.path.isfile(path)
            finally:
                os.chdir(original_cwd)
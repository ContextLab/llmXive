import pytest
import os
from pathlib import Path
from code.setup_directories import ensure_directory, main
from utils.logger import ConfigurationError

class TestSetupDirectories:
    def test_ensure_directory_creates_new(self, tmp_path):
        new_dir = tmp_path / "new" / "sub" / "dir"
        ensure_directory(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_exists_no_op(self, tmp_path):
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        ensure_directory(existing_dir)
        assert existing_dir.is_dir()

    def test_ensure_directory_raises_on_file(self, tmp_path):
        file_path = tmp_path / "file.txt"
        file_path.touch()
        with pytest.raises(ConfigurationError):
            ensure_directory(file_path)

    def test_main_creates_project_structure(self, tmp_path, monkeypatch):
        # Change to tmp_path to avoid cluttering real FS during test
        monkeypatch.chdir(tmp_path)
        
        # Mock the project root path for testing
        # We can't easily mock the hardcoded path in main(), so we test the logic
        # by checking if the function runs without error and creates the expected dirs
        # relative to the current working directory (which is tmp_path)
        
        # We need to adjust the test to verify the structure relative to tmp_path
        # Since main() hardcodes "projects/PROJ-800...", we create that structure manually
        # and verify the function logic works, or we patch the path.
        
        # Better approach: verify the side effects of main() by checking the state
        # But since main() writes to 'state/', we need to ensure that works too.
        
        # Let's just run main() and verify the directories exist
        main()
        
        project_root = Path("projects/PROJ-800-assessing-parcellation-sensitivity-of-hu")
        assert project_root.exists()
        
        expected_dirs = [
            "data/raw",
            "data/processed",
            "data/results",
            "code",
            "tests"
        ]
        
        for d in expected_dirs:
            full_path = project_root / d
            assert full_path.exists(), f"Missing directory: {full_path}"
            assert full_path.is_dir(), f"Not a directory: {full_path}"

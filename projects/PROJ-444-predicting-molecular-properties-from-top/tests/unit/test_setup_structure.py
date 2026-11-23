import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import ensure_directory, initialize_readme

class TestSetupProjectStructure:
    def test_ensure_directory_creates_new(self, tmp_path):
        """Test that ensure_directory creates a new directory."""
        new_dir = tmp_path / "subdir" / "nested"
        assert not new_dir.exists()
        
        ensure_directory(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_existing(self, tmp_path):
        """Test that ensure_directory does nothing if dir exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        ensure_directory(existing_dir)
        
        assert existing_dir.exists()

    def test_initialize_readme(self, tmp_path):
        """Test that initialize_readme creates README with correct content."""
        readme_path = tmp_path / "README.md"
        
        # Mock project_root as tmp_path for this test
        initialize_readme(tmp_path)
        
        assert readme_path.exists()
        assert readme_path.is_file()
        
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        assert content == "Project: Predicting Molecular Properties from TDA"

    def test_main_integration(self, tmp_path, monkeypatch):
        """
        Integration test for main() logic.
        We monkeypatch cwd to tmp_path to avoid affecting real filesystem.
        """
        from setup_project_structure import main
        
        # Change CWD for the test
        monkeypatch.chdir(tmp_path)
        
        # Run main
        # Note: main() prints to stdout, we capture it or just let it run
        # We expect it to succeed (exit code 0)
        try:
            main()
        except SystemExit as e:
            if e.code != 0:
                pytest.fail(f"main() exited with code {e.code}")

        # Verify structure
        project_name = "PROJ-444-predicting-molecular-properties-from-top"
        project_root = tmp_path / "projects" / project_name
        
        assert project_root.exists()
        assert (project_root / "code").exists()
        assert (project_root / "data" / "raw").exists()
        assert (project_root / "data" / "processed").exists()
        assert (project_root / "data" / "logs").exists()
        assert (project_root / "tests").exists()
        assert (project_root / "reports").exists()
        assert (project_root / "state").exists()
        assert (project_root / "README.md").exists()
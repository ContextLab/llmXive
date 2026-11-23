import os
import pytest
import shutil
from pathlib import Path
from code.setup_docs_directory import setup_docs_directory

class TestSetupDocsDirectory:
    """Unit tests for the docs directory creation logic."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Change to a temporary directory for isolation, then restore."""
        self.original_cwd = os.getcwd()
        os.chdir(tmp_path)
        yield
        os.chdir(self.original_cwd)
        # Clean up if test left a docs folder in tmp_path (though tmp_path handles it)
        docs_dir = Path("docs")
        if docs_dir.exists():
            shutil.rmtree(docs_dir)

    def test_creates_docs_directory(self):
        """Verify that setup_docs_directory creates the docs folder."""
        assert not os.path.isdir("docs")
        result = setup_docs_directory()
        assert result is True
        assert os.path.isdir("docs")

    def test_returns_true_if_exists(self):
        """Verify that setup_docs_directory returns True if directory already exists."""
        Path("docs").mkdir()
        result = setup_docs_directory()
        assert result is True
        assert os.path.isdir("docs")

    def test_creates_readme(self):
        """Verify that a README.md is created inside the docs directory."""
        setup_docs_directory()
        readme_path = Path("docs") / "README.md"
        assert readme_path.exists()
        content = readme_path.read_text()
        assert "# Project Documentation" in content

    def test_os_path_isdir_verification(self):
        """Explicit verification of the task requirement: os.path.isdir('docs')."""
        setup_docs_directory()
        assert os.path.isdir('docs'), "Task requirement failed: os.path.isdir('docs') is False"
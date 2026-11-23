import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path to import setup_linting
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_linting import ensure_ruff_config, ensure_black_config

class TestSetupLinting:
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to act as project root."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_ruff_config_created(self, temp_project_root):
        """Test that .ruff.toml is created if it doesn't exist."""
        ruff_path = temp_project_root / ".ruff.toml"
        assert not ruff_path.exists()

        ensure_ruff_config(temp_project_root)

        assert ruff_path.exists()
        content = ruff_path.read_text()
        assert "target-version" in content
        assert "select" in content
        assert "E" in content  # pycodestyle errors

    def test_ruff_config_exists_no_overwrite(self, temp_project_root):
        """Test that existing ruff config is not overwritten (in this impl, we just log)."""
        ruff_path = temp_project_root / ".ruff.toml"
        ruff_path.write_text("existing content")

        ensure_ruff_config(temp_project_root)

        # Content should remain unchanged (our impl just prints and returns)
        assert ruff_path.read_text() == "existing content"

    def test_black_config_added_to_empty(self, temp_project_root):
        """Test that [tool.black] section is added to empty pyproject.toml."""
        pyproject_path = temp_project_root / "pyproject.toml"
        
        ensure_black_config(temp_project_root)

        assert pyproject_path.exists()
        content = pyproject_path.read_text()
        assert "[tool.black]" in content
        assert "line-length" in content
        assert "88" in content

    def test_black_config_not_duplicated(self, temp_project_root):
        """Test that [tool.black] is not added if it already exists."""
        pyproject_path = temp_project_root / "pyproject.toml"
        initial_content = """
        [project]
        name = "test"

        [tool.black]
        line-length = 120
        """
        pyproject_path.write_text(initial_content)

        ensure_black_config(temp_project_root)

        content = pyproject_path.read_text()
        # Should still have only one [tool.black] section
        assert content.count("[tool.black]") == 1
        # Original content should be preserved
        assert "line-length = 120" in content

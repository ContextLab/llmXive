import os
import subprocess
import tempfile
from pathlib import Path
import pytest

@pytest.fixture
def project_root():
    """Get the project root directory."""
    # Assuming this test runs from within the code/ directory or parent
    # We look for pyproject.toml to find the root
    current = Path(__file__).parent
    while current.parent != current:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return current.parent

class TestLintingConfiguration:
    """Test that linting and formatting tools are properly configured."""

    def test_pyproject_toml_exists(self, project_root):
        """Verify pyproject.toml exists with tool configurations."""
        config_file = project_root / "pyproject.toml"
        assert config_file.exists(), "pyproject.toml must exist in project root"

        content = config_file.read_text()
        assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
        assert "[tool.ruff]" in content or "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
        assert "line-length = 88" in content, "Line length configuration missing"
        assert "py311" in content, "Python 3.11 target version missing"

    def test_ruff_config_exists(self, project_root):
        """Verify .ruff.toml or ruff config exists."""
        # Check for .ruff.toml
        ruff_file = project_root / ".ruff.toml"
        if not ruff_file.exists():
            # Check if config is in pyproject.toml (already tested above)
            config_file = project_root / "pyproject.toml"
            content = config_file.read_text()
            assert "[tool.ruff]" in content, "Ruff configuration must exist in .ruff.toml or pyproject.toml"
        else:
            content = ruff_file.read_text()
            assert "target-version" in content or "py311" in content, "Ruff target version missing"

    def test_black_config_exists(self, project_root):
        """Verify .black.toml or black config exists."""
        black_file = project_root / ".black.toml"
        if not black_file.exists():
            # Check if config is in pyproject.toml
            config_file = project_root / "pyproject.toml"
            content = config_file.read_text()
            assert "[tool.black]" in content, "Black configuration must exist in .black.toml or pyproject.toml"
        else:
            content = black_file.read_text()
            assert "line-length" in content, "Black line-length missing"

    def test_ruff_syntax_check(self, project_root):
        """Run ruff check on a sample file to ensure it works."""
        # Create a temporary valid python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass\n")
            temp_file = f.name

        try:
            # Run ruff check
            result = subprocess.run(
                ["ruff", "check", temp_file],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            # Should exit with 0 (no errors) for valid code
            assert result.returncode == 0 or "No errors found" in result.stdout, \
                f"Ruff check failed unexpectedly: {result.stderr}"
        finally:
            os.unlink(temp_file)

    def test_black_format_check(self, project_root):
        """Run black --check on a sample file to ensure it works."""
        # Create a temporary valid python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test_func():\n    pass\n")
            temp_file = f.name

        try:
            # Run black --check
            result = subprocess.run(
                ["black", "--check", temp_file],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            # Should exit with 0 (no changes needed) for valid code
            assert result.returncode == 0, \
                f"Black check failed: {result.stderr}"
        finally:
            os.unlink(temp_file)

    def test_requirements_dev_included(self, project_root):
        """Verify dev dependencies include linting tools."""
        config_file = project_root / "pyproject.toml"
        content = config_file.read_text()
        assert "ruff" in content, "Ruff not in dependencies"
        assert "black" in content, "Black not in dependencies"

    def test_pytest_config_exists(self, project_root):
        """Verify pytest configuration exists."""
        config_file = project_root / "pyproject.toml"
        content = config_file.read_text()
        assert "[tool.pytest.ini_options]" in content, "Pytest configuration missing"
        assert "testpaths" in content, "Pytest test paths missing"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
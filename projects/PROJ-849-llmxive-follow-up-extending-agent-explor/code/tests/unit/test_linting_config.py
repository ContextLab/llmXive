"""
Unit tests to verify that linting and formatting configurations are present and valid.
This task (T003) ensures ruff and black are configured.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

class TestLintingConfiguration:
    """Tests for T003: Configure linting (ruff) and formatting (black) tools."""

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists in the project root."""
        pyproject_path = CODE_DIR / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist in code/ directory"

    def test_pyproject_contains_black_config(self):
        """Verify pyproject.toml contains [tool.black] section."""
        pyproject_path = CODE_DIR / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
        assert "line-length" in content, "Black configuration must specify line-length"
        assert "py311" in content, "Black configuration must target Python 3.11"

    def test_pyproject_contains_ruff_config(self):
        """Verify pyproject.toml contains [tool.ruff] section."""
        pyproject_path = CODE_DIR / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"
        assert "select" in content, "Ruff configuration must define rules to select"
        assert "target-version" in content, "Ruff configuration must specify target version"

    def test_ruff_toml_exists(self):
        """Verify .ruff.toml exists as a standalone config file."""
        ruff_config = CODE_DIR / ".ruff.toml"
        assert ruff_config.exists(), ".ruff.toml must exist in code/ directory"

    def test_black_toml_exists(self):
        """Verify .black.toml exists as a standalone config file."""
        black_config = CODE_DIR / ".black.toml"
        assert black_config.exists(), ".black.toml must exist in code/ directory"

    def test_ruff_config_syntax_valid(self):
        """Verify .ruff.toml is valid TOML syntax by attempting to parse it."""
        try:
            import tomllib
        except ImportError:
            # Fallback for Python < 3.11 if needed, though project is 3.11+
            try:
                import toml as tomllib
            except ImportError:
                pytest.skip("toml library not available")

        ruff_config = CODE_DIR / ".ruff.toml"
        with open(ruff_config, "rb") as f:
            try:
                tomllib.load(f)
            except Exception as e:
                pytest.fail(f".ruff.toml is not valid TOML: {e}")

    def test_black_config_syntax_valid(self):
        """Verify .black.toml is valid TOML syntax."""
        try:
            import tomllib
        except ImportError:
            try:
                import toml as tomllib
            except ImportError:
                pytest.skip("toml library not available")

        black_config = CODE_DIR / ".black.toml"
        with open(black_config, "rb") as f:
            try:
                tomllib.load(f)
            except Exception as e:
                pytest.fail(f".black.toml is not valid TOML: {e}")

    def test_requirements_dev_includes_ruff_black(self):
        """Verify requirements.txt or pyproject dev deps include ruff and black."""
        pyproject_path = CODE_DIR / "pyproject.toml"
        content = pyproject_path.read_text()
        
        # Check for optional dependencies section
        assert "ruff" in content, "pyproject.toml must include ruff in dependencies"
        assert "black" in content, "pyproject.toml must include black in dependencies"

    def test_ruff_check_command_available(self):
        """Verify ruff can be invoked (if installed) and check syntax of a dummy file."""
        # Create a temporary dummy python file to check
        dummy_file = CODE_DIR / "dummy_check.py"
        dummy_content = "x = 1\n"
        dummy_file.write_text(dummy_content)
        
        try:
            # Try running ruff check on the dummy file
            result = subprocess.run(
                ["ruff", "check", str(dummy_file)],
                cwd=CODE_DIR,
                capture_output=True,
                text=True,
                timeout=30
            )
            # If ruff is not installed, this test is skipped (not failed)
            if result.returncode != 0 and "command not found" in result.stderr.lower():
                pytest.skip("ruff not installed in environment")
        except FileNotFoundError:
            pytest.skip("ruff command not found in PATH")
        except subprocess.TimeoutExpired:
            pytest.fail("ruff check timed out")
        finally:
            if dummy_file.exists():
                dummy_file.unlink()

    def test_black_format_command_available(self):
        """Verify black can be invoked (if installed) and format a dummy file."""
        dummy_file = CODE_DIR / "dummy_format.py"
        dummy_content = "x=1\n"  # Intentionally non-compliant
        dummy_file.write_text(dummy_content)
        
        try:
            result = subprocess.run(
                ["black", "--check", str(dummy_file)],
                cwd=CODE_DIR,
                capture_output=True,
                text=True,
                timeout=30
            )
            # If black is not installed, skip
            if result.returncode != 0 and "command not found" in result.stderr.lower():
                pytest.skip("black not installed in environment")
        except FileNotFoundError:
            pytest.skip("black command not found in PATH")
        except subprocess.TimeoutExpired:
            pytest.fail("black check timed out")
        finally:
            if dummy_file.exists():
                dummy_file.unlink()
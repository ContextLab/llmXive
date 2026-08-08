import os
import sys
import toml
from pathlib import Path
import pytest

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestLintingConfig:
    """Tests to verify that linting and formatting tools are configured correctly."""

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists in the project root."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist in project root"

    def test_black_config_present(self):
        """Verify Black configuration exists in pyproject.toml."""
        pyproject_path = project_root / "pyproject.toml"
        with open(pyproject_path, "r") as f:
            config = toml.load(f)
        
        assert "tool" in config, "tool section must exist in pyproject.toml"
        assert "black" in config["tool"], "black configuration must exist"
        assert "line-length" in config["tool"]["black"], "black line-length must be configured"
        assert config["tool"]["black"]["line-length"] == 88, "Black line-length should be 88"

    def test_ruff_config_present(self):
        """Verify Ruff configuration exists in pyproject.toml."""
        pyproject_path = project_root / "pyproject.toml"
        with open(pyproject_path, "r") as f:
            config = toml.load(f)
        
        assert "tool" in config, "tool section must exist in pyproject.toml"
        assert "ruff" in config["tool"], "ruff configuration must exist"
        assert "select" in config["tool"]["ruff"], "ruff select rules must be configured"
        assert "E" in config["tool"]["ruff"]["select"], "ruff must check pycodestyle errors"
        assert "F" in config["tool"]["ruff"]["select"], "ruff must check pyflakes"

    def test_ruff_standalone_config_exists(self):
        """Verify .ruff.toml exists as standalone config."""
        ruff_config = project_root / ".ruff.toml"
        assert ruff_config.exists(), ".ruff.toml must exist for standalone ruff configuration"

    def test_dev_dependencies_included(self):
        """Verify linting tools are in optional dependencies."""
        pyproject_path = project_root / "pyproject.toml"
        with open(pyproject_path, "r") as f:
            config = toml.load(f)
        
        assert "optional-dependencies" in config["project"], "optional-dependencies must exist"
        assert "dev" in config["project"]["optional-dependencies"], "dev dependencies must exist"
        
        dev_deps = config["project"]["optional-dependencies"]["dev"]
        has_ruff = any("ruff" in dep for dep in dev_deps)
        has_black = any("black" in dep for dep in dev_deps)
        
        assert has_ruff, "ruff must be in dev dependencies"
        assert has_black, "black must be in dev dependencies"
    
    def test_lint_check_script_exists(self):
        """Verify the lint_check.py script exists."""
        lint_script = project_root / "code" / "lint_check.py"
        assert lint_script.exists(), "code/lint_check.py must exist"

    def test_lint_check_script_imports(self):
        """Verify lint_check.py has valid syntax and imports."""
        lint_script = project_root / "code" / "lint_check.py"
        with open(lint_script, "r") as f:
            code = f.read()
        
        # Compile to check syntax
        try:
            compile(code, str(lint_script), 'exec')
        except SyntaxError as e:
            pytest.fail(f"Syntax error in lint_check.py: {e}")
        
        # Check for required imports
        assert "subprocess" in code, "lint_check.py must import subprocess"
        assert "main" in code, "lint_check.py must define main function"
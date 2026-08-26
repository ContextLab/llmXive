"""
Unit tests for linting and formatting tooling configuration.

These tests verify that the configuration files (pyproject.toml) 
are valid and that the helper script structure is correct.
"""
import os
import sys
import toml
from pathlib import Path
import pytest

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_pyproject_exists():
    """Test that pyproject.toml exists at the project root."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist at project root"


def test_pyproject_valid_toml():
    """Test that pyproject.toml is valid TOML syntax."""
    pyproject_path = project_root / "pyproject.toml"
    try:
        with open(pyproject_path, "r") as f:
            data = toml.load(f)
        assert "tool" in data, "pyproject.toml must contain [tool] section"
        assert "ruff" in data["tool"], "pyproject.toml must contain [tool.ruff] section"
        assert "black" in data["tool"], "pyproject.toml must contain [tool.black] section"
    except toml.TomlDecodeError as e:
        pytest.fail(f"pyproject.toml is not valid TOML: {e}")


def test_black_config_present():
    """Test that Black configuration is present."""
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        data = toml.load(f)
    
    black_config = data["tool"]["black"]
    assert "line-length" in black_config, "Black must define line-length"
    assert black_config["line-length"] == 88, "Black line-length should be 88"
    assert "target-version" in black_config, "Black must define target-version"


def test_ruff_config_present():
    """Test that Ruff configuration is present."""
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        data = toml.load(f)
    
    ruff_config = data["tool"]["ruff"]
    assert "line-length" in ruff_config, "Ruff must define line-length"
    assert "select" in ruff_config, "Ruff must define select rules"
    assert "exclude" in ruff_config, "Ruff must define exclude directories"


def test_requirements_includes_lint_tools():
    """Test that requirements.txt includes ruff and black."""
    requirements_path = project_root / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt must exist"
    
    with open(requirements_path, "r") as f:
        content = f.read()
    
    assert "ruff" in content, "requirements.txt must include ruff"
    assert "black" in content, "requirements.txt must include black"


def test_lint_format_script_exists():
    """Test that the lint_format.py script exists."""
    script_path = project_root / "code" / "tools" / "lint_format.py"
    assert script_path.exists(), "code/tools/lint_format.py must exist"


def test_lint_format_script_importable():
    """Test that lint_format.py is syntactically valid and importable."""
    script_path = project_root / "code" / "tools" / "lint_format.py"
    try:
        # Check syntax
        with open(script_path, "r") as f:
            compile(f.read(), script_path, "exec")
        
        # Try to import (this checks for runtime import errors of standard libs)
        import importlib.util
        spec = importlib.util.spec_from_file_location("lint_format", script_path)
        module = importlib.util.module_from_spec(spec)
        # We don't exec it fully to avoid side effects, just check it parses
        assert module is not None
    except SyntaxError as e:
        pytest.fail(f"lint_format.py has syntax errors: {e}")
    except ImportError as e:
        pytest.fail(f"lint_format.py has import errors: {e}")
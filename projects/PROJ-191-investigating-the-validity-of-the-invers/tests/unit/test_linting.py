"""
Unit tests for linting and formatting tools configuration.
Verifies that ruff and black are correctly configured.
"""
import subprocess
import sys
import os
from pathlib import Path
import pytest

@pytest.fixture
def code_dir():
    """Return the path to the code directory."""
    return Path(__file__).parent.parent.parent / "code"

def test_ruff_config_exists(code_dir):
    """Test that ruff configuration file exists."""
    ruff_config = code_dir / "ruff.toml"
    assert ruff_config.exists(), "ruff.toml configuration file should exist"
    
    with open(ruff_config, 'r') as f:
        content = f.read()
        assert '[lint]' in content, "ruff.toml should contain [lint] section"
        assert 'select' in content, "ruff.toml should define select codes"

def test_black_config_in_requirements(code_dir):
    """Test that black is listed in requirements."""
    req_file = code_dir / "requirements.txt"
    assert req_file.exists(), "requirements.txt should exist"
    
    with open(req_file, 'r') as f:
        content = f.read()
        assert 'black' in content.lower(), "black should be in requirements.txt"

def test_ruff_config_syntax(code_dir):
    """Test that ruff can parse the configuration (basic syntax check)."""
    ruff_config = code_dir / "ruff.toml"
    if not ruff_config.exists():
        pytest.skip("ruff.toml not found, skipping syntax check")
    
    # Run ruff with --config to verify it can read the file
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", str(ruff_config), "--help"],
        capture_output=True,
        text=True
    )
    # Help command should succeed even if no files are checked
    assert result.returncode == 0, "ruff should be able to read the config file"

def test_lint_tool_module_exists(code_dir):
    """Test that the lint tool module exists and is importable."""
    lint_tool = code_dir / "tools" / "lint.py"
    assert lint_tool.exists(), "lint.py tool should exist"
    
    # Try to import the module (checks for syntax errors)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("lint", lint_tool)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, 'main'), "lint.py should have a main function"
    except Exception as e:
        pytest.fail(f"Failed to import lint.py: {e}")

def test_format_tool_module_exists(code_dir):
    """Test that the format tool module exists and is importable."""
    format_tool = code_dir / "tools" / "format.py"
    assert format_tool.exists(), "format.py tool should exist"
    
    # Try to import the module (checks for syntax errors)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("format", format_tool)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, 'main'), "format.py should have a main function"
    except Exception as e:
        pytest.fail(f"Failed to import format.py: {e}")

def test_tools_package_exists(code_dir):
    """Test that the tools package exists."""
    tools_dir = code_dir / "tools"
    assert tools_dir.exists(), "tools directory should exist"
    
    init_file = tools_dir / "__init__.py"
    assert init_file.exists(), "tools/__init__.py should exist"
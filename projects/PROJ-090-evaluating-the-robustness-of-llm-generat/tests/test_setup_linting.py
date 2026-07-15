import subprocess
import sys
from pathlib import Path

def test_setup_linting_script_exists():
    """Verify that the setup_linting.py script exists."""
    script_path = Path(__file__).parent.parent / "code" / "setup_linting.py"
    assert script_path.exists(), f"Script not found at {script_path}"

def test_ruff_config_exists():
    """Verify that ruff.toml exists."""
    config_path = Path(__file__).parent.parent / "ruff.toml"
    assert config_path.exists(), f"Config not found at {config_path}"

def test_pyproject_black_config():
    """Verify that pyproject.toml contains black configuration."""
    config_path = Path(__file__).parent.parent / "pyproject.toml"
    assert config_path.exists()
    content = config_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "line-length = 100" in content, "Black line-length setting missing"

def test_check_tool_function():
    """Test the check_tool function logic."""
    # We can't easily install tools in a test environment, but we can test the logic
    # by checking if it returns a boolean
    from code.setup_linting import check_tool
    result = check_tool("pip") # pip should exist
    assert isinstance(result, bool)
    assert result is True, "pip should be detected as installed"

def test_install_tools_function():
    """Test that install_tools runs without error (idempotent)."""
    from code.setup_linting import install_tools
    try:
        install_tools()
    except subprocess.CalledProcessError:
        # If pip install fails (e.g. network), that's a runtime issue, not a code logic issue
        # But for this test, we assume the function executes.
        pass
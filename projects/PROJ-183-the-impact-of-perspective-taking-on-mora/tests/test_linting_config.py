"""
Tests to verify that pyproject.toml and .ruff.toml exist and contain required configurations.
This validates Task T004a.
"""
import os
import toml
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYPROJECT_PATH = os.path.join(PROJECT_ROOT, "pyproject.toml")
RUFF_CONFIG_PATH = os.path.join(PROJECT_ROOT, ".ruff.toml")

def test_pyproject_exists():
    assert os.path.exists(PYPROJECT_PATH), "pyproject.toml must exist"

def test_ruff_config_exists():
    assert os.path.exists(RUFF_CONFIG_PATH), ".ruff.toml must exist"

def test_black_line_length_in_pyproject():
    """Verify Black line-length is set to 88 in pyproject.toml"""
    assert os.path.exists(PYPROJECT_PATH)
    with open(PYPROJECT_PATH, "r") as f:
        config = toml.load(f)
    
    black_config = config.get("tool", {}).get("black", {})
    assert black_config.get("line-length") == 88, "Black line-length must be 88"

def test_ruff_line_length_in_ruff_config():
    """Verify line-length is set to 88 in .ruff.toml"""
    assert os.path.exists(RUFF_CONFIG_PATH)
    with open(RUFF_CONFIG_PATH, "r") as f:
        content = f.read()
    
    assert "line-length = 88" in content, ".ruff.toml must contain 'line-length = 88'"

def test_ruff_select_rules():
    """Verify E, W, F rule sets are selected in .ruff.toml"""
    assert os.path.exists(RUFF_CONFIG_PATH)
    with open(RUFF_CONFIG_PATH, "r") as f:
        content = f.read()
    
    # Check for the presence of the select list containing E, W, F
    assert '"E"' in content or "'E'" in content, ".ruff.toml must select E rules"
    assert '"W"' in content or "'W'" in content, ".ruff.toml must select W rules"
    assert '"F"' in content or "'F'" in content, ".ruff.toml must select F rules"

def test_f401_not_ignored_globally():
    """Ensure F401 is not globally ignored, only in specific files like __init__.py"""
    assert os.path.exists(RUFF_CONFIG_PATH)
    with open(RUFF_CONFIG_PATH, "r") as f:
        content = f.read()
    
    # The ignore list should be empty or not contain F401 globally
    if "ignore = [" in content:
        assert "F401" not in content.split("ignore = [")[1].split("]")[0], \
            "F401 should not be globally ignored"
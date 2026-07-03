"""
Tests to verify that linting and formatting configurations are correctly set up.
"""
import os
import toml
import pytest

@pytest.fixture
def pyproject_path():
    return "pyproject.toml"

def test_pyproject_exists(pyproject_path):
    """Test that pyproject.toml exists"""
    assert os.path.exists(pyproject_path), "pyproject.toml should exist"

def test_ruff_config_present(pyproject_path):
    """Test that ruff configuration is present in pyproject.toml"""
    with open(pyproject_path, "r", encoding="utf-8") as f:
        config = toml.load(f)
    
    assert "tool" in config, "tool section should exist in pyproject.toml"
    assert "ruff" in config["tool"], "ruff configuration should exist"
    
    ruff_config = config["tool"]["ruff"]
    assert "lint" in ruff_config, "ruff lint section should exist"
    assert "select" in ruff_config["lint"], "ruff select rules should be defined"
    assert "E" in ruff_config["lint"]["select"], "E (pycodestyle errors) should be selected"
    assert "F" in ruff_config["lint"]["select"], "F (pyflakes) should be selected"

def test_black_config_present(pyproject_path):
    """Test that black configuration is present in pyproject.toml"""
    with open(pyproject_path, "r", encoding="utf-8") as f:
        config = toml.load(f)
    
    assert "tool" in config, "tool section should exist in pyproject.toml"
    assert "black" in config["tool"], "black configuration should exist"
    
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "black line-length should be defined"
    assert black_config["line-length"] == 88, "black line-length should be 88"

def test_target_version_consistency(pyproject_path):
    """Test that ruff and black target the same Python version"""
    with open(pyproject_path, "r", encoding="utf-8") as f:
        config = toml.load(f)
    
    ruff_target = config["tool"]["ruff"].get("target-version", "")
    black_targets = config["tool"]["black"].get("target-version", [])
    
    # Convert black targets to string for comparison if needed
    black_target_str = "py311" if "py311" in black_targets else ""
    
    assert ruff_target == "py311", "ruff should target py311"
    assert "py311" in black_targets, "black should target py311"

def test_lint_script_exists():
    """Test that the linting convenience script exists"""
    script_path = "code/tools/run_lint.sh"
    assert os.path.exists(script_path), f"{script_path} should exist"

def test_lint_script_content():
    """Test that the linting script contains expected commands"""
    script_path = "code/tools/run_lint.sh"
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "ruff check" in content, "Script should run ruff check"
    assert "black --check" in content, "Script should run black check"
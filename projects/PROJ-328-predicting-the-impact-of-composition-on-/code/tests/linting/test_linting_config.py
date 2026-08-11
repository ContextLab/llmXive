import subprocess
import os
import pytest
from pathlib import Path
import toml

# Determine project root relative to this test file
# Expected structure: project_root/code/tests/linting/
current_dir = Path(__file__).resolve().parent
code_dir = current_dir.parent
project_root = code_dir.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists in code directory."""
    flake8_path = code_dir / ".flake8"
    assert flake8_path.exists(), f"Missing .flake8 config at {flake8_path}"

def test_pyproject_toml_exists():
    """Verify pyproject.toml with Black settings exists in code directory."""
    pyproject_path = code_dir / "pyproject.toml"
    assert pyproject_path.exists(), f"Missing pyproject.toml at {pyproject_path}"
    
    # Verify Black section exists
    config = toml.load(pyproject_path)
    assert "tool" in config
    assert "black" in config["tool"], "Missing [tool.black] section in pyproject.toml"
    assert "line-length" in config["tool"]["black"], "Missing line-length in Black config"

def test_black_can_parse_config():
    """Verify Black can successfully parse the configuration."""
    black_path = code_dir / "pyproject.toml"
    result = subprocess.run(
        ["black", "--check", "--diff", "--config", str(black_path), "."],
        cwd=code_dir,
        capture_output=True,
        text=True
    )
    # Black might return non-zero if files need formatting, but it must NOT crash on config parsing
    # We just verify the config file is valid by checking if black runs without syntax errors
    assert "SyntaxError" not in result.stderr and "Invalid" not in result.stderr

def test_flake8_can_parse_config():
    """Verify flake8 can successfully parse the configuration."""
    flake8_path = code_dir / ".flake8"
    result = subprocess.run(
        ["flake8", "--version"],
        cwd=code_dir,
        capture_output=True,
        text=True
    )
    # Just verify flake8 is available and can read the config
    assert result.returncode == 0 or "No module named 'flake8'" not in result.stderr
    
    # Try a dry run on a dummy file to ensure config is readable
    test_file = code_dir / "test_dummy_config.py"
    try:
        with open(test_file, "w") as f:
            f.write("x = 1\n")
        result = subprocess.run(
            ["flake8", "--config", str(flake8_path), str(test_file)],
            cwd=code_dir,
            capture_output=True,
            text=True
        )
    finally:
        if test_file.exists():
            test_file.unlink()
    
    # Should not raise a config parsing error
    assert "Failed to load" not in result.stderr and "Invalid" not in result.stderr

def test_linting_rules_are_reasonable():
    """Verify that the configured line length and max-complexity are reasonable."""
    pyproject_path = code_dir / "pyproject.toml"
    config = toml.load(pyproject_path)
    
    line_length = config["tool"]["black"].get("line-length", 88)
    assert 80 <= line_length <= 150, f"Black line-length {line_length} is outside reasonable range"
    
    flake8_path = code_dir / ".flake8"
    # Simple check that max-line-length is defined
    with open(flake8_path, "r") as f:
        content = f.read()
        assert "max-line-length" in content, "max-line-length not found in .flake8"
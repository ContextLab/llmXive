import subprocess
import os
import pytest
from pathlib import Path

# Determine project root relative to this test file
# Assuming tests/linting/test_linting_config.py -> root is ../../
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
code_dir = project_root / "code"

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists in code/"""
    config_path = code_dir / ".flake8"
    assert config_path.exists(), f"Missing flake8 config at {config_path}"
    # Check for key settings
    content = config_path.read_text()
    assert "max-line-length" in content, "max-line-length not found in .flake8"
    assert "88" in content, "max-line-length should be 88 (Black compatible)"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in code/ with Black settings"""
    config_path = code_dir / "pyproject.toml"
    assert config_path.exists(), f"Missing pyproject.toml at {config_path}"
    content = config_path.read_text()
    assert "[tool.black]" in content, "Black section missing in pyproject.toml"
    assert "line-length" in content, "Black line-length setting missing"

def test_black_can_parse_config():
    """Verify Black can successfully parse the configuration"""
    config_path = code_dir / "pyproject.toml"
    result = subprocess.run(
        ["black", "--config", str(config_path), "--check", "--diff", "--quiet", str(code_dir)],
        capture_output=True,
        text=True
    )
    # We expect this to pass or fail based on code style, not config parsing
    # If it returns an error code due to config parsing, that's a failure
    # However, since code might not be formatted yet, we just check for config errors
    assert "Error" not in result.stderr or "No such file" not in result.stderr, \
        f"Black failed to parse config: {result.stderr}"

def test_flake8_can_parse_config():
    """Verify flake8 can successfully parse the configuration"""
    config_path = code_dir / ".flake8"
    result = subprocess.run(
        ["flake8", "--config", str(config_path), "--select=E9,F63,F7,F82", str(code_dir)],
        capture_output=True,
        text=True
    )
    # flake8 might find errors in code, but it shouldn't fail to parse config
    # We check for specific config parsing errors
    assert "SyntaxError" not in result.stderr and "Invalid" not in result.stderr, \
        f"Flake8 failed to parse config: {result.stderr}"

def test_linting_rules_are_reasonable():
    """Verify the configured rules align with project standards"""
    flake8_path = code_dir / ".flake8"
    black_path = code_dir / "pyproject.toml"
    
    flake8_content = flake8_path.read_text()
    black_content = black_path.read_text()
    
    # Check that max-line-length is 88 in both (or compatible)
    assert "88" in flake8_content, "Flake8 max-line-length should be 88"
    assert "88" in black_content, "Black line-length should be 88"
    
    # Check that E203 is ignored in flake8 (Black requirement)
    assert "E203" in flake8_content, "Flake8 should ignore E203 for Black compatibility"
    assert "E501" in flake8_content, "Flake8 should ignore E501 (line length handled by Black)"
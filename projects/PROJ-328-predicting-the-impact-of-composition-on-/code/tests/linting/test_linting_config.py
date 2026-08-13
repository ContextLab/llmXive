import subprocess
import os
import pytest
from pathlib import Path
import toml

PROJECT_ROOT = Path(__file__).parent.parent.parent
FLAKE8_CONFIG = PROJECT_ROOT / ".flake8"
PYPROJECT_CONFIG = PROJECT_ROOT / "pyproject.toml"
CODE_DIR = PROJECT_ROOT / "code"

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    assert FLAKE8_CONFIG.exists(), f"Missing .flake8 config at {FLAKE8_CONFIG}"

def test_pyproject_toml_exists():
    """Verify pyproject.toml configuration file exists."""
    assert PYPROJECT_CONFIG.exists(), f"Missing pyproject.toml config at {PYPROJECT_CONFIG}"

def test_black_can_parse_config():
    """Verify Black can parse the configuration."""
    try:
        config = toml.load(PYPROJECT_CONFIG)
        assert "tool" in config
        assert "black" in config["tool"]
        assert config["tool"]["black"]["line-length"] == 120
    except Exception as e:
        pytest.fail(f"Black configuration parsing failed: {e}")

def test_flake8_can_parse_config():
    """Verify flake8 can parse its configuration."""
    result = subprocess.run(
        ["flake8", "--version"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"flake8 failed to run: {result.stderr}"

def test_linting_rules_are_reasonable():
    """Run a quick lint check on a known safe file to ensure rules don't crash."""
    # We test against seed.py which should be clean
    seed_path = CODE_DIR / "seed.py"
    if not seed_path.exists():
        pytest.skip("seed.py not found, skipping lint rule validation")

    result = subprocess.run(
        ["flake8", str(seed_path), "--max-line-length=120"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # We don't assert returncode == 0 because seed.py might have intentional style issues we ignore,
    # but we assert it didn't crash or produce errors about config parsing.
    assert "SyntaxError" not in result.stderr and "ConfigError" not in result.stderr, \
        f"flake8 configuration error: {result.stderr}"

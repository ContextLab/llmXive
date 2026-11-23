"""
Tests to verify linting and formatting configuration files exist and are valid TOML.
"""
import os
import toml
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")

@pytest.fixture
def ruff_config_path():
    return os.path.join(CODE_DIR, ".ruff.toml")

@pytest.fixture
def black_config_path():
    return os.path.join(CODE_DIR, ".black.toml")

def test_ruff_config_exists(ruff_config_path):
    assert os.path.exists(ruff_config_path), f"Ruff config missing at {ruff_config_path}"

def test_black_config_exists(black_config_path):
    assert os.path.exists(black_config_path), f"Black config missing at {black_config_path}"

def test_ruff_config_valid_toml(ruff_config_path):
    try:
        with open(ruff_config_path, "r") as f:
            data = toml.load(f)
        assert "lint" in data, "Ruff config missing 'lint' section"
        assert "select" in data["lint"], "Ruff config missing 'lint.select'"
    except Exception as e:
        pytest.fail(f"Ruff config is not valid TOML: {e}")

def test_black_config_valid_toml(black_config_path):
    try:
        with open(black_config_path, "r") as f:
            data = toml.load(f)
        assert "tool" in data, "Black config missing 'tool' section"
        assert "black" in data["tool"], "Black config missing 'tool.black' section"
    except Exception as e:
        pytest.fail(f"Black config is not valid TOML: {e}")

def test_ruff_select_contains_standard_checks(ruff_config_path):
    with open(ruff_config_path, "r") as f:
        data = toml.load(f)
    selected = data["lint"]["select"]
    # Ensure we are checking for syntax errors and common issues
    assert "E" in selected, "Ruff config should select E (pycodestyle errors)"
    assert "F" in selected, "Ruff config should select F (pyflakes)"

def test_black_line_length_is_reasonable(black_config_path):
    with open(black_config_path, "r") as f:
        data = toml.load(f)
    line_length = data["tool"]["black"].get("line-length", 88)
    assert 80 <= line_length <= 120, f"Black line-length {line_length} is outside reasonable range (80-120)"

"""
Test suite to verify that .ruff.toml exists and is parsable.
This ensures the linting configuration is valid before running the linter.
"""
import os
import toml
import pytest
from pathlib import Path

@pytest.fixture
def ruff_config_path():
    return Path(__file__).parent.parent.parent / ".ruff.toml"

def test_ruff_config_exists(ruff_config_path):
    """Assert that the .ruff.toml file exists in the project root."""
    assert ruff_config_path.exists(), f"File not found: {ruff_config_path}"

def test_ruff_config_parsable(ruff_config_path):
    """Assert that .ruff.toml is valid TOML syntax."""
    try:
        with open(ruff_config_path, "r", encoding="utf-8") as f:
            config = toml.load(f)
        assert isinstance(config, dict), "Config must be a dictionary"
        assert "lint" in config or "format" in config, "Config should contain at least 'lint' or 'format' sections"
    except Exception as e:
        pytest.fail(f"Failed to parse .ruff.toml: {e}")

def test_ruff_config_has_select_rules(ruff_config_path):
    """Assert that the 'lint.select' list contains expected rule prefixes."""
    with open(ruff_config_path, "r", encoding="utf-8") as f:
        config = toml.load(f)

    lint_section = config.get("lint", {})
    select_rules = lint_section.get("select", [])

    expected_prefixes = {"E", "F", "I"}
    found_prefixes = {rule[:1] for rule in select_rules if isinstance(rule, str)}

    # At least E, F, I should be present for basic style and logic checks
    assert expected_prefixes.issubset(found_prefixes), (
        f"Missing expected rule prefixes {expected_prefixes - found_prefixes} in lint.select"
    )

def test_ruff_config_line_length(ruff_config_path):
    """Assert that line-length is configured to a reasonable value (e.g., 88)."""
    with open(ruff_config_path, "r", encoding="utf-8") as f:
        config = toml.load(f)

    line_length = config.get("line-length", 88)
    assert isinstance(line_length, int), "line-length must be an integer"
    assert 80 <= line_length <= 120, f"line-length {line_length} is outside reasonable range [80, 120]"
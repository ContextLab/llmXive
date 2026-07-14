"""
Unit tests to verify that linting and formatting configuration files exist and are valid.
"""
import os
import pytest
import tomli

CONFIG_FILES = [
    ".ruff.toml",
    ".black.toml",
]

class TestLintingConfig:
    """Tests for linting and formatting configuration."""

    def test_config_files_exist(self):
        """Verify that all required configuration files exist in the project root."""
        missing = []
        for file in CONFIG_FILES:
            if not os.path.exists(file):
                missing.append(file)
        
        assert not missing, f"Missing configuration files: {', '.join(missing)}"

    def test_ruff_config_valid_toml(self):
        """Verify that .ruff.toml is valid TOML."""
        with open(".ruff.toml", "rb") as f:
            try:
                config = tomli.load(f)
                assert "lint" in config or "format" in config, "Ruff config should contain 'lint' or 'format' sections"
            except tomli.TOMLDecodeError as e:
                pytest.fail(f"Invalid TOML in .ruff.toml: {e}")

    def test_black_config_valid_toml(self):
        """Verify that .black.toml is valid TOML."""
        with open(".black.toml", "rb") as f:
            try:
                config = tomli.load(f)
                assert "tool" in config and "black" in config["tool"], \
                    "Black config should contain 'tool.black' section"
            except tomli.TOMLDecodeError as e:
                pytest.fail(f"Invalid TOML in .black.toml: {e}")

    def test_black_line_length(self):
        """Verify that black line-length is set to 88."""
        with open(".black.toml", "rb") as f:
            config = tomli.load(f)
            line_length = config["tool"]["black"].get("line-length", 88)
            assert line_length == 88, f"Expected black line-length 88, got {line_length}"

    def test_ruff_ignores_line_length(self):
        """Verify that ruff ignores E501 (line too long) since black handles it."""
        with open(".ruff.toml", "rb") as f:
            config = tomli.load(f)
            ignore = config.get("lint", {}).get("ignore", [])
            assert "E501" in ignore, "Ruff should ignore E501 to avoid conflict with black"
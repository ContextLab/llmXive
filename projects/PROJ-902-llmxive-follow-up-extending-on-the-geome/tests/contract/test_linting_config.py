"""
Contract test for linting configuration (.ruff.toml).

This test validates that:
1. The .ruff.toml file exists in the project root.
2. The file is valid TOML syntax.
3. The file contains required configuration sections (e.g., [lint], [format]).
4. Specific required rules or settings are present (e.g., line length, target version).
"""
import os
import tomllib
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUFF_CONFIG_PATH = PROJECT_ROOT / ".ruff.toml"

# Required configuration keys based on project standards (derived from T003)
REQUIRED_SECTIONS = {"lint", "format"}
REQUIRED_SETTINGS = {
    "lint": {
        "select": list,  # Should be a list of rule codes
        "ignore": list,  # Should be a list of rule codes to ignore
        "target-version": str,  # e.g., "py311"
    },
    "format": {
        "line-length": int,  # e.g., 88 or 100
    },
}


def _load_ruff_config() -> dict[str, Any]:
    """Load and parse the .ruff.toml file."""
    if not RUFF_CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Linting configuration file not found at {RUFF_CONFIG_PATH}. "
            "Run T003 to generate the file."
        )

    with open(RUFF_CONFIG_PATH, "rb") as f:
        try:
            return tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML syntax in {RUFF_CONFIG_PATH}: {e}") from e


class TestLintingConfigSchema:
    """Contract tests for the .ruff.toml file structure and content."""

    def test_file_exists(self):
        """Assert that .ruff.toml exists in the project root."""
        assert RUFF_CONFIG_PATH.exists(), (
            f"File {RUFF_CONFIG_PATH} does not exist. "
            "Ensure T003 has been completed successfully."
        )

    def test_valid_toml_syntax(self):
        """Assert that the file contains valid TOML syntax."""
        # If this raises, the test fails with a clear error
        config = _load_ruff_config()
        assert isinstance(config, dict), "Parsed config must be a dictionary."

    def test_required_sections_present(self):
        """Assert that all required configuration sections exist."""
        config = _load_ruff_config()
        missing_sections = REQUIRED_SECTIONS - set(config.keys())
        
        assert not missing_sections, (
            f"Missing required sections in .ruff.toml: {missing_sections}. "
            f"Expected at least: {REQUIRED_SECTIONS}"
        )

    def test_lint_select_is_list(self):
        """Assert that 'lint.select' is a list."""
        config = _load_ruff_config()
        lint_section = config.get("lint", {})
        
        assert "select" in lint_section, (
            "Missing 'select' key in [lint] section. "
            "Define a list of rule codes (e.g., ['E', 'F', 'W'])."
        )
        
        assert isinstance(lint_section["select"], list), (
            f"'lint.select' must be a list, got {type(lint_section['select']).__name__}"
        )

    def test_lint_ignore_is_list(self):
        """Assert that 'lint.ignore' is a list."""
        config = _load_ruff_config()
        lint_section = config.get("lint", {})
        
        assert "ignore" in lint_section, (
            "Missing 'ignore' key in [lint] section. "
            "Define a list of rule codes to ignore."
        )
        
        assert isinstance(lint_section["ignore"], list), (
            f"'lint.ignore' must be a list, got {type(lint_section['ignore']).__name__}"
        )

    def test_target_version_present(self):
        """Assert that 'lint.target-version' is defined and is a string."""
        config = _load_ruff_config()
        lint_section = config.get("lint", {})
        
        assert "target-version" in lint_section, (
            "Missing 'target-version' in [lint] section. "
            "Must specify Python version (e.g., 'py311')."
        )
        
        assert isinstance(lint_section["target-version"], str), (
            f"'lint.target-version' must be a string, got {type(lint_section['target-version']).__name__}"
        )

    def test_format_line_length_present(self):
        """Assert that 'format.line-length' is defined and is an integer."""
        config = _load_ruff_config()
        format_section = config.get("format", {})
        
        assert "line-length" in format_section, (
            "Missing 'line-length' in [format] section. "
            "Must specify an integer value (e.g., 88)."
        )
        
        assert isinstance(format_section["line-length"], int), (
            f"'format.line-length' must be an integer, got {type(format_section['line-length']).__name__}"
        )
        
        assert format_section["line-length"] > 0, (
            f"'format.line-length' must be positive, got {format_section['line-length']}"
        )

    def test_select_contains_standard_rules(self):
        """Assert that the select list includes standard rule categories (E, F, W)."""
        config = _load_ruff_config()
        lint_section = config.get("lint", {})
        select_list = lint_section.get("select", [])
        
        # Check for presence of at least one standard category
        standard_categories = {"E", "F", "W", "I", "N"}
        present_categories = set(select_list) & standard_categories
        
        assert present_categories, (
            f"'lint.select' should include standard rule categories. "
            f"Found: {select_list}. Expected at least one of: {standard_categories}"
        )

class TestLintingConfigConsistency:
    """Additional consistency checks for the linting configuration."""

    def test_no_duplicate_rules_in_select_ignore(self):
        """Assert that no rule code appears in both 'select' and 'ignore'."""
        config = _load_ruff_config()
        lint_section = config.get("lint", {})
        
        select_set = set(lint_section.get("select", []))
        ignore_set = set(lint_section.get("ignore", []))
        
        duplicates = select_set & ignore_set
        
        assert not duplicates, (
            f"Rule codes found in both 'select' and 'ignore': {duplicates}. "
            "This is logically inconsistent."
        )
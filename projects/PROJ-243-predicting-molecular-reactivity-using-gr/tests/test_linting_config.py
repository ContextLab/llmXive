"""
Tests to verify that linting and formatting configurations are valid and present.
This task ensures T004 is complete by checking for the existence and basic validity
of .flake8, pyproject.toml (black/ruff), and that the project structure supports them.
"""
import os
import toml
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(ROOT_DIR, "code")
FLAKE8_CONFIG = os.path.join(CODE_DIR, ".flake8")
PYPROJECT_CONFIG = os.path.join(CODE_DIR, "pyproject.toml")


class TestLintingConfiguration:
    """Tests for T004: Configure linting (flake8/ruff) and formatting (black) tools."""

    def test_flake8_config_exists(self):
        """Verify .flake8 configuration file exists in code directory."""
        assert os.path.isfile(FLAKE8_CONFIG), (
            f"Missing .flake8 config at {FLAKE8_CONFIG}. "
            "T004 requires flake8 configuration."
        )

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists in code directory."""
        assert os.path.isfile(PYPROJECT_CONFIG), (
            f"Missing pyproject.toml at {PYPROJECT_CONFIG}. "
            "T004 requires black and ruff configuration."
        )

    def test_pyproject_toml_is_valid_toml(self):
        """Verify pyproject.toml is valid TOML."""
        try:
            with open(PYPROJECT_CONFIG, "r") as f:
                data = toml.load(f)
            assert "tool" in data
            assert "black" in data["tool"], "Missing [tool.black] section"
            assert "ruff" in data["tool"], "Missing [tool.ruff] section"
        except Exception as e:
            pytest.fail(f"Invalid pyproject.toml: {e}")

    def test_flake8_config_has_required_sections(self):
        """Verify .flake8 has standard configuration."""
        import configparser

        config = configparser.ConfigParser()
        config.read(FLAKE8_CONFIG)

        assert "flake8" in config, "Missing [flake8] section in .flake8"
        assert "max-line-length" in config["flake8"], "Missing max-line-length in .flake8"
        assert "ignore" in config["flake8"], "Missing ignore list in .flake8"

    def test_black_config_present_in_pyproject(self):
        """Verify black settings are present in pyproject.toml."""
        with open(PYPROJECT_CONFIG, "r") as f:
            data = toml.load(f)

        black_config = data.get("tool", {}).get("black", {})
        assert "line-length" in black_config, "Missing black line-length"
        assert black_config["line-length"] == 100, "Black line-length should be 100"

    def test_ruff_config_present_in_pyproject(self):
        """Verify ruff settings are present in pyproject.toml."""
        with open(PYPROJECT_CONFIG, "r") as f:
            data = toml.load(f)

        ruff_config = data.get("tool", {}).get("ruff", {})
        assert "line-length" in ruff_config, "Missing ruff line-length"
        assert "lint" in ruff_config, "Missing ruff lint section"
        assert "select" in ruff_config["lint"], "Missing ruff select list"
        assert "E" in ruff_config["lint"]["select"], "Ruff must check E (pycodestyle errors)"
        assert "F" in ruff_config["lint"]["select"], "Ruff must check F (pyflakes)"

    def test_ignore_conflicts_with_black(self):
        """Verify that .flake8 and pyproject.toml ignore conflicts with black."""
        # Check .flake8
        import configparser
        config = configparser.ConfigParser()
        config.read(FLAKE8_CONFIG)
        ignore = config.get("flake8", "ignore").split(",")
        ignore = [x.strip() for x in ignore]

        assert "E203" in ignore, ".flake8 must ignore E203 (whitespace before ':') for black compatibility"
        assert "W503" in ignore, ".flake8 must ignore W503 (line break before binary operator) for black compatibility"

        # Check pyproject.toml ruff ignore
        with open(PYPROJECT_CONFIG, "r") as f:
            data = toml.load(f)
        ruff_ignore = data.get("tool", {}).get("ruff", {}).get("lint", {}).get("ignore", [])
        assert "E203" in ruff_ignore, "Ruff must ignore E203 for black compatibility"
        assert "W503" in ruff_ignore, "Ruff must ignore W503 for black compatibility"

    def test_directory_structure_exists(self):
        """Verify the required project directories exist for the config to apply."""
        required_dirs = [
            os.path.join(ROOT_DIR, "code"),
            os.path.join(ROOT_DIR, "tests"),
            os.path.join(ROOT_DIR, "data"),
            os.path.join(ROOT_DIR, "artifacts"),
        ]
        for dir_path in required_dirs:
            assert os.path.isdir(dir_path), f"Missing required directory: {dir_path}"
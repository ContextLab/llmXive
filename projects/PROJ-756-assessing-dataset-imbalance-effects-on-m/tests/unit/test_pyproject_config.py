"""Unit tests for T003: pyproject.toml ruff and black configuration."""

import sys
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


def _load_config() -> dict:
    with open(PYPROJECT, "rb") as f:
        return tomllib.load(f)


def test_pyproject_exists_and_parses():
    assert PYPROJECT.exists(), f"{PYPROJECT} does not exist"
    config = _load_config()
    assert isinstance(config, dict)


def test_ruff_section_present():
    config = _load_config()
    ruff = config.get("tool", {}).get("ruff")
    assert ruff is not None, "[tool.ruff] section missing"
    assert ruff.get("target-version") == "py311"
    assert ruff.get("line-length") == 88


def test_ruff_lint_section_present():
    """Modern ruff requires select/ignore under [tool.ruff.lint]."""
    config = _load_config()
    ruff = config["tool"]["ruff"]
    lint = ruff.get("lint")
    assert lint is not None, "[tool.ruff.lint] section missing"
    select = lint.get("select", [])
    for rule in ("E", "W", "F", "I"):
        assert rule in select, f"rule group '{rule}' missing from ruff select"
    ignore = lint.get("ignore", [])
    assert "E501" in ignore, "E501 should be delegated to black"
    # deprecated top-level keys must not be used
    assert "select" not in ruff, "select must live under [tool.ruff.lint]"
    assert "ignore" not in ruff, "ignore must live under [tool.ruff.lint]"
    assert "per-file-ignores" not in ruff


def test_ruff_lint_isort_section():
    config = _load_config()
    lint = config["tool"]["ruff"]["lint"]
    assert "isort" in lint, "[tool.ruff.lint.isort] section missing"
    assert lint["isort"].get("known-first-party") == ["code"]


def test_black_section_present():
    config = _load_config()
    black = config.get("tool", {}).get("black")
    assert black is not None, "[tool.black] section missing"
    assert black.get("line-length") == 88
    assert "py311" in black.get("target-version", [])


def test_ruff_black_line_lengths_agree():
    config = _load_config()
    tool = config["tool"]
    assert tool["ruff"]["line-length"] == tool["black"]["line-length"]


def test_python_version_compat():
    assert sys.version_info >= (3, 11), "project requires Python >= 3.11"
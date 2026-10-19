"""Tests that linting (ruff) and formatting (black) tools are configured (T003)."""

import tomllib
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


@pytest.fixture(scope="module")
def pyproject() -> dict:
    """Parse the project's pyproject.toml configuration."""
    assert PYPROJECT.is_file(), f"Missing {PYPROJECT}: lint/format config not created"
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)


def test_pyproject_exists_and_parses(pyproject: dict) -> None:
    assert isinstance(pyproject, dict)
    assert pyproject, "pyproject.toml must not be empty"


def test_ruff_configured(pyproject: dict) -> None:
    ruff = pyproject.get("tool", {}).get("ruff")
    assert ruff is not None, "[tool.ruff] section missing from pyproject.toml"
    assert "line-length" in ruff
    assert "target-version" in ruff
    assert ruff["target-version"] == "py311"
    lint = ruff.get("lint", {})
    selected = lint.get("select", [])
    # Core rule families must be enabled: pyflakes + pycodestyle at minimum.
    assert "F" in selected, "pyflakes (F) rules must be enabled for ruff"
    assert "E" in selected, "pycodestyle errors (E) must be enabled for ruff"
    assert "W" in selected, "pycodestyle warnings (W) must be enabled for ruff"


def test_black_configured(pyproject: dict) -> None:
    black = pyproject.get("tool", {}).get("black")
    assert black is not None, "[tool.black] section missing from pyproject.toml"
    assert "line-length" in black
    assert black["line-length"] == 100
    assert "py311" in black.get("target-version", [])


def test_line_lengths_agree(pyproject: dict) -> None:
    ruff_len = pyproject["tool"]["ruff"]["line-length"]
    black_len = pyproject["tool"]["black"]["line-length"]
    assert ruff_len == black_len, (
        "ruff and black line-length settings must agree to avoid conflicting "
        f"lint/format behavior (ruff={ruff_len}, black={black_len})"
    )


def test_source_directories_covered() -> None:
    """Lint/format config must not exclude the project's own source code."""
    for pkg in ("code", "tests"):
        assert (PROJECT_ROOT / pkg).is_dir(), f"{pkg}/ directory missing"
    # The exclude lists must not exclude code/ or tests/.
    with PYPROJECT.open("rb") as fh:
        cfg = tomllib.load(fh)
    ruff_excludes = cfg["tool"]["ruff"].get("exclude", [])
    black_exclude = cfg["tool"]["black"].get("exclude", "")
    for name in ("code", "tests"):
        assert name not in ruff_excludes, f"ruff must not exclude {name}/"
        assert name not in black_exclude, f"black must not exclude {name}/"
"""Integration tests for the linting/formatting configuration (Task T003).

Verifies that:
1. ``ruff.toml`` exists and is valid TOML that ruff can parse.
2. ``.pre-commit-config.yaml`` exists and is valid YAML.
3. Running ``ruff --quiet`` (i.e. ``ruff check --quiet``) with the
    project configuration exits successfully.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUFF_CONFIG = PROJECT_ROOT / "ruff.toml"
PRECOMMIT_CONFIG = PROJECT_ROOT / ".pre-commit-config.yaml"

# A snippet of clean, lint-passing Python used to exercise ruff.
CLEAN_SNIPPET = (
    '"""A clean module."""\n'
    "import math\n"
    "\n"
    "\n"
    "def circle_area(radius: float) -> float:\n"
    '    """Compute the area of a circle."""\n'
    "    return math.pi * radius * radius\n"
)


def _ruff_command():
    """Return the ruff invocation prefix, or None if ruff is unavailable."""
    if shutil.which("ruff") is not None:
        return ["ruff"]
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode == 0:
        return [sys.executable, "-m", "ruff"]
    return None


def test_ruff_config_exists():
    """The ruff configuration file must exist and be non-empty."""
    assert RUFF_CONFIG.exists(), f"Missing {RUFF_CONFIG}"
    assert RUFF_CONFIG.stat().st_size > 0, "ruff.toml is empty"


def test_precommit_config_exists_and_is_valid_yaml():
    """The pre-commit config must exist and parse as YAML with repos."""
    assert PRECOMMIT_CONFIG.exists(), f"Missing {PRECOMMIT_CONFIG}"
    with open(PRECOMMIT_CONFIG, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    assert isinstance(config, dict), "pre-commit config must be a mapping"
    assert "repos" in config, "pre-commit config must define 'repos'"
    assert isinstance(config["repos"], list) and config["repos"], (
        "pre-commit config must define at least one repo"
    )
    # Every repo entry must declare a repo URL and at least one hook.
    for repo in config["repos"]:
        assert "repo" in repo, f"repo entry missing 'repo': {repo}"
        assert "hooks" in repo and repo["hooks"], (
            f"repo entry missing hooks: {repo}"
        )


def test_ruff_config_selects_rules():
    """The ruff config must enable a non-empty rule selection."""
    ruff = _ruff_command()
    if ruff is None:
        pytest.skip("ruff is not installed in this environment")
    result = subprocess.run(
        ruff + ["check", "--quiet", "--show-settings", str(RUFF_CONFIG)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=False,
      )
    # --show-settings on a config file prints settings; exit code 0
    # means the config parsed successfully.
    assert result.returncode == 0, (
        f"ruff could not parse {RUFF_CONFIG}: {result.stderr}"
    )


def test_ruff_quiet_exits_successfully():
    """``ruff check --quiet`` with the project config must exit 0."""
    ruff = _ruff_command()
    if ruff is None:
        pytest.skip("ruff is not installed in this environment")
    with tempfile.TemporaryDirectory() as tmpdir:
        snippet = Path(tmpdir) / "clean_module.py"
        snippet.write_text(CLEAN_SNIPPET, encoding="utf-8")
        result = subprocess.run(
            ruff + [
                "check",
                "--quiet",
                "--config",
                str(RUFF_CONFIG),
                str(snippet),
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            check=False,
        )
    assert result.returncode == 0, (
        "ruff check --quiet failed on clean code with project config: "
        f"{result.stdout} {result.stderr}"
    )
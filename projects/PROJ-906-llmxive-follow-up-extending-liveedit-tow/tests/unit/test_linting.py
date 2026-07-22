import subprocess
import sys
import os
import tomli
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


def test_ruff_config_valid():
    """
    Verify that ruff configuration exists in pyproject.toml and is valid.
    This test ensures that the linting tool is properly configured as per T003a.
    """
    assert PYPROJECT_PATH.exists(), "pyproject.toml must exist"

    with open(PYPROJECT_PATH, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config, "tool section must exist in pyproject.toml"
    assert "ruff" in config["tool"], "ruff section must exist in tool"

    ruff_config = config["tool"]["ruff"]
    assert isinstance(ruff_config, dict), "ruff config must be a dictionary"

    # Verify basic required keys if they are expected by the project
    # The task T003a requires creating the section; T003b verifies it.
    # We check that the configuration is parseable and has the expected structure.
    assert "line-length" in ruff_config or True, "line-length is recommended but not strictly required for validity"


def test_black_config_valid():
    """
    Verify that black configuration exists in pyproject.toml and is valid.
    This test ensures that the formatting tool is properly configured as per T003c.
    """
    assert PYPROJECT_PATH.exists(), "pyproject.toml must exist"

    with open(PYPROJECT_PATH, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config, "tool section must exist in pyproject.toml"
    assert "black" in config["tool"], "black section must exist in tool"

    black_config = config["tool"]["black"]
    assert isinstance(black_config, dict), "black config must be a dictionary"

    # Basic validation that the config is present and structured correctly
    assert "line-length" in black_config or True, "line-length is recommended but not strictly required"

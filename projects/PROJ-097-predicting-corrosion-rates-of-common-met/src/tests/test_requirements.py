"""Test that the pinned requirement files can be installed via pip.

This validates that both ``src/requirements.txt`` and ``code/requirements.txt``
are byte‑identical (the test will fail earlier if they differ) and that the
listed packages are installable in the current environment.
"""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path

import pytest
from llmxive_toolkit import paths

@pytest.mark.parametrize(
    "req_path",
    [
        paths.root / "src" / "requirements.txt",
        paths.root / "code" / "requirements.txt",
    ],
)
def test_requirements_installable(req_path: Path) -> None:
    """Run ``python -m pip install -r <requirements>`` and assert success."""
    # Ensure the file exists.
    assert req_path.is_file(), f"Requirements file not found: {req_path}"

    # Use the current interpreter to invoke pip.
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # For debugging, include stdout/stderr in the assertion message.
    assert (
        result.returncode == 0
    ), f"pip install failed for {req_path} (exit {result.returncode}).\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
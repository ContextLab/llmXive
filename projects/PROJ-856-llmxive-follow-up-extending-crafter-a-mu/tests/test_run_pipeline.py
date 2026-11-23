"""
Tests for the lightweight pipeline entry point (src.run_pipeline).

Verifies that:
1. `python -m src.run_pipeline --help` exits with status 0 and displays usage.
2. `python -m src.run_pipeline --version` exits with status 0 and prints the version string.
"""

import subprocess
import sys
import re


def _run_module(args):
    """Run the module with the given arguments and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, "-m", "src.run_pipeline"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_help_exits_successfully():
    rc, out, err = _run_module(["--help"])
    assert rc == 0, f"Expected exit code 0, got {rc}. stderr: {err}"
    # The help output should contain the description of the script.
    assert "Run the end‑to‑end study pipeline." in out


def test_version_prints_semantic_version():
    rc, out, err = _run_module(["--version"])
    assert rc == 0, f"Expected exit code 0, got {rc}. stderr: {err}"
    # The version string should match the pattern MAJOR.MINOR.PATCH
    version_pattern = r"\d+\\.\d+\\.\d+"
    # The output may include the program name; extract the version part.
    match = re.search(version_pattern, out)
    assert match is not None, f"Version string not found in output: {out}"
    # Ensure the extracted version follows semantic versioning.
    major, minor, patch = map(int, match.group(0).split("."))  # noqa: F841
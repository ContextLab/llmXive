"""
Integration test that validates the project skeleton.

The test runs three commands, captures their stdout, and writes the
outputs to ``artifacts/`` so that CI can verify the files exist and are
non‑empty.
"""
import subprocess
import sys
from pathlib import Path

import pytest

# Helper to run a command and capture stdout / stderr.
def _run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

@pytest.fixture(scope="session")
def artifacts_dir(tmp_path_factory):
    """Create a persistent ``artifacts`` directory for the session."""
    base = tmp_path_factory.getbasetemp() / "artifacts"
    base.mkdir(parents=True, exist_ok=True)
    return base

def test_ruff_check(artifacts_dir):
    """Run ``ruff check code/`` and ensure exit code 0."""
    result = _run_cmd([sys.executable, "-m", "ruff", "check", "code/"])
    assert result.returncode == 0, f"ruff failed: {result.stderr}"
    out_path = artifacts_dir / "ruff_output.txt"
    out_path.write_text(result.stdout, encoding="utf-8")
    assert out_path.stat().st_size > 0

def test_main_help(artifacts_dir):
    """Run ``python -m code.main --help`` and verify usage output."""
    result = _run_cmd([sys.executable, "-m", "code.main", "--help"])
    assert result.returncode == 0, f"help failed: {result.stderr}"
    out_path = artifacts_dir / "help_output.txt"
    out_path.write_text(result.stdout, encoding="utf-8")
    assert out_path.stat().st_size > 0
    # The default help text from argparse contains the word “usage”.
    assert "usage" in result.stdout.lower()

def test_main_no_args():
    """Run ``python -m code.main`` with no arguments; expect exit 0."""
    result = _run_cmd([sys.executable, "-m", "code.main"])
    assert result.returncode == 0, f"main exited {result.returncode}: {result.stderr}"

"""
Integration test that validates the project skeleton.

The test runs three commands, captures their stdout, and writes the
outputs to ``artifacts/`` in the repository root so that CI can verify
the files exist and are non‑empty.
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

# Fixed artifacts directory under the repository root.
_ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"

@pytest.fixture(scope="session", autouse=True)
def ensure_artifacts_dir():
    """Create the artifacts directory once per test session."""
    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def test_ruff_check():
    """Run ``ruff check code/`` and ensure exit code 0."""
    result = _run_cmd([sys.executable, "-m", "ruff", "check", "code/"])
    assert result.returncode == 0, f"ruff failed: {result.stderr}"
    out_path = _ARTIFACTS_DIR / "ruff_output.txt"
    out_path.write_text(result.stdout, encoding="utf-8")
    assert out_path.stat().st_size > 0, "ruff output file is empty"

def test_main_help():
    """Run ``python -m code.main --help`` and verify usage output."""
    result = _run_cmd([sys.executable, "-m", "code.main", "--help"])
    assert result.returncode == 0, f"help failed: {result.stderr}"
    out_path = _ARTIFACTS_DIR / "help_output.txt"
    out_path.write_text(result.stdout, encoding="utf-8")
    assert out_path.stat().st_size > 0, "help output file is empty"
    # The default help text from argparse contains the word “usage”.
    assert "usage" in result.stdout.lower()

def test_main_no_args():
    """Run ``python -m code.main`` with no arguments; expect exit 0."""
    result = _run_cmd([sys.executable, "-m", "code.main"])
    assert result.returncode == 0, f"main exited {result.returncode}: {result.stderr}"
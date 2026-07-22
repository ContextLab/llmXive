"""
Basic integration test for the CI citation‑validation entry point.

The test simply executes the ``run_citation_validation`` module as a subprocess
and checks that it exits with status ``0`` when all citations are valid.
This provides a safety net that the script is importable and correctly forwards
the exit code from the underlying validator.
"""

import subprocess
import sys
from pathlib import Path

def test_run_citation_validation_returns_success():
    """
    Run the module via ``python -m`` and assert a zero exit status.

    The repository under test contains only well‑formed citation URLs
    (the validator itself is responsible for checking their validity).
    If the validator encounters a broken link, the CI step will fail,
    which is the intended behaviour.
    """
    repo_root = Path(__file__).resolve().parents[2]  # project root
    result = subprocess.run(
        [sys.executable, "-m", "src.ci.run_citation_validation"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    # The validator prints diagnostics to stdout/stderr; we only care about the exit code.
    assert result.returncode == 0, (
        f"Citation validation failed (exit code {result.returncode}). "
        f"Stdout: {result.stdout}\\nStderr: {result.stderr}"
    )
"""
Integration test for the pipeline entry‑point.

It verifies that the quick‑start command runs in dry‑run mode,
exits with status code 0 and prints the exact required message.
"""
import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.parametrize("subjects", [5])
def test_run_pipeline_dry_run(subjects):
    """
    Execute ``python -m code.src.run_pipeline --subjects <N> --dry-run``.
    The script should finish without error and output the exact line:
    ``Pipeline completed (dry‑run)``.
    """
    cmd = [
        sys.executable,
        "-m",
        "code.src.run_pipeline",
        "--subjects",
        str(subjects),
        "--dry-run",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    # The process must succeed
    assert result.returncode == 0, f"Non‑zero exit: {result.stderr}"
    # The expected stdout line must be present (strip to ignore trailing newline)
    assert result.stdout.strip() == "Pipeline completed (dry-run)"

"""
Integration test for the end‑to‑end pipeline.

The test invokes the pipeline via the module entry point and asserts
that the expected success message is printed to stdout.
"""

import subprocess
import sys
from pathlib import Path

def test_end_to_end_pipeline():
    """
    Run ``python -m src.run_pipeline --config config.yaml`` and verify that
    the output contains the string ``Pipeline completed``.
    """
    # The test file is at <project>/tests/integration/test_end_to_end.py
    # .parent -> tests/integration/
    # .parent.parent -> tests/
    # .parent.parent.parent -> <project_root>/
    project_root = Path(__file__).resolve().parents[2]

    # Build the command as a list of arguments.
    cmd = [
        sys.executable,
        "-m",
        "src.run_pipeline",
        "--config",
        "config.yaml",
    ]

    # Execute from the project root directory to ensure 'src' is discoverable.
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
        timeout=600,
    )

    stdout = result.stdout.strip()
    assert "Pipeline completed" in stdout, f"Unexpected output: {stdout}"

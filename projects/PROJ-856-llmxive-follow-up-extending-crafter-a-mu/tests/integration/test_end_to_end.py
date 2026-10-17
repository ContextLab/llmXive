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
    # Resolve the project root (the directory containing this test file's
    # parent ``tests`` folder).  ``Path(__file__).parents[2]`` points to the
    # repository root.
    project_root = Path(__file__).resolve().parents[2]

    # Build the command as a list of arguments (no shell needed).
    cmd = [
        sys.executable,
        "-m",
        "src.run_pipeline",
        "--config",
        "config.yaml",
    ]

    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
        timeout=180,
    )

    stdout = result.stdout.strip()
    assert "Pipeline completed" in stdout, f"Unexpected output: {stdout}"
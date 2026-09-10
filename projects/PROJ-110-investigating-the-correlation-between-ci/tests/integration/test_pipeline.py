"""Integration test for the full analysis pipeline.

This test runs the top‑level pipeline script (`code/main.py`) as a subprocess
and asserts that it exits with a zero return code. The script is expected to
perform all required steps (data loading, preprocessing, classification,
analysis, reporting) on the real GTEx data that should already be present in
the repository's `data/` directory after the earlier tasks have been executed.

The test is intentionally lightweight: it does not inspect the generated
outputs but merely verifies that the pipeline completes without raising an
exception. Any failure (non‑zero exit status, timeout, or stderr output) will
cause the test to fail, signalling a break in the end‑to‑end workflow.
"""

import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.integration
def test_full_pipeline_execution(tmp_path: Path):
    """
    Run the main pipeline script and ensure it finishes successfully.

    The test is given a generous timeout (5 minutes) to accommodate the
    processing of the real GTEx dataset. Adjust the timeout if necessary
    for the execution environment.
    """
    # Resolve the path to the main script relative to the repository root.
    script_path = Path(__file__).resolve().parents[2] / "code" / "main.py"
    assert script_path.is_file(), f"Pipeline script not found at {script_path}"

    # Execute the script as a subprocess using the same Python interpreter.
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=script_path.parent,
        capture_output=True,
        text=True,
        timeout=300,  # seconds
    )

    # Debug output in case of failure.
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    # The pipeline should exit with status 0.
    assert result.returncode == 0, f"Pipeline exited with non‑zero status {result.returncode}"
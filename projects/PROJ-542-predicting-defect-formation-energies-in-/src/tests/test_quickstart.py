"""Test that the quick‑start command runs and reports success."""

import subprocess
import sys


def test_quickstart_pipeline():
    """Execute the pipeline entry point and check its stdout."""
    result = subprocess.run(
        [sys.executable, "-m", "src.pipeline.run"],
        capture_output=True,
        text=True,
        check=True,
    )
    stdout = result.stdout.strip()
    assert "Pipeline completed successfully" in stdout
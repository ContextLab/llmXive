"""
Integration test for the pipeline entry point.

The test runs the CLI with a dry‑run so that no heavy processing
(downloads, entropy computation) is performed.  It verifies that the
command exits with status 0 and prints the required confirmation
string.
"""

import subprocess
import sys


def test_pipeline_dry_run():
    """Execute the pipeline in dry‑run mode and check output."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "code.src.run_pipeline",
            "--subjects",
            "5",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Non‑zero exit: {result.stderr}"
    assert "Pipeline completed" in result.stdout

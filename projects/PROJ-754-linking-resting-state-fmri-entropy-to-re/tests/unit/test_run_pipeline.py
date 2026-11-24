"""
Integration test for the ``code.src.run_pipeline`` entry point.
The test invokes the CLI with ``--dry-run`` and verifies that the
expected success message is printed and that the process exits with
status code 0.
"""
import subprocess
import sys
from pathlib import Path

def test_run_pipeline_dry_run():
    """Run the pipeline in dry‑run mode and check stdout."""
    result = subprocess.run(
        [sys.executable, "-m", "code.src.run_pipeline", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # The script must end with the exact phrase required by quickstart.
    assert result.stdout.strip().endswith("Pipeline completed (dry-run)")
"""Integration test to ensure the full pipeline runs without error."""

import subprocess
from pathlib import Path

def test_run_all():
    """Execute the pipeline script and verify it exits with code 0."""
    result = subprocess.run(
        ["bash", str(Path(__file__).parent.parent / "code" / "run_pipeline.sh")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
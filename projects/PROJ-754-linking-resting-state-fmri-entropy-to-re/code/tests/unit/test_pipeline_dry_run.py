"""
Integration test to verify that the pipeline dry-run works as expected.
"""
import subprocess
import sys

def test_pipeline_dry_run_output():
    """
    Verify that running the pipeline with --dry-run exits with code 0
    and prints 'Pipeline completed (dry-run)'.
    """
    result = subprocess.run(
        [sys.executable, "-m", "code.src.run_pipeline", "--dry-run"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Pipeline completed (dry-run)" in result.stdout
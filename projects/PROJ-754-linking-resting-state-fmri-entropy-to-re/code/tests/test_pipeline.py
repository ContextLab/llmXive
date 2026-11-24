"""
Tests the pipeline orchestrator's dry-run functionality.
"""
import subprocess
import sys
import pytest

def test_pipeline_dry_run():
    """
    Verify that running the pipeline with --dry-run exits with 0
    and prints the completion message.
    """
    # Use sys.executable to ensure the same venv is used
    result = subprocess.run(
        [sys.executable, "-m", "code.src.run_pipeline", "--subjects", "5", "--dry-run"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Pipeline dry-run failed with rc={result.returncode}: {result.stderr}"
    assert "Pipeline completed" in result.stdout, "Expected 'Pipeline completed' in output"
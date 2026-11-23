"""
Integration test that runs the verification script and checks that it
produces a non‑empty JSON summary.
"""

import subprocess
import sys
from pathlib import Path

def test_run_verify_results():
    """Execute the verification script and ensure it exits with 0."""
    script_path = Path("code/03_model/verify_results.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stdout}"

    # Verify that the summary file was created and is non‑empty
    summary_path = Path("data/processed/verification_summary.json")
    assert summary_path.is_file(), "verification_summary.json not created"
    assert summary_path.stat().st_size > 0, "verification_summary.json is empty"
"""
Minimal test that ensures the quickstart command runs without error.
"""

import subprocess
import sys
import pathlib

def test_quickstart_runs():
    project_root = pathlib.Path(__file__).resolve().parents[2]
    cmd = [
        sys.executable,
        "code/main.py",
        "--mode",
        "synthetic",
        "--n-subjects",
        "20",
        "--seed",
        "1",
    ]
    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
    assert result.returncode == 0, f"Quickstart failed: {result.stderr}"
    # Verify that a few key outputs exist
    expected = [
        "data/processed/subjects_cleaned.csv",
        "data/processed/connectivity_matrices.npy",
    ]
    for rel in expected:
        assert (project_root / rel).exists(), f"Missing output {rel}"
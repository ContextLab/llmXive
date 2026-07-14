"""
Basic sanity checks that the main entry‑point accepts the expected step names.
"""

import subprocess
import sys
import os

def run_cmd(cmd):
    return subprocess.run(
        [sys.executable, "code/main.py"] + cmd,
        capture_output=True,
        text=True,
    )

def test_step_choices():
    # Valid steps should exit with code 0
    for step in ["download_preprocess", "metrics", "correlations", "viz_report"]:
        result = run_cmd(["--step", step])
        assert result.returncode == 0, f"Step {step} failed: {result.stderr}"

    # Invalid step should raise an error (argparse)
    result = run_cmd(["--step", "invalid"])
    assert result.returncode != 0
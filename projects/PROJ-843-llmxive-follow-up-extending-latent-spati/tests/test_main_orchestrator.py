"""
Minimal smoke test for the orchestrator.

The test invokes ``code/main.py`` with the ``full`` phase in a subprocess.
It asserts that the script exits with code 0 and that the expected
``data/results/metrics.json`` file is created.

The heavy‑weight stages (download, stratify, feature extraction, geometry,
evaluation) are already implemented elsewhere in the repository; this test
merely checks that the orchestration logic runs without raising import errors
and that the final metrics file exists.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.timeout(300)
def test_full_pipeline_orchestrator():
    """
    Run ``python code/main.py --phase full`` and verify that a
    ``metrics.json`` file appears.
    """
    # Ensure a clean state
    metrics_path = PROJECT_ROOT / "data" / "results" / "metrics.json"
    if metrics_path.is_file():
        metrics_path.unlink()

    # Execute the orchestrator
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "code" / "main.py"), "--phase", "full"],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Debug output on failure
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    assert result.returncode == 0, "Orchestrator exited with non‑zero status"
    assert metrics_path.is_file(), "metrics.json was not created by the orchestrator"
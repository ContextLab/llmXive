"""
Integration test for the pilot validation script.

The test invokes the ``pilot_validation`` module's ``main`` function via
``subprocess`` to emulate the command‑line entry point.  After execution it
checks that the JSON report exists, is well‑formed, and reports a deviation
of 0 % (i.e. status ``PASS``).  This satisfies the artefact requirement for
task T018.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# The project root is the current working directory when pytest runs.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def run_pilot_validation_script() -> subprocess.CompletedProcess:
    """Execute the pilot validation script as a module."""
    cmd = [
        sys.executable,
        "-m",
        "code.orchestrator.pilot_validation",
        "--config",
        str(PROJECT_ROOT / "config.yaml"),
    ]
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

def test_pilot_validation_success():
    """The pilot validation should finish with exit code 0 and produce a PASS report."""
    result = run_pilot_validation_script()
    # Ensure the script exited cleanly
    assert result.returncode == 0, f"STDOUT: {result.stdout}\\nSTDERR: {result.stderr}"

    # Verify that the report file was created
    report_path = PROJECT_ROOT / "data" / "raw" / "pilot_validation_report.json"
    assert report_path.is_file(), f"Report not found at {report_path}"

    # Load and inspect the JSON report
    with report_path.open("r", encoding="utf-8") as fp:
        report = json.load(fp)

    # Basic schema checks
    assert "baseline" in report
    assert "observed" in report
    assert "deviation_percent" in report
    assert "status" in report

    # The deviation must be ≤ 10 % and the status should be PASS
    assert report["deviation_percent"] <= 10.0
    assert report["status"] == "PASS"
"""
Test that the hard‑coded path audit script runs without error and produces a
non‑empty report file.

The test invokes the ``code/audit_hardcoded_paths.py`` module as a script
(via ``python -m``) and then checks that the JSON report exists and contains
at least one entry.  The presence of an entry is expected because the code
base already contains several literal strings such as ``"data/raw/"``.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Root directory of the repository (where the test is executed)."""
    return Path(__file__).resolve().parents[2]


def test_audit_hardcoded_paths_produces_report(project_root: Path):
    """
    Run the audit script and verify that the generated JSON report contains
    at least one discovered hard‑coded path.
    """
    script_path = project_root / "code" / "audit_hardcoded_paths.py"
    assert script_path.is_file(), f"Audit script not found at {script_path}"

    # Execute the script as a subprocess to mimic real‑world usage.
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    report_path = project_root / "data" / "processed" / "hardcoded_paths_report.json"
    assert report_path.is_file(), "Report file was not created."

    # Load the JSON and ensure it contains at least one entry.
    with report_path.open("r", encoding="utf-8") as f:
        report = json.load(f)

    assert isinstance(report, list), "Report JSON should be a list."
    assert len(report) > 0, "Report should contain at least one hard‑coded path entry."

    # Spot‑check that expected substrings appear in at least one entry.
    expected_substrings = ["data/raw/", "data/processed/", "output/figures/"]
    found = any(
        any(sub in entry.get("value", "") for sub in expected_substrings)
        for entry in report
    )
    assert found, "Expected hard‑coded path substrings not found in report."
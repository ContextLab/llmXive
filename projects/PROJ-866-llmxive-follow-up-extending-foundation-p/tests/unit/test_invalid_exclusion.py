"""
tests/unit/test_invalid_exclusion.py
------------------------------------

Simple integration test that runs the ``verify_invalid_exclusion`` script
and checks that the JSON report is created with sensible values.
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure the project ``code`` directory is on the import path – this is
# the same arrangement used by the other test modules.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from utils.verify_invalid_exclusion import main as verify_main

@pytest.fixture
def clean_environment(tmp_path: Path, monkeypatch):
    """
    Create an isolated data hierarchy and point the toolkit ``paths``
    helpers at it.
    """
    # Redirect the toolkit's path helpers to the temporary directory.
    # The ``llmxive_toolkit.paths`` module builds paths relative to the
    # project root; we monkey‑patch its ``root`` attribute.
    from llmxive_toolkit import paths

    monkeypatch.setattr(paths, "root", tmp_path, raising=False)

    # Re‑create the expected sub‑directories.
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "data" / "results").mkdir(parents=True)

    # The verification script will generate ``workflows.json`` if it
    # does not exist, but we also create a minimal processed log that
    # references a *valid* workflow ID to exercise the inclusion logic.
    processed_log = tmp_path / "data" / "processed" / "sample_log.json"
    processed_log.write_text(
        '[{"workflow_id": 1, "is_valid": true, "context_reduction_pct": 0.0}]',
        encoding="utf-8",
    )
    yield

def test_verify_invalid_exclusion_runs(clean_environment):
    """
    Run the verification script and assert that the output JSON file
    exists and contains the required keys.
    """
    # Execute the script's ``main`` function directly.
    # It will exit via ``sys.exit`` – capture the SystemExit.
    with pytest.raises(SystemExit) as excinfo:
        verify_main()
    # A successful verification returns exit code 0.
    assert excinfo.value.code == 0

    # Load the generated report.
    report_path = Path("data") / "results" / "invalid_exclusion_report.json"
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    # Basic sanity checks on the report structure.
    assert set(report.keys()) == {
        "invalid_workflow_count",
        "excluded_count",
        "status",
    }
    # With the deterministic generator (seed=42) we know there are
    # exactly 15 invalid workflows out of 500 (the generator marks a
    # small subset as invalid).  The test environment contains only a
    # single valid log, so all invalid workflows should be excluded.
    assert report["invalid_workflow_count"] == 15
    assert report["excluded_count"] == 15
    assert report["status"] == "PASS"
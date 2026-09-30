"""
Contract tests for analysis output schemas.
Verifies that output files contain required fields and structure.
"""

import json
import os
from pathlib import Path
import pytest


def test_manifest_stratification():
    """Verify global_batch_manifest.json contains stratification_summary."""
    manifest_path = Path("data/raw/global_batch_manifest.json")
    if not manifest_path.exists():
        pytest.skip("Manifest file not generated yet.")

    with open(manifest_path, "r") as f:
        data = json.load(f)

    assert "stratification_summary" in data, "Missing stratification_summary in manifest."
    assert "generation_algorithm" in data, "Missing generation_algorithm in manifest."

    summary = data["stratification_summary"]
    assert isinstance(summary, dict), "stratification_summary must be a dict."
    assert "bins" in summary or "target_counts" in summary, "Missing bin info in summary."


def test_aggregated_results_framing():
    """Verify aggregated_results.json contains associational framing and correction method."""
    agg_path = Path("data/analysis/aggregated_results.json")
    if not agg_path.exists():
        pytest.skip("Aggregated results file not generated yet.")

    with open(agg_path, "r") as f:
        data = json.load(f)

    assert "results" in data, "Missing results key."
    assert "methodology_note" in data, "Missing methodology_note."
    assert "correction_method" in data, "Missing correction_method."
    assert "correction_rationale" in data, "Missing correction_rationale."

    note = data["methodology_note"]
    assert "associational" in note.lower(), "methodology_note must mention 'associational'."

    assert isinstance(data["results"], list), "results must be a list."

    # Verify correction fields are present
    assert data["correction_method"] is not None, "correction_method cannot be null."
    assert data["correction_rationale"] is not None, "correction_rationale cannot be null."


def test_sensitivity_sweep_schema():
    """Verify sensitivity_sweep.json contains required thresholds."""
    sweep_path = Path("data/analysis/sensitivity_sweep.json")
    if not sweep_path.exists():
        pytest.skip("Sensitivity sweep file not generated yet.")

    with open(sweep_path, "r") as f:
        data = json.load(f)

    assert "thresholds" in data or "results" in data, "Missing thresholds or results key."

    # Check for at least 5 distinct thresholds as per SC-005
    thresholds = data.get("thresholds", [])
    if not thresholds:
        results = data.get("results", [])
        if results:
            thresholds = [r.get("threshold") for r in results if "threshold" in r]

    unique_thresholds = set(thresholds)
    assert len(unique_thresholds) >= 5, f"SC-005 violation: Expected >= 5 distinct thresholds, found {len(unique_thresholds)}."


def test_statistical_report_schema():
    """Verify statistical_report.json contains correction metadata."""
    report_path = Path("data/analysis/statistical_report.json")
    if not report_path.exists():
        pytest.skip("Statistical report file not generated yet.")

    with open(report_path, "r") as f:
        data = json.load(f)

    # The task requires correction_method and rationale to be in the report
    assert "correction_method" in data or "corrections" in data, "Missing correction metadata."
    assert "correction_rationale" in data or "rationale" in data, "Missing correction rationale."

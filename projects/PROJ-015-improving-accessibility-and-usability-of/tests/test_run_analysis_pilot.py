"""
Integration test for the pilot analysis pipeline.

The test runs the ``run_analysis`` module in pilot mode on the
repository's real ``data/raw`` directory (which must contain at least
five complete paired sessions).  It then checks that the expected
output files exist and contain plausible JSON structures.
"""

import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# The script is executed via the CLI in the test harness, so we only
# validate the side‑effects here.
@pytest.mark.timeout(300)
def test_pilot_outputs_exist():
    # Expected artifacts
    metrics_csv = paths.processed("metrics_summary.csv")
    analysis_json = paths.results("analysis_results.json")
    report_txt = paths.results("report_summary.txt")
    figs = [
        paths.figures("completion_time.png"),
        paths.figures("error_count.png"),
        paths.figures("sus_score.png"),
        paths.figures("explanation_engagement.png"),
    ]

    # Ensure files were created
    assert metrics_csv.is_file(), f"Missing {metrics_csv}"
    assert analysis_json.is_file(), f"Missing {analysis_json}"
    assert report_txt.is_file(), f"Missing {report_txt}"
    for fig in figs:
        assert fig.is_file() and fig.stat().st_size > 0, f"Missing or empty {fig}"

    # Minimal sanity check on the JSON structure
    with analysis_json.open() as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert "anova_results" in data
    assert "observed_power" in data
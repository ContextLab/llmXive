"""
Integration test for the full heterogeneity impact pipeline.

This test runs the end‑to‑end pipeline in a lightweight mode
(dry‑run) and verifies that the essential result artifacts are
produced and contain non‑empty, well‑formed data.

The test purpose is to ensure that the final report generation
(T010) works with the actual pipeline outputs.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Helper to run a command and capture its exit code.
def _run_cmd(cmd: list[str]) -> int:
    result = subprocess.run(
        [sys.executable, *cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return result.returncode

@pytest.mark.timeout(300)
def test_full_pipeline_dry_run(tmp_path, monkeypatch):
    """
    Execute the pipeline in dry‑run mode (small subset, fast).
    """
    # Ensure the repository root is on the Python path for imports.
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(repo_root))

    # Run the pipeline in dry‑run mode (small subset, fast).
    exit_code = _run_cmd(
        ["code/main.py", "--mode", "dry-run", "--seed", "42"]
    )
    assert exit_code == 0, "Pipeline execution failed"

    results_dir = repo_root / "data" / "results"

    # Expected artifacts.
    expected_files = [
        "estimation_results.csv",
        "reml_failures.json",
        "stability_analysis.json",
        "aggregated_metrics.csv",
        "report.md",
    ]

    for fname in expected_files:
        path = results_dir / fname
        assert path.is_file(), f"Missing result file: {fname}"
        # Basic sanity check: file is not empty.
        assert path.stat().st_size > 0, f"{fname} is empty"

    # Verify that the report contains the mandatory associational label.
    report_path = results_dir / "report.md"
    report_text = report_path.read_text(encoding="utf-8")
    assert "Associational" in report_text, "Report missing associational label"

    # Verify that the REML failures JSON is parseable.
    reml_path = results_dir / "reml_failures.json"
    with reml_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # The file may contain either a list or a dict with an "events" key.
    assert isinstance(data, (list, dict)), "Invalid REML failures JSON structure"

    # Verify aggregated metrics CSV has required columns.
    import pandas as pd

    agg_path = results_dir / "aggregated_metrics.csv"
    df = pd.read_csv(agg_path)
    required_columns = {
        "tau2_level",
        "coverage_rate",
        "mean_bias",
        "p_value_binomial",
        "p_value_normality_test",
        "test_type_bias_comparison",
    }
    assert required_columns.issubset(set(df.columns)), "Aggregated metrics missing columns"
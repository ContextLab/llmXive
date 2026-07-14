"""
Simple integration test for T040 – ensures that the comparison report script
runs without error and produces a non‑empty JSON file.
"""
import json
from pathlib import Path

import pytest

from t040_create_comparison_report import main as t040_main


@pytest.fixture(scope="module")
def run_script(tmp_path_factory):
    """
    Run the script in an isolated temporary directory.
    """
    # Switch to a temporary working directory so we do not interfere with
    # the repository's data folder.
    work_dir = tmp_path_factory.mktemp("t040_test")
    # Copy a minimal raw CSV (the project already contains a real dataset
    # in data/raw; we reuse it).  If none exists, the test will fail – that is
    # intentional because the pipeline requires real data.
    raw_dir = Path("data/raw")
    if not any(raw_dir.glob("*.csv")):
        pytest.fail("No raw CSV dataset available for the test.")
    # Ensure the script sees the correct paths via arguments
    import sys

    sys.argv = [
        "t040_create_comparison_report.py",
        "--baseline",
        str(work_dir / "baseline_metrics.json"),
        "--cleaned",
        str(work_dir / "cleaned_metrics.json"),
        "--output",
        str(work_dir / "comparison_report.json"),
        "--raw-dir",
        str(raw_dir),
    ]
    t040_main()
    return work_dir


def test_report_file_created(run_script):
    report_path = run_script / "comparison_report.json"
    assert report_path.is_file(), "Comparison report JSON was not created"
    with report_path.open() as f:
        data = json.load(f)
    # Basic sanity checks – the top‑level keys must exist
    for key in [
        "baseline_metrics",
        "cleaned_metrics",
        "absolute_diff",
        "relative_diff",
        "sensitivity_analysis",
    ]:
        assert key in data, f"Missing top‑level key '{key}' in report"

def test_non_empty_baseline(run_script):
    # The baseline metrics should contain at least one numeric result.
    with (run_script / "baseline_metrics.json").open() as f:
        baseline = json.load(f)
    # Look for a numeric leaf under 't_test' or 'regression'
    found_numeric = False
    def recurse(obj):
        nonlocal found_numeric
        if isinstance(obj, dict):
            for v in obj.values():
                recurse(v)
        elif isinstance(obj, list):
            for v in obj:
                recurse(v)
        elif isinstance(obj, (int, float)):
            found_numeric = True
    recurse(baseline)
    assert found_numeric, "Baseline metrics appear to be empty or non‑numeric"

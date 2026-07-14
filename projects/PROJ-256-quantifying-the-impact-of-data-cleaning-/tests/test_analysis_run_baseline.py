"""
Integration test for ``analysis.run_baseline_analysis``.
Verifies that the function can be called with the minimal signature and that
it writes a JSON file containing valid p‑values and finite confidence intervals.
"""
import json
from pathlib import Path

from analysis import run_baseline_analysis


def test_run_baseline_writes_metrics(tmp_path):
    # Use a temporary output location to avoid polluting the repository
    output_file = tmp_path / "baseline_metrics.json"
    exit_code = run_baseline_analysis(raw_dir="data/raw", output_file=str(output_file))
    assert exit_code == 0
    assert output_file.is_file()

    with output_file.open() as f:
        metrics = json.load(f)

    # Basic sanity checks on the produced structure
    assert "t_test" in metrics
    assert "linear_regression" in metrics
    t = metrics["t_test"]
    if t:
        assert 0 < t["p_value"] < 1
        low, high = t["ci"]
        assert low < high
        assert all(map(lambda x: isinstance(x, (int, float)), t["ci"]))
    lr = metrics["linear_regression"]
    assert 0 < lr["p_value"] < 1
    low, high = lr["ci"]
    assert low < high
    assert all(map(lambda x: isinstance(x, (int, float)), lr["ci"]))
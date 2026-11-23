"""
Unit tests for the end‑to‑end entry point (code/main.py).

The tests verify that the pipeline can be run in dry‑run mode and that
the required artefacts are produced with the correct dimensions.
"""

import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.timeout(300)
def test_main_dry_run_creates_outputs(tmp_path, monkeypatch):
    """
    Execute the pipeline in dry‑run mode and check that the essential
    result files exist and contain the expected number of rows.
    """
    # Ensure the repository root is on the Python path.
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(repo_root))

    # Run the pipeline.
    result = subprocess.run(
        [sys.executable, "code/main.py", "--mode", "dry-run", "--seed", "42"],
        cwd=str(repo_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Verify artefacts.
    results_dir = repo_root / "data" / "results"
    expected_files = [
        "estimation_results.csv",
        "aggregated_metrics.csv",
        "report.md",
        "reml_failures.json",
        "stability_analysis.json",
        "coverage_vs_tau2.png",
        "mean_bias_vs_tau2.png",
        "simulation_raw.jsonl",
    ]
    for fname in expected_files:
        path = results_dir / fname
        assert path.is_file(), f"Missing {fname}"
        assert path.stat().st_size > 0, f"{fname} is empty"
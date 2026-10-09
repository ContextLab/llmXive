import os
import json
import subprocess
import sys
import pytest
from pathlib import Path

@pytest.fixture
def clean_results(tmp_path):
    """Create a clean results directory for the test."""
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    return results_dir

def test_main_creates_model_metrics(tmp_path, monkeypatch):
    """
    End‑to‑end test that the orchestrator runs without error and produces
    `results/model_metrics.json`. The test provides dummy input files
    for the dependent steps so that the orchestrator does not attempt to
    download large datasets.
    """
    # Create minimal placeholder JSON files that the orchestrator expects.
    # These are deliberately simple but valid JSON structures.
    dummy_training = {"r2": 0.25, "rmse": 0.5}
    dummy_perm = {"p_value": 0.03, "null_distribution": []}
    dummy_baseline = {"baseline_r2": 0.10, "baseline_rmse": 0.6}
    dummy_profile = {"elapsed_seconds": 123, "status": "ok"}

    # Write them to the expected locations under the temporary directory.
    for name, content in [
        ("results/train_results.json", dummy_training),
        ("results/permutation_test.json", dummy_perm),
        ("results/baseline_comparison.json", dummy_baseline),
        ("results/runtime_profile.json", dummy_profile),
    ]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(content, f)

    # Ensure the orchestrator sees the temporary working directory as the project root.
    monkeypatch.chdir(tmp_path)

    # Run the orchestrator script.
    result = subprocess.run(
        [sys.executable, "code/main.py", "--output-dir", "results"],
        capture_output=True,
        text=True,
    )

    # The script should exit with status 0.
    assert result.returncode == 0, f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    # The merged file must exist and contain the merged components.
    merged_path = tmp_path / "results" / "model_metrics.json"
    assert merged_path.is_file(), "Merged model_metrics.json was not created."

    with open(merged_path, "r") as f:
        merged = json.load(f)

    # Basic sanity checks on the merged structure.
    assert "components" in merged
    assert merged["components"]["training"]["r2"] == 0.25
    assert merged["components"]["permutation_test"]["p_value"] == 0.03
    assert merged["components"]["baseline_comparison"]["baseline_r2"] == 0.10
    assert merged["components"]["runtime_profile"]["status"] == "ok"

    # Ensure the R² threshold check passed (default threshold is 0.0 if not set).
    # No exception should have been raised. The test passes if we reach here.
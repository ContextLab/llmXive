"""
Unit test for the sensitivity analysis script.

The test runs the script on a very small synthetic setup to ensure that
it executes without error and produces the expected JSON output.
"""

import json
from pathlib import Path

import pytest

# Import the main entry point from the module we just implemented.
from eval.sensitivity import main as sensitivity_main, save_sensitivity_results

@pytest.fixture(scope="module")
def output_path(tmp_path_factory):
    # Override the results directory for the test to keep the repo clean.
    results_dir = tmp_path_factory.mktemp("results")
    # Monkey‑patch the config helper to return our temporary directory.
    from config import get_results_dir

    original = get_results_dir

    def fake_get_results_dir():
        return results_dir

    # Apply patch
    import builtins

    builtins.get_results_dir = fake_get_results_dir
    yield results_dir
    # Restore original after test
    builtins.get_results_dir = original

def test_sensitivity_runs_and_writes_json(output_path):
    # Run the sensitivity analysis – this will invoke the geometry pipeline
    # via subprocess which we do NOT actually execute in CI.  To keep the
    # test lightweight we mock ``subprocess.run``.
    import subprocess

    original_run = subprocess.run

    def fake_run(*args, **kwargs):
        # Simulate a successful geometry pipeline run by creating a dummy
        # sparse warped frames file.
        dummy_warp = Path("data") / "results" / "sparse_warped_frames.npy"
        dummy_warp.parent.mkdir(parents=True, exist_ok=True)
        import numpy as np
        np.save(dummy_warp, np.zeros((1, 1, 3)))  # minimal placeholder
        return subprocess.CompletedProcess(args=args, returncode=0)

    subprocess.run = fake_run

    # Also mock the dense baseline loader to avoid needing the real file.
    from eval.sensitivity import _load_dense_baseline

    original_load_dense = _load_dense_baseline

    def fake_load_dense():
        import numpy as np
        return np.zeros((1, 1, 3))

    eval.sensitivity._load_dense_baseline = fake_load_dense

    # Execute
    sensitivity_main()

    # Restore patches
    subprocess.run = original_run
    eval.sensitivity._load_dense_baseline = original_load_dense

    # Verify the JSON file exists and has the expected structure.
    json_path = output_path / "sensitivity.json"
    assert json_path.is_file(), "Sensitivity JSON output missing"
    with json_path.open() as f:
        data = json.load(f)
    assert isinstance(data, list) and len(data) > 0
    for entry in data:
        assert "ransac_threshold" in entry
        assert "world_score" in entry
        assert "sparse_consistency_score" in entry
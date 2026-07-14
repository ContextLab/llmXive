import json
from pathlib import Path

import numpy as np
import pytest

from eval.sensitivity import main as sensitivity_main, run_ransac_sweep

@pytest.fixture
def dummy_data(tmp_path):
    # Create dummy dense and sparse .npy files with minimal realistic shape
    dense = np.random.rand(5, 64, 64, 3).astype(np.float32)
    sparse = np.random.rand(5, 64, 64, 3).astype(np.float32)

    raw_dir = tmp_path / "raw"
    results_dir = tmp_path / "results"
    raw_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)

    dense_path = raw_dir / "dense_baseline_frames.npy"
    sparse_path = results_dir / "sparse_warped_frames.npy"

    np.save(dense_path, dense)
    np.save(sparse_path, sparse)

    # Patch the config getters to point to our temporary locations
    import sys
    from types import SimpleNamespace

    mock_config = SimpleNamespace(
        get_raw_dir=lambda: str(raw_dir),
        get_results_dir=lambda: str(results_dir),
        ensure_directories=lambda *args, **kwargs: None,
    )
    sys.modules["config"] = mock_config
    yield dense_path, sparse_path, results_dir

def test_run_ransac_sweep():
    dense = np.random.rand(2, 32, 32, 3).astype(np.float32)
    sparse = np.random.rand(2, 32, 32, 3).astype(np.float32)
    thresholds = [0.1, 0.2, 0.3]
    results = run_ransac_sweep(thresholds, dense, sparse)
    assert len(results) == len(thresholds)
    for r, thr in zip(results, thresholds):
        assert r["threshold"] == thr
        assert isinstance(r["world_score"], float)
        assert isinstance(r["sparse_consistency"], float)

def test_main_creates_output(dummy_data):
    _, _, results_dir = dummy_data
    # Execute the script's main function
    sensitivity_main()
    output_file = results_dir / "sensitivity.json"
    assert output_file.is_file()
    with output_file.open() as f:
        data = json.load(f)
    assert "sensitivity_sweep" in data
    assert isinstance(data["sensitivity_sweep"], list)
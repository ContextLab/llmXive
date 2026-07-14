"""
Minimal integration test for ``code/eval/metrics.py``.

The test creates tiny synthetic dense and sparse frame stacks,
stores them in the expected locations, runs the ``main`` function and
checks that the JSON report is produced and contains the four keys.
"""
import json
from pathlib import Path

import numpy as np

# Import the module under test
from eval.metrics import main as metrics_main


def test_metrics_produce_output(tmp_path, monkeypatch):
    # ------------------------------------------------------------------
    # Arrange – create tiny synthetic data (2 frames, 8x8 RGB)
    # ------------------------------------------------------------------
    dense = np.random.randint(0, 256, size=(2, 8, 8, 3), dtype=np.uint8)
    sparse = dense.copy()
    # introduce a small perturbation to ensure non‑trivial metric values
    sparse[0, 0, 0, 0] = (sparse[0, 0, 0, 0] + 10) % 256

    # Write the arrays to the real project directories
    from config import get_raw_dir, get_results_dir, ensure_directories

    ensure_directories()
    raw_dir = get_raw_dir()
    results_dir = get_results_dir()

    dense_path = raw_dir / "dense_baseline_frames.npy"
    sparse_path = results_dir / "sparse_warped_frames.npy"

    dense_path.parent.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    np.save(dense_path, dense)
    np.save(sparse_path, sparse)

    # ------------------------------------------------------------------
    # Act – run the metrics script
    # ------------------------------------------------------------------
    metrics_main()

    # ------------------------------------------------------------------
    # Assert – JSON file exists and contains expected keys
    # ------------------------------------------------------------------
    out_path = results_dir / "metrics.json"
    assert out_path.is_file(), "Metrics JSON was not created"

    with out_path.open() as f:
        data = json.load(f)

    expected_keys = {
        "world_score_psnr",
        "sparse_consistency_ssim",
        "fid",
        "unified_geometric_error_l1",
    }
    assert expected_keys.issubset(data.keys()), "Missing metric keys in output"

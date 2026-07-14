import json
from pathlib import Path

import numpy as np

from eval.metrics import (
    calculate_world_score,
    calculate_sparse_consistency_score,
    compute_unified_geometric_error,
)

def test_world_score_computation(tmp_path: Path):
    # Create a simple synthetic dense sequence where frames are identical
    frames = np.zeros((5, 64, 64, 3), dtype=np.uint8)
    score = calculate_world_score(frames)
    assert isinstance(score, float)
    # No change between frames → score should be 0.0
    assert abs(score) < 1e-6

def test_sparse_consistency_score_fallback(tmp_path: Path):
    # Sparse frames with a known offset
    sparse = np.arange(5 * 4).reshape(5, 2, 2, 1).astype(np.float32)
    # No dense baseline present – function should fallback to intra‑sparse metric
    score = calculate_sparse_consistency_score(sparse)
    assert isinstance(score, float)
    # With a linear progression the L2 diff should be > 0
    assert score > 0

def test_unified_geometric_error(tmp_path: Path):
    dense = np.zeros((3, 8, 8, 3), dtype=np.uint8)
    sparse = np.ones((3, 8, 8, 3), dtype=np.uint8) * 255
    error = compute_unified_geometric_error(dense, sparse)
    # Max per‑pixel distance between 0 and 255 is 255, L2 across 3 channels ~ 441.67
    assert isinstance(error, float)
    assert error > 400  # sanity check

def test_metrics_json_written(tmp_path: Path, monkeypatch):
    # Monkeypatch the paths used inside eval.metrics to a temporary location
    from config import get_results_dir, get_raw_dir

    # Create dummy dense and sparse files
    raw_dir = tmp_path / "raw"
    results_dir = tmp_path / "results"
    raw_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)

    dense_path = raw_dir / "dense_baseline_frames.npy"
    sparse_path = results_dir / "sparse_warped_frames.npy"

    np.save(dense_path, np.zeros((2, 4, 4, 3), dtype=np.uint8))
    np.save(sparse_path, np.ones((2, 4, 4, 3), dtype=np.uint8) * 255)

    monkeypatch.setattr("config.get_raw_dir", lambda: raw_dir)
    monkeypatch.setattr("config.get_results_dir", lambda: results_dir)

    from eval.metrics import main as metrics_main
    metrics_main()

    out_file = results_dir / "metrics.json"
    assert out_file.is_file()
    data = json.loads(out_file.read_text())
    assert "world_score" in data
    assert "fid" in data
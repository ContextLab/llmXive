import json
import os
from pathlib import Path

import numpy as np

# Import the module under test
from eval.metrics import main as metrics_main, calculate_world_score, calculate_sparse_consistency_score

def test_metric_computation(tmp_path: Path):
    """
    End‑to‑end test that the metrics script writes a JSON file with the expected keys.
    Uses tiny synthetic arrays (real data not required for the test of plumbing).
    """
    # Set up fake data directories
    project_root = Path(__file__).resolve().parents[2]  # project root
    raw_dir = project_root / "data" / "raw"
    results_dir = project_root / "data" / "results"
    raw_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal synthetic frames (2 frames, 8x8 RGB)
    dense = np.random.randint(0, 256, size=(2, 8, 8, 3), dtype=np.uint8)
    sparse = dense.copy()  # identical so errors are zero

    np.save(raw_dir / "dense_baseline_frames.npy", dense)
    np.save(results_dir / "sparse_warped_frames.npy", sparse)

    # Run the main entry point
    metrics_main()

    # Verify JSON exists and contains the required keys
    json_path = results_dir / "metrics.json"
    assert json_path.is_file(), "metrics.json was not created"

    with json_path.open() as f:
        data = json.load(f)

    for key in (
        "world_score",
        "sparse_consistency_score",
        "unified_geometric_error",
        "fid",
    ):
        assert key in data, f"Missing key {key} in metrics.json"

    # Simple sanity checks on values (they should be zero for identical frames)
    assert data["world_score"] == 0.0
    assert data["sparse_consistency_score"] == 0.0
    assert data["unified_geometric_error"] == 0.0
    # FID may be 0.0 (fallback) or a small positive number – just ensure it's a float
    assert isinstance(data["fid"], float)
import json
from pathlib import Path

import pytest

# Import the main function to trigger metric computation
from eval.metrics import main as metrics_main

@pytest.fixture(scope="module")
def run_metrics(tmp_path_factory):
    # Ensure a clean environment: use temporary directories for data
    # Override config functions to point to temporary locations
    from config import ensure_directories, get_raw_dir, get_results_dir

    # Create temporary data directories
    raw_dir = Path(tmp_path_factory.mktemp("raw"))
    results_dir = Path(tmp_path_factory.mktemp("results"))

    # Monkey‑patch config getters for the duration of the test
    original_get_raw_dir = get_raw_dir
    original_get_results_dir = get_results_dir

    def fake_get_raw_dir():
        return raw_dir

    def fake_get_results_dir():
        return results_dir

    # Apply patches
    import config

    config.get_raw_dir = fake_get_raw_dir
    config.get_results_dir = fake_get_results_dir

    # Ensure directories exist
    ensure_directories([raw_dir, results_dir])

    # Create tiny dummy data that satisfies shape expectations
    # Dense baseline: 2 frames, 32x32 RGB
    dense_dummy = (np.random.rand(2, 32, 32, 3) * 255).astype(np.uint8)
    dense_path = raw_dir / "dense_baseline_frames.npy"
    np.save(dense_path, dense_dummy)

    # Sparse warped frames: same shape for simplicity
    sparse_dummy = (np.random.rand(2, 32, 32, 3) * 255).astype(np.uint8)
    sparse_path = results_dir / "sparse_warped_frames.npy"
    np.save(sparse_path, sparse_dummy)

    # Run the metrics script
    metrics_main()

    # Yield the path to the generated JSON for assertions
    yield results_dir / "metrics.json"

    # Cleanup / restore original functions
    config.get_raw_dir = original_get_raw_dir
    config.get_results_dir = original_get_results_dir

def test_metrics_file_exists(run_metrics):
    """The metrics JSON file must be created."""
    assert run_metrics.is_file()

def test_metrics_content(run_metrics):
    """The JSON must contain all expected keys and numeric values."""
    with open(run_metrics) as fp:
        data = json.load(fp)
    for key in [
        "WorldScore",
        "SparseConsistencyScore",
        "FID",
        "UnifiedGeometricError",
    ]:
        assert key in data
        assert isinstance(data[key], (int, float))
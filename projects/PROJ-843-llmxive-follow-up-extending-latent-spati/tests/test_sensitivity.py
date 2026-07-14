import json
from pathlib import Path

from eval.sensitivity import main as sensitivity_main, load_dense_baseline, load_sparse_warped

def test_sensitivity_workflow(tmp_path, monkeypatch):
    """
    Run the sensitivity script on tiny synthetic arrays to ensure it
    produces a valid JSON output without touching the real data directories.
    """
    # Create minimal dense and sparse arrays
    dense = tmp_path / "dense.npy"
    sparse = tmp_path / "sparse.npy"
    import numpy as np
    np.save(dense, np.zeros((1, 1, 3)))
    np.save(sparse, np.zeros((1, 1, 3)))

    # Patch the paths used inside the module
    monkeypatch.setattr("eval.sensitivity.Path", lambda *p: Path(*p))
    monkeypatch.setattr("eval.sensitivity.load_dense_baseline", lambda: np.load(dense))
    monkeypatch.setattr("eval.sensitivity.load_sparse_warped", lambda: np.load(sparse))

    # Run the script (it will write to the real results directory)
    sensitivity_main()

    # Verify the JSON file exists and has the expected keys
    results_path = Path("data") / "results" / "sensitivity.json"
    assert results_path.is_file()
    data = json.load(results_path.open())
    assert isinstance(data, list)
    for entry in data:
        assert "ransac_threshold" in entry
        assert "world_score" in entry
        assert "sparse_consistency_score" in entry
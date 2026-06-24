"""
Integration test for the dummy GNN training pipeline.

The test imports the ``train_gnn`` script, runs its ``main`` function and
checks that:
  * a checkpoint file ``gnn_dummy.pt`` is created under ``data/checkpoints``
  * the returned metrics dictionary contains non‑negative ``mae`` and ``rmse``
"""
import importlib.util
import pathlib


def _load_train_gnn_module():
    """Load the ``train_gnn.py`` module from the project tree."""
    project_root = pathlib.Path(__file__).resolve().parents[3]
    script_path = project_root / "code" / "training" / "train_gnn.py"
    spec = importlib.util.spec_from_file_location("train_gnn", str(script_path))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None, "Failed to load train_gnn module"
    spec.loader.exec_module(module)
    return module


def test_gnn_training_pipeline():
    # Ensure a clean checkpoints directory before the run
    project_root = pathlib.Path(__file__).resolve().parents[3]
    checkpoints_dir = project_root / "data" / "checkpoints"
    if checkpoints_dir.exists():
        for f in checkpoints_dir.iterdir():
            f.unlink()
    else:
        checkpoints_dir.mkdir(parents=True)

    # Run the training script
    train_gnn = _load_train_gnn_module()
    metrics = train_gnn.main()

    # Verify checkpoint was written
    ckpt_file = checkpoints_dir / "gnn_dummy.pt"
    assert ckpt_file.is_file(), "Checkpoint file was not created"

    # Verify metrics structure
    assert isinstance(metrics, dict), "Metrics should be a dict"
    assert "mae" in metrics and "rmse" in metrics, "Missing metric keys"
    assert metrics["mae"] >= 0.0, "MAE should be non‑negative"
    assert metrics["rmse"] >= 0.0, "RMSE should be non‑negative"

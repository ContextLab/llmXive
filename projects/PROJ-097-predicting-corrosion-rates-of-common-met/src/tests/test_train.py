"""Basic sanity test for the training step (T004)."""

from __future__ import annotations

import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def test_first_run_metrics_created():
    """Run the training script and ensure the JSON file exists and looks sane."""
    from src.pipeline.train import main as train_main

    rc = train_main([])
    assert rc == 0, "train_main exited with non‑zero status"

    metrics_path = paths.results("first_run_metrics.json")
    assert metrics_path.is_file(), f"Metrics file not found at {metrics_path}"

    with open(metrics_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Basic sanity checks on the structure
    assert "folds" in data and isinstance(data["folds"], list), "Missing 'folds' list"
    assert "model_r2_mean" in data, "Missing model R² mean"
    assert "baseline_r2_mean" in data, "Missing baseline R² mean"
    # Ensure the Full model improves over baseline by at least a tiny margin
    assert data["model_r2_mean"] > data["baseline_r2_mean"], "Model does not outperform baseline"
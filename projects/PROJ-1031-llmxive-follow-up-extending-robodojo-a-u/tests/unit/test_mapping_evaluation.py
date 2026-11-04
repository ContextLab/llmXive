"""
Unit tests for ``code/analysis/mapping_evaluation.py``.
The tests create temporary Parquet files with synthetic but *real* data,
invoke the evaluation function, and verify that the produced metrics are
correct and written to the expected location.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the module under test
from code.analysis.mapping_evaluation import evaluate_mapping

@pytest.fixture
def synthetic_symbolic_state():
    """Create a simple SymbolicState DataFrame."""
    # 35 tasks – satisfies the ≥30 requirement
    records = []
    for i in range(35):
        task_id = f"T{i:03d}"
        # Simple deterministic predicates based on task index
        pred = [f"Pred_{i % 5}", f"Common_{i % 3}"]
        records.append(
            {
                "state_id": f"state_{i}",
                "task_id": task_id,
                "predicates": pred,
                "affordances": [],
                "connectivity_graph": {},
                "graph_type": "Full",
            }
        )
    return pd.DataFrame(records)

def test_evaluate_mapping_correctness(synthetic_symbolic_state):
    """
    Create matching prediction and ground‑truth files where the predictions
    are a noisy version of the ground truth. Verify that precision and
    recall are computed as expected.
    """
    # Ground truth = original predicates
    gt_df = synthetic_symbolic_state.copy()

    # Predictions: keep the first predicate, drop the second, and add a false one
    pred_records = []
    for _, row in synthetic_symbolic_state.iterrows():
        preds = [row["predicates"][0], "NoisePredicate"]
        pred_records.append(
            {
                "state_id": row["state_id"],
                "task_id": row["task_id"],
                "predicates": preds,
                "affordances": [],
                "connectivity_graph": {},
                "graph_type": row["graph_type"],
            }
        )
    pred_df = pd.DataFrame(pred_records)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pred_path = tmp_path / "predictions.parquet"
        gt_path = tmp_path / "ground_truth.parquet"
        out_path = tmp_path / "metrics.parquet"

        pred_df.to_parquet(pred_path, index=False)
        gt_df.to_parquet(gt_path, index=False)

        # Run evaluation
        metrics_df = evaluate_mapping(
            predictions_path=pred_path,
            ground_truth_path=gt_path,
            output_path=out_path,
        )

        # Verify output file exists
        assert out_path.is_file(), "Metrics Parquet file was not created"

        # Verify DataFrame shape
        assert metrics_df.shape[0] == 35
        assert set(metrics_df.columns) == {"task_id", "precision", "recall"}

        # For each row, precision = 1/2 (one correct predicate out of two)
        # recall = 1/2 (one correct out of two ground‑truth predicates)
        assert all(abs(p - 0.5) < 1e-6 for p in metrics_df["precision"])
        assert all(abs(r - 0.5) < 1e-6 for r in metrics_df["recall"])

def test_evaluate_mapping_insufficient_tasks(synthetic_symbolic_state):
    """
    Ensure the function raises a ValueError when fewer than 30 overlapping
    tasks are present.
    """
    # Truncate to 20 tasks
    truncated = synthetic_symbolic_state.head(20)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pred_path = tmp_path / "pred.parquet"
        gt_path = tmp_path / "gt.parquet"
        out_path = tmp_path / "out.parquet"

        truncated.to_parquet(pred_path, index=False)
        truncated.to_parquet(gt_path, index=False)

        with pytest.raises(ValueError, match="Insufficient overlapping tasks"):
            evaluate_mapping(
                predictions_path=pred_path,
                ground_truth_path=gt_path,
                output_path=out_path,
            )
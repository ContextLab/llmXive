"""
code/analysis/mapping_evaluation.py
-----------------------------------
Evaluation script for the embedding‑to‑SymbolicState mapping (FR‑013).

This script loads a set of predicted SymbolicState records (produced by
``code/models/symbolic_state.py``) and a manually annotated ground‑truth
SymbolicState dataset, computes precision and recall of the predicate
predictions for each task, and writes the per‑task metrics to a Parquet
file ``data/interim/mapping_metrics.parquet``.

The output conforms to the ``symbolic_state.schema.yaml`` contract in the
sense that the ``task_id`` column matches the schema and the additional
``precision`` and ``recall`` columns are numeric values in ``[0, 1]``.
"""

import argparse
import logging
import os
from pathlib import Path
from typing import List, Set, Tuple

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_symbolic_states(file_path: Path) -> pd.DataFrame:
    """Load a Parquet file containing SymbolicState records.

    The file is expected to have at least the columns ``task_id`` and
    ``predicates`` where ``predicates`` is a list‑like column (e.g. a
    Python list stored by pandas).

    Args:
        file_path: Path to the Parquet file.

    Returns:
        DataFrame with ``task_id`` as index and a ``predicates`` column.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"SymbolicState file not found: {file_path}")

    df = pd.read_parquet(file_path)
    if "task_id" not in df.columns or "predicates" not in df.columns:
        raise ValueError(
            f"SymbolicState file must contain 'task_id' and 'predicates' columns. Got columns: {df.columns}"
        )
    # Ensure predicates are stored as Python lists (they may be read as objects)
    df["predicates"] = df["predicates"].apply(lambda x: list(x) if not isinstance(x, list) else x)
    return df.set_index("task_id")

def _precision_recall(
    pred: Set[str], truth: Set[str]
) -> Tuple[float, float]:
    """Compute precision and recall for a single task.

    Handles empty predicate sets gracefully:
    - If both sets are empty, precision and recall are defined as 1.0.
    - If the prediction set is empty but truth is not, precision = 1.0,
      recall = 0.0 (no false positives, all false negatives).
    - If the truth set is empty but predictions exist, precision = 0.0,
      recall = 1.0 (all predictions are false positives).

    Args:
        pred: Predicted predicate set.
        truth: Ground‑truth predicate set.

    Returns:
        (precision, recall) each in the range [0, 1].
    """
    if not pred and not truth:
        return 1.0, 1.0
    if not pred:
        # No predictions → no false positives, but all true items missed
        return 1.0, 0.0
    if not truth:
        # Predictions exist but nothing to predict → all are false positives
        return 0.0, 1.0

    intersection = pred.intersection(truth)
    precision = len(intersection) / len(pred)
    recall = len(intersection) / len(truth)
    return precision, recall

def evaluate_mapping(
    predictions_path: Path,
    ground_truth_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    """Main evaluation routine.

    Loads predictions and ground‑truth SymbolicState tables, computes per‑task
    precision/recall, and writes the results to ``output_path``.

    Args:
        predictions_path: Path to the predictions Parquet file.
        ground_truth_path: Path to the ground‑truth Parquet file.
        output_path: Destination for the metrics Parquet file.

    Returns:
        DataFrame with columns ``task_id``, ``precision``, ``recall``.
    """
    log.info("Loading predicted SymbolicState records from %s", predictions_path)
    pred_df = _load_symbolic_states(predictions_path)

    log.info("Loading ground‑truth SymbolicState records from %s", ground_truth_path)
    gt_df = _load_symbolic_states(ground_truth_path)

    # Align tasks – keep only tasks present in both files
    common_tasks = pred_df.index.intersection(gt_df.index)
    if len(common_tasks) < 30:
        raise ValueError(
            f"Insufficient overlapping tasks for evaluation: found {len(common_tasks)} "
            f"(need at least 30)."
        )

    metrics = []
    for task_id in common_tasks:
        pred_set = set(pred_df.at[task_id, "predicates"])
        truth_set = set(gt_df.at[task_id, "predicates"])
        precision, recall = _precision_recall(pred_set, truth_set)
        metrics.append(
            {
                "task_id": task_id,
                "precision": precision,
                "recall": recall,
            }
        )
        log.debug(
            "Task %s – precision: %.3f, recall: %.3f", task_id, precision, recall
        )

    metrics_df = pd.DataFrame(metrics)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write Parquet (uses pyarrow under the hood)
    metrics_df.to_parquet(output_path, index=False)
    log.info("Mapping evaluation metrics written to %s", output_path)
    return metrics_df

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate precision and recall of embedding‑to‑SymbolicState mapping."
    )
    parser.add_argument(
        "--predictions",
        type=str,
        required=True,
        help="Path to the predicted SymbolicState Parquet file.",
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        required=True,
        help="Path to the ground‑truth SymbolicState Parquet file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(paths.data("interim", "mapping_metrics.parquet")),
        help="Destination for the metrics Parquet file.",
    )
    return parser.parse_args()

def main() -> int:
    args = _parse_args()
    try:
        evaluate_mapping(
            predictions_path=Path(args.predictions),
            ground_truth_path=Path(args.ground_truth),
            output_path=Path(args.output),
        )
    except Exception as exc:
        log.error("Mapping evaluation failed: %s", exc)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

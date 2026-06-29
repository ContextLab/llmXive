"""
Bug label reliability validation script.

This module provides a function to compute basic classification metrics
(precision, recall, F1 score) given a CSV file containing the true bug
labels and predicted labels. The CSV must contain the columns
``bug_label`` and ``predicted_label`` where each value is binary (0 or 1).

The function returns a dictionary adhering to the contract expected by
the contract test located at ``tests/contract/test_bug_label_validation.py``.

Additionally, the module can be executed as a script to print the metrics
for a given CSV file.
"""

import argparse
import pandas as pd
from typing import Dict

def validate_bug_labels(csv_path: str) -> Dict[str, float]:
    """
    Compute precision, recall, and F1 score for bug‑label predictions.

    Parameters
    ----------
    csv_path: str
        Path to a CSV file with exactly two columns:
        - ``bug_label``: ground‑truth binary label (0/1)
        - ``predicted_label``: predicted binary label (0/1)

    Returns
    -------
    dict
        Mapping with keys ``precision``, ``recall`` and ``f1_score``.
        All values are ``float`` in the range ``[0.0, 1.0]``.
    """
    # Load the CSV
    df = pd.read_csv(csv_path)

    # Verify required columns exist
    required = {"bug_label", "predicted_label"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Missing required column(s) in CSV: {', '.join(missing)}")

    # Cast to integer for safety and ensure binary values
    df = df.astype({"bug_label": int, "predicted_label": int})

    # True Positives, False Positives, False Negatives
    tp = ((df["bug_label"] == 1) & (df["predicted_label"] == 1)).sum()
    fp = ((df["bug_label"] == 0) & (df["predicted_label"] == 1)).sum()
    fn = ((df["bug_label"] == 1) & (df["predicted_label"] == 0)).sum()

    # Precision, Recall, F1
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1_score),
    }

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate bug‑label predictions by computing precision, recall, and F1 score."
    )
    parser.add_argument(
        "csv_path",
        type=str,
        help="Path to the CSV file containing 'bug_label' and 'predicted_label' columns.",
    )
    return parser.parse_args()

def main() -> None:
    """
    Entry point for command‑line execution.

    Reads the CSV path from command‑line arguments, computes the metrics,
    and prints them to stdout in a human‑readable format.
    """
    args = _parse_args()
    metrics = validate_bug_labels(args.csv_path)
    # Pretty‑print the results
    print("Bug‑label validation metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.4f}")

if __name__ == "__main__":
    main()
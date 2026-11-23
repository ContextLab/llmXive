import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from code.config import get_project_root, EvalConfig
from code.utils.io_utils import read_csv, write_csv

# Constants
F1_STDDEV_THRESHOLD = 0.15  # SC-003 threshold


def generate_stratified_random_baseline(
    data: pd.DataFrame,
    rubric_col: str = "rubric_type",
    label_col: str = "hacking_label",
    sample_fraction: float = 0.1,
    seed: int = 42
) -> pd.Series:
    """
    Generate a stratified random baseline for comparison.
    Samples a fraction of timesteps uniformly within each rubric type.
    """
    if seed is None:
        raise RuntimeError("MISSING_CONFIG: BASELINE_SEED required for reproducibility")

    rng = np.random.default_rng(seed)
    baseline_labels = pd.Series([0] * len(data), index=data.index)

    rubric_types = data[rubric_col].unique()
    for r_type in rubric_types:
        mask = data[rubric_col] == r_type
        indices = data[mask].index
        n_sample = max(1, int(len(indices) * sample_fraction))
        sampled_indices = rng.choice(indices, size=n_sample, replace=False)
        baseline_labels.loc[sampled_indices] = 1

    return baseline_labels


def compute_f1_scores(
    predicted_labels: pd.Series,
    ground_truth_labels: pd.Series
) -> float:
    """
    Compute F1 score for binary classification.
    """
    tp = ((predicted_labels == 1) & (ground_truth_labels == 1)).sum()
    fp = ((predicted_labels == 1) & (ground_truth_labels == 0)).sum()
    fn = ((predicted_labels == 0) & (ground_truth_labels == 1)).sum()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def wilcoxon_signed_rank_test(
    scores_a: List[float],
    scores_b: List[float]
) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test comparing two sets of scores.
    Returns (statistic, p-value).
    """
    from scipy import stats
    if len(scores_a) != len(scores_b):
        raise ValueError("Scores lists must be of equal length for paired test")
    stat, pval = stats.wilcoxon(scores_a, scores_b)
    return stat, pval


def check_f1_stddev_threshold(
    f1_scores_by_rubric: Dict[str, float],
    threshold: float = F1_STDDEV_THRESHOLD
) -> Tuple[bool, float]:
    """
    Check SC-003: F1 std dev across rubric types must be <= threshold.
    Returns (passed, std_dev).
    """
    if not f1_scores_by_rubric:
        raise ValueError("No F1 scores provided to check threshold")

    scores = np.array(list(f1_scores_by_rubric.values()))
    std_dev = np.std(scores, ddof=0)  # Population std dev

    if std_dev > threshold:
        return False, std_dev
    return True, std_dev


def main():
    """
    Main entry point for T035: Check SC-003 (F1 std dev <= 0.15).
    
    This function:
    1. Loads the labeled trajectories data (output of US2).
    2. Computes F1 scores per rubric type.
    3. Checks if the standard deviation of these F1 scores exceeds 0.15.
    4. If it exceeds, halts the pipeline with exit code 1 (research failure).
    5. If it passes, continues (exits 0) for report generation.
    """
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "trajectories_labeled.csv"
    
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        print("Please ensure US2 (T023) has completed successfully.")
        sys.exit(1)

    # Load data
    df = read_csv(data_path)
    
    # Ensure required columns exist
    required_cols = ["rubric_type", "hacking_label", "hacked_label"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        sys.exit(1)

    # Group by rubric type and compute F1 scores
    f1_scores_by_rubric = {}
    
    rubric_types = df["rubric_type"].unique()
    for r_type in rubric_types:
        subset = df[df["rubric_type"] == r_type]
        
        predicted = subset["hacked_label"]
        ground_truth = subset["hacking_label"]
        
        f1 = compute_f1_scores(predicted, ground_truth)
        f1_scores_by_rubric[r_type] = f1
        print(f"F1 Score for {r_type}: {f1:.4f}")

    # Check SC-003
    passed, std_dev = check_f1_stddev_threshold(f1_scores_by_rubric)
    
    print(f"\nStandard Deviation of F1 scores across rubrics: {std_dev:.4f}")
    print(f"Threshold (SC-003): {F1_STDDEV_THRESHOLD}")
    
    if not passed:
        print("\n!!! RESEARCH FAILURE: SC-003 VIOLATION !!!")
        print("F1 standard deviation exceeds the allowed threshold of 0.15.")
        print("The pipeline is halted as per research protocol. No tuning permitted.")
        sys.exit(1)
    
    print("\nSC-003 PASSED: F1 standard deviation is within acceptable limits.")
    print("Continuing to report generation...")
    sys.exit(0)


if __name__ == "__main__":
    main()
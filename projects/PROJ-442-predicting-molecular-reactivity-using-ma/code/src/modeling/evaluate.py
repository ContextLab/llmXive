"""Model evaluation module."""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.modeling.config import load_config
from src.utils.logging import setup_logger, get_logger, log_operation
from src.utils.state_manager import register_artifact

_logger: Optional[Any] = None


def _ensure_logger() -> Any:
    global _logger
    if _logger is None:
        _logger = setup_logger("evaluation")
    return _logger


def load_cv_results(input_path: str) -> pd.DataFrame:
    """Load cross-validation results from CSV.

    Expected columns:
      - fold: fold number
      - reaction_type: reaction class
      - target: observed value
      - prediction: predicted value
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"CV results file not found: {input_path}")

    df = pd.read_csv(input_path)
    return df


def compute_spearman_correlation(
    df: pd.DataFrame,
    target_col: str = "target",
    pred_col: str = "prediction",
) -> float:
    """Compute Spearman rank correlation between target and prediction."""
    rho, _ = spearmanr(df[target_col], df[pred_col])
    return float(rho)


def run_permutation_test(
    df: pd.DataFrame,
    target_col: str = "target",
    pred_col: str = "prediction",
    n_iterations: int = 1000,
    seed: int = 42,
) -> float:
    """Run permutation test to compute p-value for Spearman correlation.

    Shuffles targets within each class to maintain class balance.
    """
    _logger = _ensure_logger()
    np.random.seed(seed)

    # Compute observed correlation
    observed_rho, _ = spearmanr(df[target_col], df[pred_col])

    # Get unique classes
    if "reaction_type" in df.columns:
        classes = df["reaction_type"].unique()
    else:
        classes = [None]

    # Permutation loop
    count_extreme = 0
    for i in range(n_iterations):
        df_shuffled = df.copy()
        for cls in classes:
            if cls is not None:
                mask = df_shuffled["reaction_type"] == cls
                shuffled_targets = df_shuffled.loc[mask, target_col].values.copy()
                np.random.shuffle(shuffled_targets)
                df_shuffled.loc[mask, target_col] = shuffled_targets
            else:
                shuffled_targets = df_shuffled[target_col].values.copy()
                np.random.shuffle(shuffled_targets)
                df_shuffled[target_col] = shuffled_targets

        perm_rho, _ = spearmanr(df_shuffled[target_col], df_shuffled[pred_col])
        if abs(perm_rho) >= abs(observed_rho):
            count_extreme += 1

    p_value = count_extreme / n_iterations
    _logger.log(
        "permutation_test_complete",
        observed_rho=observed_rho,
        p_value=p_value,
        n_iterations=n_iterations,
    )

    return p_value


def load_exclusion_metadata(metadata_path: str) -> Dict[str, Any]:
    """Load class exclusion metadata."""
    if not os.path.exists(metadata_path):
        return {"excluded_classes": []}

    with open(metadata_path, "r") as f:
        return json.load(f)


def generate_summary_report(
    df: pd.DataFrame,
    p_value: float,
    output_path: str,
    min_samples: int = 1000,
) -> None:
    """Generate summary report with class rankings and significance.

    Args:
        df: CV results DataFrame
        p_value: Permutation test p-value
        output_path: Output report path
        min_samples: Minimum samples required for a class to be included
    """
    _logger = _ensure_logger()

    # Load exclusion metadata if available
    exclusion_path = str(Path(output_path).parent / "class_exclusion_metadata.json")
    exclusion_metadata = load_exclusion_metadata(exclusion_path)
    excluded_classes = [item["class"] for item in exclusion_metadata.get("excluded_classes", [])]

    # Compute per-class Spearman correlations
    class_rankings = []
    if "reaction_type" in df.columns:
        for cls in df["reaction_type"].unique():
            if cls in excluded_classes:
                continue

            class_df = df[df["reaction_type"] == cls]
            if len(class_df) < min_samples:
                continue

            rho, _ = spearmanr(class_df["target"], class_df["prediction"])
            class_rankings.append({
                "class": cls,
                "spearman_rho": float(rho),
                "n_samples": len(class_df),
            })

    # Sort by Spearman rho
    class_rankings.sort(key=lambda x: x["spearman_rho"], reverse=True)

    # Determine significance
    is_significant = p_value < 0.01
    significance_label = "Significant" if is_significant else "Not Significant"

    # Build report
    report = {
        "timestamp": pd.Timestamp.utcnow().isoformat(),
        "overall_p_value": p_value,
        "significance": significance_label,
        "class_rankings": class_rankings,
        "excluded_classes": excluded_classes,
    }

    # Save report
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    register_artifact(output_path, "placeholder_checksum")

    _logger.log(
        "report_generated",
        output_path=output_path,
        n_classes=len(class_rankings),
        significance=significance_label,
    )


def main() -> None:
    """Main entry point for evaluation script."""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate model performance")
    parser.add_argument(
        "--input",
        required=True,
        help="Input CV results CSV path",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output analysis report JSON path",
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=1000,
        help="Number of permutation test iterations",
    )

    args = parser.parse_args()

    # Initialize logger
    setup_logger("evaluation")

    try:
        # Load CV results
        df = load_cv_results(args.input)

        # Compute overall Spearman correlation
        overall_rho = compute_spearman_correlation(df)
        _logger.log("overall_spearman", rho=overall_rho)

        # Run permutation test
        p_value = run_permutation_test(df, n_iterations=args.n_permutations)

        # Generate report
        generate_summary_report(df, p_value, args.output)

    except Exception as e:
        _logger = _ensure_logger()
        _logger.log("evaluation_failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
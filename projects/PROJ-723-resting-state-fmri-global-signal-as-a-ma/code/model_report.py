"""
T025: Generate model_report.json containing primary model metrics,
null distribution stats, and significance results.

Dependencies:
  - T019, T020, T021, T022 (modeling.py functions)
  - T016 (cleaned_data.csv)
  - T023 (delta_r2.json)
  - T024 (diagnostics.json)
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np

# Import from existing API surface
from utils import get_logger, read_json, write_json
from modeling import (
    load_cleaned_data,
    run_ridge_regression_with_nested_cv,
    run_null_distribution_analysis,
    run_reduced_model_analysis,
    calculate_delta_r2,
)

logger = get_logger(__name__)


def load_existing_results() -> Dict[str, Any]:
    """Load previously generated results (delta_r2, diagnostics)."""
    results_dir = Path("data/results")
    delta_r2_path = results_dir / "delta_r2.json"
    diagnostics_path = results_dir / "diagnostics.json"

    delta_r2_data = None
    diagnostics_data = None

    if delta_r2_path.exists():
        delta_r2_data = read_json(delta_r2_path)
        logger.info(f"Loaded delta_r2 from {delta_r2_path}")
    else:
        logger.warning(f"delta_r2.json not found at {delta_r2_path}")

    if diagnostics_path.exists():
        diagnostics_data = read_json(diagnostics_path)
        logger.info(f"Loaded diagnostics from {diagnostics_path}")
    else:
        logger.warning(f"diagnostics.json not found at {diagnostics_path}")

    return {
        "delta_r2": delta_r2_data,
        "diagnostics": diagnostics_data,
    }


def compute_null_distribution_stats(
    null_maes: np.ndarray, observed_mae: float
) -> Dict[str, float]:
    """Compute statistics for the null distribution and empirical p-value."""
    if len(null_maes) == 0:
        raise ValueError("Null MAE array is empty; cannot compute stats.")

    mean_null = float(np.mean(null_maes))
    std_null = float(np.std(null_maes))
    min_null = float(np.min(null_maes))
    max_null = float(np.max(null_maes))

    # Empirical p-value: proportion of null MAEs <= observed MAE
    # (Lower MAE is better, so we check how often null performed as well as or better than observed)
    p_value = float(np.sum(null_maes <= observed_mae) / len(null_maes))

    return {
        "mean_null_mae": mean_null,
        "std_null_mae": std_null,
        "min_null_mae": min_null,
        "max_null_mae": max_null,
        "empirical_p_value": p_value,
    }


def generate_model_report() -> Dict[str, Any]:
    """
    Main function to generate the model report.

    Steps:
      1. Load cleaned data.
      2. Run primary ridge regression (nested CV).
      3. Run null distribution analysis.
      4. Compute null distribution stats and p-value.
      5. Load existing results (delta_r2, diagnostics).
      6. Assemble and save report.
    """
    logger.info("Starting model report generation (T025)...")

    # 1. Load cleaned data
    data_path = Path("data/processed/cleaned_data.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}")

    df = load_cleaned_data(data_path)
    logger.info(f"Loaded {len(df)} subjects from cleaned_data.csv")

    # 2. Run primary ridge regression
    logger.info("Running primary ridge regression with nested CV...")
    primary_results = run_ridge_regression_with_nested_cv(df)
    # primary_results should contain: mean_mae, mean_r, mean_r2, optimal_alpha, cv_scores, etc.

    observed_mae = primary_results["mean_mae"]
    observed_r = primary_results["mean_r"]
    observed_r2 = primary_results["mean_r2"]
    optimal_alpha = primary_results["optimal_alpha"]

    logger.info(f"Primary model - MAE: {observed_mae:.4f}, r: {observed_r:.4f}, R²: {observed_r2:.4f}")

    # 3. Run null distribution analysis
    logger.info("Running null distribution analysis (1,000 permutations)...")
    null_results = run_null_distribution_analysis(df, n_permutations=1000)
    null_maes = null_results["null_maes"]

    # 4. Compute null stats and p-value
    null_stats = compute_null_distribution_stats(null_maes, observed_mae)

    logger.info(f"Null distribution stats: mean={null_stats['mean_null_mae']:.4f}, p-value={null_stats['empirical_p_value']:.4f}")

    # 5. Load existing results (delta_r2, diagnostics)
    existing = load_existing_results()

    # 6. Assemble report
    report = {
        "primary_model": {
            "mean_out_of_fold_mae": observed_mae,
            "mean_out_of_fold_pearson_r": observed_r,
            "mean_out_of_fold_r_squared": observed_r2,
            "optimal_alpha": optimal_alpha,
        },
        "null_distribution": {
            "n_permutations": len(null_maes),
            "mean_null_mae": null_stats["mean_null_mae"],
            "std_null_mae": null_stats["std_null_mae"],
            "min_null_mae": null_stats["min_null_mae"],
            "max_null_mae": null_stats["max_null_mae"],
            "empirical_p_value": null_stats["empirical_p_value"],
        },
        "reduced_model_comparison": existing["delta_r2"],
        "collinearity_diagnostics": existing["diagnostics"],
        "metadata": {
            "n_subjects": len(df),
            "features_used": list(df.drop(columns=["Subject_ID"]).columns),
        },
    }

    return report


def main():
    """Entry point for T025."""
    logging.basicConfig(level=logging.INFO)

    try:
        report = generate_model_report()

        output_path = Path("data/results/model_report.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        write_json(output_path, report)
        logger.info(f"Model report saved to {output_path}")

        # Print summary to stdout
        print(f"Primary Model MAE: {report['primary_model']['mean_out_of_fold_mae']:.4f}")
        print(f"Primary Model Pearson r: {report['primary_model']['mean_out_of_fold_pearson_r']:.4f}")
        print(f"Primary Model R²: {report['primary_model']['mean_out_of_fold_r_squared']:.4f}")
        print(f"Empirical p-value: {report['null_distribution']['empirical_p_value']:.4f}")

    except Exception as e:
        logger.error(f"Failed to generate model report: {e}")
        raise


if __name__ == "__main__":
    main()

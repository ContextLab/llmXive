"""
Statistical analysis module for comparing baseline and spiking transformer models.

Implements paired t-tests, multiple comparison corrections (Bonferroni, Holm-Bonferroni),
and report generation for the Neuromorphic Transformer project.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
from utils.logging_config import setup_logging

# Initialize logger
logger = setup_logging("analysis.statistical_tests")


def load_metrics_data(
    baseline_path: str,
    spiking_path: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load baseline and spiking metrics from CSV files.

    Args:
        baseline_path: Path to baseline_metrics.csv
        spiking_path: Path to spiking_metrics.csv

    Returns:
        Tuple of (baseline_df, spiking_df)

    Raises:
        FileNotFoundError: If the specified files do not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline metrics file not found: {baseline_path}")
    if not os.path.exists(spiking_path):
        raise FileNotFoundError(f"Spiking metrics file not found: {spiking_path}")

    baseline_df = pd.read_csv(baseline_path)
    spiking_df = pd.read_csv(spiking_path)

    required_cols = ["seed", "perplexity", "energy_per_token_kWh"]
    for col in required_cols:
        if col not in baseline_df.columns:
            raise ValueError(f"Missing column '{col}' in baseline metrics")
        if col not in spiking_df.columns:
            raise ValueError(f"Missing column '{col}' in spiking metrics")

    logger.info(f"Loaded {len(baseline_df)} baseline records and {len(spiking_df)} spiking records")
    return baseline_df, spiking_df


def prepare_paired_data(
    baseline_df: pd.DataFrame,
    spiking_df: pd.DataFrame
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    Prepare paired data arrays for t-tests by matching on 'seed'.

    Args:
        baseline_df: Baseline metrics dataframe.
        spiking_df: Spiking metrics dataframe.

    Returns:
        Dictionary mapping metric name to (baseline_values, spiking_values) tuple.
    """
    # Merge on seed to ensure pairing
    merged = pd.merge(
        baseline_df[["seed", "perplexity", "energy_per_token_kWh"]],
        spiking_df[["seed", "perplexity", "energy_per_token_kWh"]],
        on="seed",
        suffixes=("_baseline", "_spiking")
    )

    if len(merged) == 0:
        raise ValueError("No matching seeds found between baseline and spiking datasets.")

    logger.info(f"Prepared {len(merged)} paired records for statistical testing")

    paired_data = {
        "perplexity": (
            merged["perplexity_baseline"].values,
            merged["perplexity_spiking"].values
        ),
        "energy_per_token_kWh": (
            merged["energy_per_token_kWh_baseline"].values,
            merged["energy_per_token_kWh_spiking"].values
        )
    }
    return paired_data


def run_paired_ttest(
    baseline_values: np.ndarray,
    spiking_values: np.ndarray,
    alternative: str = "two-sided"
) -> Dict[str, float]:
    """
    Run a paired t-test on two arrays.

    Args:
        baseline_values: Array of baseline metric values.
        spiking_values: Array of spiking metric values.
        alternative: Type of alternative hypothesis ('two-sided', 'less', 'greater').

    Returns:
        Dictionary with 'statistic' and 'pvalue'.
    """
    if len(baseline_values) != len(spiking_values):
        raise ValueError("Input arrays must have the same length for paired t-test")

    if len(baseline_values) < 2:
        raise ValueError("Paired t-test requires at least 2 samples")

    statistic, pvalue = stats.ttest_rel(baseline_values, spiking_values, alternative=alternative)
    return {"statistic": float(statistic), "pvalue": float(pvalue)}


def apply_bonferroni_correction(
    pvalues: List[float],
    num_tests: int = None
) -> List[float]:
    """
    Apply Bonferroni correction for multiple hypothesis testing.

    Args:
        pvalues: List of raw p-values.
        num_tests: Number of tests performed. Defaults to len(pvalues).

    Returns:
        List of corrected p-values.
    """
    if num_tests is None:
        num_tests = len(pvalues)

    if num_tests == 0:
        return []

    corrected = [min(p * num_tests, 1.0) for p in pvalues]
    return corrected


def apply_holm_bonferroni_correction(
    pvalues: List[float]
) -> List[float]:
    """
    Apply Holm-Bonferroni correction (step-down method).

    Args:
        pvalues: List of raw p-values.

    Returns:
        List of corrected p-values.
    """
    n = len(pvalues)
    if n == 0:
        return []

    # Sort p-values with original indices
    sorted_indices = np.argsort(pvalues)
    sorted_pvalues = [pvalues[i] for i in sorted_indices]

    corrected = [0.0] * n
    alpha = 0.05

    for i, p in enumerate(sorted_pvalues):
        adjusted_p = min(p * (n - i), 1.0)
        # Holm's method: ensure monotonicity
        if i > 0:
            adjusted_p = max(adjusted_p, corrected[sorted_indices[i-1]])
        corrected[sorted_indices[i]] = adjusted_p

    return corrected


def generate_statistical_report(
    paired_data: Dict[str, Tuple[np.ndarray, np.ndarray]],
    output_path: str
) -> Dict[str, Any]:
    """
    Generate a comprehensive statistical report comparing baseline and spiking models.

    Args:
        paired_data: Dictionary of paired metrics.
        output_path: Path to save the JSON report.

    Returns:
        The report dictionary.
    """
    report = {
        "test_type": "Paired T-Test",
        "corrections": ["Bonferroni", "Holm-Bonferroni"],
        "results": {}
    }

    raw_pvalues = []

    for metric_name, (baseline_vals, spiking_vals) in paired_data.items():
        logger.info(f"Running paired t-test for {metric_name}")
        t_result = run_paired_ttest(baseline_vals, spiking_vals)
        raw_pvalues.append(t_result["pvalue"])

        # Calculate mean difference
        mean_diff = np.mean(baseline_vals - spiking_vals)
        mean_baseline = np.mean(baseline_vals)
        mean_spiking = np.mean(spiking_vals)

        report["results"][metric_name] = {
            "t_statistic": t_result["statistic"],
            "p_value_raw": t_result["pvalue"],
            "mean_baseline": float(mean_baseline),
            "mean_spiking": float(mean_spiking),
            "mean_difference": float(mean_diff),
            "interpretation": "Significant" if t_result["pvalue"] < 0.05 else "Not Significant"
        }

    # Apply corrections
    bonferroni_corrected = apply_bonferroni_correction(raw_pvalues)
    holm_corrected = apply_holm_bonferroni_correction(raw_pvalues)

    report["correction_results"] = {
        "bonferroni": {
            "corrected_pvalues": bonferroni_corrected,
            "significant_count": sum(1 for p in bonferroni_corrected if p < 0.05)
        },
        "holm_bonferroni": {
            "corrected_pvalues": holm_corrected,
            "significant_count": sum(1 for p in holm_corrected if p < 0.05)
        }
    }

    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Statistical report saved to {output_path}")
    return report


def main():
    """
    Main entry point for running statistical analysis from command line.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run statistical analysis on model metrics")
    parser.add_argument("--baseline", type=str, default="data/processed/baseline_metrics.csv",
                        help="Path to baseline metrics CSV")
    parser.add_argument("--spiking", type=str, default="data/processed/spiking_metrics.csv",
                        help="Path to spiking metrics CSV")
    parser.add_argument("--output", type=str, default="data/results/statistical_report.json",
                        help="Output path for JSON report")

    args = parser.parse_args()

    try:
        baseline_df, spiking_df = load_metrics_data(args.baseline, args.spiking)
        paired_data = prepare_paired_data(baseline_df, spiking_df)
        report = generate_statistical_report(paired_data, args.output)

        print(f"Analysis complete. Report saved to: {args.output}")
        print(f"Significant results (Bonferroni): {report['correction_results']['bonferroni']['significant_count']}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

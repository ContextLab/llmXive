"""
Statistical Power Analysis Module for Polymer Degradation Dataset.

This module performs statistical power analysis to determine if the filtered
dataset has sufficient size and effect size to support meaningful conclusions
regarding degradation pathways.

Requirements:
- Calculates Cohen's d effect size
- Uses alpha=0.05, beta=0.20 (power=0.80)
- Flags dataset if <150 instances
- Generates JSON report in data/reports/
"""

import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from statsmodels.stats.power import TTestIndPower, TTestPower
from statsmodels.stats.effect_size import CohensD

# Import project utilities
from utils import get_logger, get_project_paths
from data_models import PolymerRecord

logger = get_logger(__name__)


def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.

    Args:
        group1: numpy array of values for group 1
        group2: numpy array of values for group 2

    Returns:
        Cohen's d value
    """
    if len(group1) == 0 or len(group2) == 0:
        raise ValueError("Cannot calculate Cohen's d with empty groups")

    # Use statsmodels for robust calculation
    try:
        d = CohensD(group1, group2).effect_size()
        return float(d)
    except Exception as e:
        logger.error(f"Error calculating Cohen's d: {e}")
        # Fallback to manual calculation if statsmodels fails
        mean1, mean2 = np.mean(group1), np.mean(group2)
        std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
        n1, n2 = len(group1), len(group2)

        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        if pooled_std == 0:
            return 0.0
        return float((mean1 - mean2) / pooled_std)


def interpret_effect_size(d: float) -> str:
    """
    Interpret the magnitude of Cohen's d.

    Args:
        d: Cohen's d value

    Returns:
        String interpretation of effect size
    """
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"


def check_dataset_power(
    n_samples: int,
    effect_size: float,
    alpha: float = 0.05,
    beta: float = 0.20
) -> Dict[str, Any]:
    """
    Check if the dataset has sufficient statistical power.

    Args:
        n_samples: Total number of samples in the dataset
        effect_size: Cohen's d effect size
        alpha: Significance level (default 0.05)
        beta: Type II error rate (default 0.20 for 80% power)

    Returns:
        Dictionary with power analysis results
    """
    power = 1 - beta
    test = TTestIndPower()

    # Calculate power for two-sample t-test
    try:
        # For equal sample sizes, we use n1 = n2 = n_samples / 2
        n_per_group = max(1, n_samples // 2)
        calculated_power = test.power(
            effect_size=effect_size,
            nobs1=n_per_group,
            alpha=alpha,
            ratio=1.0
        )
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}. Using conservative estimate.")
        calculated_power = 0.0

    # Determine if power is sufficient
    is_sufficient = calculated_power >= power

    return {
        "n_samples": n_samples,
        "n_per_group": n_per_group,
        "effect_size": effect_size,
        "effect_size_interpretation": interpret_effect_size(effect_size),
        "alpha": alpha,
        "beta": beta,
        "target_power": power,
        "calculated_power": float(calculated_power),
        "is_sufficient": is_sufficient,
        "minimum_samples_for_power": test.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            ratio=1.0
        ) if effect_size > 0 else 0
    }


def run_power_analysis_from_csv(
    csv_path: str,
    value_column: str,
    group_column: str,
    output_path: str,
    alpha: float = 0.05,
    beta: float = 0.20,
    minimum_threshold: int = 150
) -> Dict[str, Any]:
    """
    Perform power analysis on a CSV dataset.

    Args:
        csv_path: Path to the CSV file containing the dataset
        value_column: Name of the column containing numeric values for effect size
        group_column: Name of the column containing group labels
        output_path: Path to save the JSON report
        alpha: Significance level
        beta: Type II error rate
        minimum_threshold: Minimum number of samples required

    Returns:
        Dictionary with complete power analysis results
    """
    import pandas as pd

    logger.info(f"Loading dataset from {csv_path}")
    df = pd.read_csv(csv_path)

    if value_column not in df.columns:
        raise ValueError(f"Value column '{value_column}' not found in dataset")
    if group_column not in df.columns:
        raise ValueError(f"Group column '{group_column}' not found in dataset")

    # Get unique groups
    groups = df[group_column].unique()
    if len(groups) < 2:
        raise ValueError(f"Need at least 2 groups for power analysis, found {len(groups)}")

    # Take first two groups for comparison
    group1_name, group2_name = groups[0], groups[1]
    group1_data = df[df[group_column] == group1_name][value_column].dropna().values
    group2_data = df[df[group_column] == group2_name][value_column].dropna().values

    total_samples = len(df)
    n_per_group = min(len(group1_data), len(group2_data))

    logger.info(f"Dataset size: {total_samples} total, {n_per_group} in comparison groups")

    # Calculate effect size
    effect_size = calculate_cohen_d(group1_data, group2_data)
    logger.info(f"Calculated Cohen's d: {effect_size:.4f} ({interpret_effect_size(effect_size)})")

    # Check power
    power_results = check_dataset_power(total_samples, effect_size, alpha, beta)

    # Check against minimum threshold
    meets_threshold = total_samples >= minimum_threshold
    power_analysis_passed = power_results["is_sufficient"] and meets_threshold

    # Generate report
    report = {
        "dataset_path": csv_path,
        "analysis_parameters": {
            "alpha": alpha,
            "beta": beta,
            "target_power": 1 - beta,
            "minimum_samples_threshold": minimum_threshold
        },
        "dataset_statistics": {
            "total_samples": total_samples,
            "groups_compared": [group1_name, group2_name],
            "samples_per_group": [len(group1_data), len(group2_data)],
            "value_column": value_column,
            "group_column": group_column
        },
        "effect_size": {
            "cohen_d": effect_size,
            "interpretation": interpret_effect_size(effect_size)
        },
        "power_analysis": power_results,
        "threshold_check": {
            "meets_minimum_samples": meets_threshold,
            "minimum_threshold": minimum_threshold,
            "actual_samples": total_samples
        },
        "overall_status": {
            "passed": power_analysis_passed,
            "reasons": []
        }
    }

    # Collect reasons for failure
    if not meets_threshold:
        report["overall_status"]["reasons"].append(
            f"Dataset size ({total_samples}) below minimum threshold ({minimum_threshold})"
        )
    if not power_results["is_sufficient"]:
        report["overall_status"]["reasons"].append(
            f"Statistical power ({power_results['calculated_power']:.4f}) below target ({1-beta:.4f})"
        )

    if not power_analysis_passed:
        logger.warning(
            f"Power analysis FAILED: {'; '.join(report['overall_status']['reasons'])}"
        )
    else:
        logger.info("Power analysis PASSED")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Power analysis report saved to {output_path}")

    return report


def main():
    """
    Main entry point for power analysis on the polyester-filtered dataset.
    """
    logger.info("Starting power analysis for polymer degradation dataset")

    # Get project paths
    paths = get_project_paths()
    processed_data_path = paths["processed_data"]
    reports_path = paths["reports"]

    # Define input and output paths
    input_csv = os.path.join(processed_data_path, "polyester_filtered.csv")
    output_json = os.path.join(reports_path, "power_analysis_report.json")

    # Check if input file exists
    if not os.path.exists(input_csv):
        logger.error(f"Input file not found: {input_csv}")
        logger.error("Please run T015 (filter_polyesters) before running power analysis")
        return 1

    # Run power analysis
    # We assume the dataset has a 'degradation_pathway' column for grouping
    # and a numeric column (e.g., 'half_life_days' or 'rate_constant') for effect size
    # If specific columns don't exist, we use available numeric columns
    try:
        import pandas as pd
        df = pd.read_csv(input_csv)

        # Determine appropriate columns
        group_col = "degradation_pathway"
        if group_col not in df.columns:
            # Try to find any categorical column
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                group_col = categorical_cols[0]
                logger.warning(f"Using '{group_col}' as group column instead of 'degradation_pathway'")
            else:
                raise ValueError("No categorical column found for grouping")

        # Find numeric column for effect size calculation
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            raise ValueError("No numeric columns found for effect size calculation")

        value_col = numeric_cols[0]
        logger.info(f"Using '{value_col}' for effect size calculation")

        report = run_power_analysis_from_csv(
            csv_path=input_csv,
            value_column=value_col,
            group_column=group_col,
            output_path=output_json,
            alpha=0.05,
            beta=0.20,
            minimum_threshold=150
        )

        # Generate warning flag if needed
        if not report["overall_status"]["passed"]:
            logger.warning("=" * 60)
            logger.warning("WARNING: Power analysis failed!")
            for reason in report["overall_status"]["reasons"]:
                logger.warning(f"  - {reason}")
            logger.warning("Consider collecting more data or adjusting experimental design.")
            logger.warning("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit(main())

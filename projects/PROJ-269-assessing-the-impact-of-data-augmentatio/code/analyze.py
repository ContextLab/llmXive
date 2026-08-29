"""
Analysis module for the augmentation impact study.

Provides functions for calculating error rates, confidence intervals,
and generating comparative analysis reports.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RESULTS_DIR: Path = Path("results")
REPORTS_DIR: Path = Path("results/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_simulation_results(filepath: Path) -> Dict[str, Any]:
    """
    Load simulation results from JSON file.

    Args:
        filepath: Path to the JSON file.

    Returns:
        Loaded results dictionary.
    """
    try:
        with open(filepath, 'r') as f:
            data: Dict[str, Any] = json.load(f)

        logger.info(f"Loaded results from {filepath}: {len(data.get('p_values', []))} p-values")
        return data

    except Exception as e:
        logger.error(f"Failed to load results from {filepath}: {str(e)}")
        raise


def calculate_error_rates(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Calculate Type I and Type II error rates from p-values.

    Args:
        p_values: List of p-values from hypothesis tests.
        alpha: Significance threshold.

    Returns:
        Dictionary with error rate metrics.
    """
    if not p_values:
        return {'type_i_rate': 0.0, 'type_ii_rate': 0.0, 'power': 0.0}

    p_array: np.ndarray = np.array(p_values)

    # Type I error rate (false positive rate under null)
    type_i_rate: float = np.mean(p_array < alpha)

    # For Type II, we need to know if these are null or alt condition
    # This function assumes input is from alt condition for Type II calculation
    # In practice, the caller should specify the condition
    type_ii_rate: float = np.mean(p_array >= alpha)
    power: float = 1.0 - type_ii_rate

    return {
        'type_i_rate': float(type_i_rate),
        'type_ii_rate': float(type_ii_rate),
        'power': float(power),
        'alpha_threshold': alpha
    }


def calculate_bootstrap_ci(
    data: List[float],
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Tuple[float, float, float]:
    """
    Calculate bootstrap confidence interval for a statistic.

    Args:
        data: Input data.
        n_bootstrap: Number of bootstrap samples.
        confidence_level: Confidence level (e.g., 0.95).
        random_state: Random seed.

    Returns:
        Tuple of (mean, lower_ci, upper_ci).
    """
    if random_state is not None:
        np.random.seed(random_state)

    data_array: np.ndarray = np.array(data)
    n: int = len(data_array)

    if n == 0:
        return 0.0, 0.0, 0.0

    bootstrap_means: np.ndarray = []

    for _ in range(n_bootstrap):
        sample: np.ndarray = np.random.choice(data_array, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))

    bootstrap_means_arr: np.ndarray = np.array(bootstrap_means)
    mean: float = np.mean(bootstrap_means_arr)
    lower_ci: float = np.percentile(bootstrap_means_arr, (1 - confidence_level) / 2 * 100)
    upper_ci: float = np.percentile(bootstrap_means_arr, (1 + confidence_level) / 2 * 100)

    return float(mean), float(lower_ci), float(upper_ci)


def ks_test_wrapper(
    p_values_baseline: List[float],
    p_values_augmented: List[float]
) -> Dict[str, Any]:
    """
    Perform Kolmogorov-Smirnov test on p-value distributions.

    Args:
        p_values_baseline: P-values from baseline condition.
        p_values_augmented: P-values from augmented condition.

    Returns:
        Dictionary with KS test statistics and p-value.
    """
    if not p_values_baseline or not p_values_augmented:
        logger.warning("Empty p-value lists provided to KS test.")
        return {'statistic': 0.0, 'p_value': 1.0, 'valid': False}

    try:
        stat: float
        p_val: float
        stat, p_val = stats.ks_2samp(p_values_baseline, p_values_augmented)

        return {
            'statistic': float(stat),
            'p_value': float(p_val),
            'valid': True,
            'n_baseline': len(p_values_baseline),
            'n_augmented': len(p_values_augmented)
        }

    except Exception as e:
        logger.error(f"KS test failed: {str(e)}")
        return {'statistic': 0.0, 'p_value': 1.0, 'valid': False}


def analyze_baseline_results(
    baseline_results: Dict[str, Any],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Analyze baseline simulation results.

    Args:
        baseline_results: Dictionary containing baseline simulation data.
        alpha: Significance threshold.

    Returns:
        Analysis results dictionary.
    """
    p_values: List[float] = baseline_results.get('p_values', [])
    error_rates: Dict[str, float] = calculate_error_rates(p_values, alpha)

    mean_p, lower_ci, upper_ci = calculate_bootstrap_ci(p_values)

    return {
        'metadata': baseline_results.get('metadata', {}),
        'p_value_stats': {
            'mean': float(mean_p),
            'ci_95': [float(lower_ci), float(upper_ci)],
            'min': float(np.min(p_values)) if p_values else 0.0,
            'max': float(np.max(p_values)) if p_values else 1.0
        },
        'error_rates': error_rates
    }


def generate_report(
    all_results: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate final comparative analysis report.

    Args:
        all_results: List of analysis results from different configurations.
        output_path: Optional path to save the report.

    Returns:
        Path to the generated report.
    """
    if output_path is None:
        output_path: Path = REPORTS_DIR / "final_analysis_report.json"

    # Aggregate results
    report: Dict[str, Any] = {
        'metadata': {
            'generated_at': str(pd.Timestamp.now()),
            'threshold': 0.10,
            'disclaimer': "DISCLAIMER: Findings are associational and do not imply causation."
        },
        'summary': [],
        'comparisons': []
    }

    for result in all_results:
        summary_entry: Dict[str, Any] = {
            'dataset': result.get('dataset', 'unknown'),
            'size': result.get('size', 0),
            'method': result.get('method', 'unknown'),
            'type_i_rate': result.get('error_rates', {}).get('type_i_rate', 0.0),
            'power': result.get('error_rates', {}).get('power', 0.0),
            'unsafe': result.get('error_rates', {}).get('type_i_rate', 0.0) > 0.10
        }
        report['summary'].append(summary_entry)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Generated final report at {output_path}")
    return output_path


def main() -> int:
    """
    Main function to run analysis.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    logger.info("Analysis module ready. Use analyze_baseline_results() or generate_report().")
    return 0


if __name__ == "__main__":
    exit(main())

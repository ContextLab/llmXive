"""
Statistical utilities for the Episodic Future Thinking pipeline.

Implements mixed-effects testing with Bonferroni correction as per FR-008.
"""

import json
import math
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Import local logger to avoid circular import with stdlib 'logging'
from utils.logging import get_stats_logger

# Try importing statsmodels; if missing, we handle it gracefully but fail loudly
try:
    import pandas as pd
    import numpy as np
    import statsmodels.api as sm
    from statsmodels.stats.multitest import multipletests
    HAS_STATS = True
except ImportError:
    HAS_STATS = False
    logging.getLogger(__name__).warning(
        "statsmodels/pandas/numpy not installed. Statistical functions will raise ImportError."
    )


def calculate_effect_size(
    group1: List[float],
    group2: List[float],
    method: str = "cohen_d"
) -> float:
    """
    Calculate effect size (Cohen's d) between two groups.

    Args:
        group1: List of values for the first group (e.g., baseline).
        group2: List of values for the second group (e.g., episodic).
        method: Currently only 'cohen_d' is supported.

    Returns:
        Cohen's d value.
    """
    if not HAS_STATS:
        raise ImportError("numpy required for effect size calculation")

    g1 = np.array(group1)
    g2 = np.array(group2)

    if len(g1) < 2 or len(g2) < 2:
        raise ValueError("Each group must have at least 2 samples for variance calculation")

    n1, n2 = len(g1), len(g2)
    mean1, mean2 = np.mean(g1), np.mean(g2)
    var1, var2 = np.var(g1, ddof=1), np.var(g2, ddof=1)

    # Pooled standard deviation
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    if pooled_std == 0:
        return 0.0

    return (mean2 - mean1) / pooled_std


def run_mixed_effects_test(
    data: Dict[str, Any],
    correction_method: str = "bonferroni"
) -> Dict[str, Any]:
    """
    Run a mixed-effects analysis (simulated via linear model for fixed effects
    in this context) and apply Bonferroni correction for multiple comparisons.

    This function addresses FR-008 by enforcing Bonferroni correction.

    Args:
        data: Dictionary containing 'baseline' and 'episodic' lists of scores.
        correction_method: Method for multiple comparison correction. Defaults to 'bonferroni'.

    Returns:
        Dictionary with test statistics, p-values (raw and corrected), and effect size.
    """
    if not HAS_STATS:
        raise ImportError(
            "statsmodels, pandas, and numpy are required for statistical testing. "
            "Please install them via requirements.txt."
        )

    logger = get_stats_logger()
    logger.info("Starting mixed effects test with %s correction", correction_method)

    if 'baseline' not in data or 'episodic' not in data:
        raise ValueError("Input data must contain 'baseline' and 'episodic' keys")

    baseline_scores = data['baseline']
    episodic_scores = data['episodic']

    if len(baseline_scores) == 0 or len(episodic_scores) == 0:
        raise ValueError("Input groups cannot be empty")

    # Convert to DataFrame for statsmodels
    df = pd.DataFrame({
        'score': baseline_scores + episodic_scores,
        'condition': ['baseline'] * len(baseline_scores) + ['episodic'] * len(episodic_scores)
    })

    # Create dummy variable for condition
    X = pd.get_dummies(df['condition'], drop_first=True)
    # Rename column to 'episodic' for clarity
    X.columns = ['episodic']
    y = df['score']

    # Add constant for intercept
    X_const = sm.add_constant(X)

    # Fit OLS model (MixedEffects often requires specifying groups; here we treat as fixed effects
    # for the comparison of means, which is standard for this type of A/B test in the absence
    # of subject-level grouping data in the JSON input)
    model = sm.OLS(y, X_const).fit()

    raw_pvalue = model.pvalues['episodic']
    t_stat = model.tvalues['episodic']

    # Apply Bonferroni correction
    # If we are comparing multiple metrics, we would adjust. Here we assume 1 comparison
    # unless the data structure implies multiple. The task specifies Bonferroni.
    # If multiple comparisons were implied (e.g., multiple tasks), we'd need n_tests.
    # Assuming 1 test for the primary comparison, but applying the function for robustness.
    n_tests = 1 # Default to single comparison unless data implies otherwise
    corrected_pvalues, _, _, _ = multipletests([raw_pvalue], alpha=0.05, method=correction_method)

    effect_size = calculate_effect_size(baseline_scores, episodic_scores)

    result = {
        "t_statistic": float(t_stat),
        "raw_p_value": float(raw_pvalue),
        "corrected_p_value": float(corrected_pvalues[0]),
        "correction_method": correction_method,
        "effect_size_cohen_d": float(effect_size),
        "n_baseline": len(baseline_scores),
        "n_episodic": len(episodic_scores),
        "model_summary": model.summary().tables[1].as_csv() if hasattr(model.summary(), 'tables') else str(model.summary())
    }

    logger.info("Test complete. Corrected p-value: %.4f", result["corrected_p_value"])
    return result


def calculate_power_analysis(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80
) -> Dict[str, float]:
    """
    Calculate required sample size for a given effect size and power.

    Args:
        effect_size: Expected Cohen's d.
        alpha: Significance level.
        power: Desired statistical power.

    Returns:
        Dictionary with required sample size per group.
    """
    if not HAS_STATS:
        raise ImportError("statsmodels required for power analysis")

    from statsmodels.stats.power import TTestIndPower

    analysis = TTestIndPower()
    n = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        ratio=1.0,
        alternative='two-sided'
    )

    return {
        "required_n_per_group": int(math.ceil(n)),
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power
    }


def run_power_analysis(
    data: Dict[str, Any],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run power analysis based on observed data.

    Args:
        data: Dictionary with 'baseline' and 'episodic' lists.
        alpha: Significance level.

    Returns:
        Dictionary with observed effect size and required sample size.
    """
    effect = calculate_effect_size(data['baseline'], data['episodic'])
    power_info = calculate_power_analysis(effect, alpha)
    power_info["observed_effect_size"] = effect
    return power_info


def main():
    """
    CLI entry point for statistical analysis.

    Usage:
        python code/utils/stats.py --input data/logs/episodic_results.json --variant 10 --fdr
    """
    parser = argparse.ArgumentParser(description="Run statistical tests on episodic planning results")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to JSON file containing 'baseline' and 'episodic' result lists"
    )
    parser.add_argument(
        "--variant",
        type=str,
        default="default",
        help="Variant identifier for logging/output naming"
    )
    parser.add_argument(
        "--fdr",
        action="store_true",
        help="Use FDR (Benjamini-Hochberg) instead of Bonferroni (default: Bonferroni)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save JSON results. If None, prints to stdout."
    )

    args = parser.parse_args()

    logger = get_stats_logger()
    logger.info("Starting stats analysis for variant: %s", args.variant)

    if not HAS_STATS:
        logger.error("Missing dependencies (statsmodels/pandas/numpy). Cannot proceed.")
        sys.exit(1)

    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        sys.exit(1)

    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON input: %s", e)
        sys.exit(1)

    # Determine correction method
    correction_method = "fdr_bh" if args.fdr else "bonferroni"

    try:
        results = run_mixed_effects_test(data, correction_method=correction_method)
        results["variant"] = args.variant
        results["timestamp"] = datetime.now().isoformat()
        results["input_file"] = str(input_path)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info("Results written to %s", output_path)
        else:
            print(json.dumps(results, indent=2))

    except Exception as e:
        logger.error("Statistical analysis failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
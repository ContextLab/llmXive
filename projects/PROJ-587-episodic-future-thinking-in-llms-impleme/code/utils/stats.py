"""
Statistical utilities for the Episodic Future Thinking project.

Implements mixed-effects modeling, effect size calculations, and power analysis
using statsmodels with Bonferroni correction for multiple comparisons (FR-008).
"""
import json
import math
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.formula.api import mixedlm

# Resolve circular import by avoiding direct 'import logging' at top level if
# this file is named logging.py in a different context, but here it is stats.py.
# However, the error log showed:
# File ".../code/utils/stats.py", line 4, in <module>
#   import logging
#   File ".../code/utils/logging.py", ...
# This implies the environment might have a shadowing issue or the error log
# was from a previous broken state where stats.py was named logging.py or
# the import path was messed up.
# To be safe and ensure this file works independently:
# We will use the standard library logging module explicitly.
# The previous error "partially initialized module 'logging' has no attribute 'Logger'"
# happened because the file itself was named `logging.py` or there was a circular
# import where `stats.py` tried to import `logging` but the local `logging.py`
# was being loaded instead of stdlib.
# Since the path is `code/utils/stats.py`, importing `logging` should be fine
# UNLESS the user's PYTHONPATH or a local file named `logging.py` exists in the
# current working directory or `code/utils`.
# The error log says:
# File "/home/.../code/utils/stats.py", line 4, in <module>
#   import logging
# File "/home/.../code/utils/logging.py", ...
# This confirms that `import logging` in `stats.py` was resolving to `code/utils/logging.py`
# instead of the stdlib `logging`. This is a classic shadowing error.
# Fix: Use `import logging as stdlib_logging` or ensure we don't shadow.
# But we cannot rename `code/utils/logging.py` in this task (it's T017).
# We must fix `stats.py` to NOT shadow the stdlib logging module.
# The solution is to import the stdlib logging module explicitly by bypassing
# the local module if possible, or simply not importing it if we can use a
# different mechanism.
# However, the standard way to fix "import logging" resolving to a local file
# is to ensure the stdlib is found first. But Python's import system is
# path-order based. If `code/utils` is in sys.path, and `logging.py` exists there,
# it will be imported.
# We can use `import importlib; stdlib_logging = importlib.import_module('logging')`
# to force the stdlib version.

import importlib
stdlib_logging = importlib.import_module('logging')

def calculate_effect_size(
    group1: np.ndarray,
    group2: np.ndarray
) -> float:
    """
    Calculate Cohen's d effect size between two groups.

    Args:
        group1: Array of values for group 1.
        group2: Array of values for group 2.

    Returns:
        Cohen's d value.
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float(np.mean(group1) - np.mean(group2)) / pooled_std


def run_mixed_effects_test(
    data: pd.DataFrame,
    dependent_var: str,
    fixed_effects: List[str],
    random_effects: str = "1 | subject_id",
    correction_method: str = "bonferroni"
) -> Dict[str, Any]:
    """
    Run a linear mixed-effects model with Bonferroni correction for multiple comparisons.

    Args:
        data: DataFrame containing the experimental data.
        dependent_var: Name of the dependent variable column.
        fixed_effects: List of fixed effect variables.
        random_effects: Random effects formula string (default: intercept by subject).
        correction_method: Method for multiple testing correction (default: 'bonferroni').

    Returns:
        Dictionary containing model summary, p-values, and corrected p-values.
    """
    # Construct formula
    formula = f"{dependent_var} ~ {' + '.join(fixed_effects)}"

    # Fit the model
    model = mixedlm(formula, data, groups=data["subject_id"])
    result = model.fit()

    # Extract p-values for fixed effects
    p_values = result.pvalues
    fixed_effect_names = [name for name in fixed_effects if name in p_values.index]

    # Filter p-values for fixed effects only
    relevant_p_values = [p_values[name] for name in fixed_effect_names]

    # Apply Bonferroni correction
    if len(relevant_p_values) > 0:
        corrected_p_values, _, _, _ = multipletests(
            relevant_p_values,
            alpha=0.05,
            method=correction_method
        )
    else:
        corrected_p_values = []

    return {
        "formula": formula,
        "random_effects": random_effects,
        "coefficients": result.params.to_dict(),
        "p_values": {name: p_values[name] for name in fixed_effect_names},
        "corrected_p_values": {
            name: p for name, p in zip(fixed_effect_names, corrected_p_values)
        },
        "aicc": result.aicc,
        "bic": result.bic,
        "loglike": result.llf
    }


def calculate_power_analysis(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80
) -> int:
    """
    Calculate required sample size for a given effect size and power.

    Args:
        effect_size: Cohen's d effect size.
        alpha: Significance level.
        power: Desired statistical power.

    Returns:
        Required sample size per group.
    """
    if effect_size == 0:
        return float('inf')

    # Approximate formula for two-sample t-test
    from scipy.stats import norm
    z_alpha = norm.ppf(1 - alpha / 2)
    z_power = norm.ppf(power)

    n_per_group = 2 * ((z_alpha + z_power) / effect_size) ** 2
    return int(math.ceil(n_per_group))


def run_power_analysis(
    baseline_scores: np.ndarray,
    treatment_scores: np.ndarray,
    alpha: float = 0.05,
    target_power: float = 0.80
) -> Dict[str, Any]:
    """
    Run power analysis for two groups.

    Args:
        baseline_scores: Array of baseline scores.
        treatment_scores: Array of treatment scores.
        alpha: Significance level.
        target_power: Target statistical power.

    Returns:
        Dictionary containing effect size, required sample size, and current power.
    """
    effect_size = calculate_effect_size(baseline_scores, treatment_scores)
    required_n = calculate_power_analysis(effect_size, alpha, target_power)

    # Calculate current power (simplified)
    n_current = min(len(baseline_scores), len(treatment_scores))
    # Approximate power calculation
    from scipy.stats import nct
    # This is a simplified approximation
    current_power = 1.0 - nct.cdf(
        nct.ppf(alpha/2, n_current-1),
        n_current-1,
        effect_size * math.sqrt(n_current/2)
    )

    return {
        "effect_size": effect_size,
        "required_sample_size_per_group": required_n,
        "current_sample_size": n_current,
        "estimated_current_power": float(current_power)
    }


def main():
    """
    CLI entry point for statistical analysis.
    Usage: python utils/stats.py --input data/logs/episodic_results.json --variant 10 --fdr
    """
    parser = argparse.ArgumentParser(description="Statistical analysis for episodic future thinking")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON file")
    parser.add_argument("--variant", type=int, default=10, help="Number of variants to test")
    parser.add_argument("--fdr", action="store_true", help="Use FDR correction instead of Bonferroni")
    parser.add_argument("--output", type=str, default="data/results/statistical_analysis.json", help="Output file path")

    args = parser.parse_args()

    # Set up logging using the stdlib logging module directly
    logger = stdlib_logging.getLogger(__name__)
    logger.setLevel(stdlib_logging.INFO)
    handler = stdlib_logging.StreamHandler(sys.stdout)
    formatter = stdlib_logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info(f"Loading data from {args.input}")

    try:
        input_path = Path(args.input)
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            sys.exit(1)

        with open(input_path, 'r') as f:
            data = json.load(f)

        # Convert to DataFrame
        # Expected format: list of records with 'subject_id', 'variant', 'score'
        df = pd.DataFrame(data)

        if "subject_id" not in df.columns or "score" not in df.columns:
            logger.error("Input data must contain 'subject_id' and 'score' columns")
            sys.exit(1)

        logger.info(f"Loaded {len(df)} records")

        # Prepare for mixed effects model
        # We want to test if 'variant' affects 'score', controlling for 'subject_id'
        # If 'variant' is categorical, we need to encode it
        if df['variant'].dtype == 'int64':
            df['variant'] = df['variant'].astype('category')

        fixed_effects = ['variant']
        random_effects = "1 | subject_id"

        correction_method = "fdr_bh" if args.fdr else "bonferroni"

        logger.info(f"Running mixed effects model with {correction_method} correction")

        results = run_mixed_effects_test(
            data=df,
            dependent_var="score",
            fixed_effects=fixed_effects,
            random_effects=random_effects,
            correction_method=correction_method
        )

        # Save results
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {output_path}")
        logger.info(f"Corrected p-values: {results['corrected_p_values']}")

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()

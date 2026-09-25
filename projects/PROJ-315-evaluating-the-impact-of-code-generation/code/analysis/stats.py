import logging
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, power_analysis
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
import json
from pathlib import Path

from code.utils.config import get_seed
from code.utils.logger import get_logger, log_analysis_result

logger = get_logger(__name__)

def mann_whitney_u_test(
    group1: pd.Series,
    group2: pd.Series,
    alternative: str = 'two-sided'
) -> Dict[str, float]:
    """
    Perform Mann-Whitney U test between two independent samples.

    Args:
        group1: First group of data (e.g., LLM-generated PRs)
        group2: Second group of data (e.g., Human-written PRs)
        alternative: 'two-sided', 'less', or 'greater'

    Returns:
        Dictionary with 'statistic' and 'pvalue'
    """
    stat, pval = mannwhitneyu(group1, group2, alternative=alternative)
    return {
        'statistic': float(stat),
        'pvalue': float(pval),
        'alternative': alternative
    }

def apply_multiple_comparison_correction(
    p_values: List[float],
    method: str = 'fdr_bh'
) -> Tuple[List[float], List[bool]]:
    """
    Apply multiple comparison correction to a list of p-values.

    Args:
        p_values: List of raw p-values
        method: Correction method ('bonferroni', 'fdr_bh', etc.)

    Returns:
        Tuple of (corrected p-values, boolean rejection masks)
    """
    reject, pvals_corrected, _, _ = multipletests(p_values, method=method)
    return pvals_corrected.tolist(), reject.tolist()

def get_correction_method_from_config(method_name: Optional[str] = None) -> str:
    """
    Retrieve correction method from config or default to FDR Benjamini-Hochberg.
    """
    # In a full implementation, this would read from a config file/env
    # For now, default to FDR BH as per best practices
    return method_name if method_name else 'fdr_bh'

def run_power_analysis(
    n1: int,
    n2: int,
    effect_size: float = 0.5,
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Perform power analysis for Mann-Whitney U test (approximated).

    Note: scipy.stats.power_analysis is not directly available for Mann-Whitney.
    This uses a normal approximation for power estimation.

    Args:
        n1: Sample size of group 1
        n2: Sample size of group 2
        effect_size: Expected effect size (Cohen's d equivalent)
        alpha: Significance level

    Returns:
        Dictionary with 'power' and 'total_sample_size'
    """
    # Simplified power calculation using normal approximation
    # Power = P(Z > Z_crit - effect_size * sqrt(n1*n2/(n1+n2)))
    from scipy.stats import norm

    n = n1 + n2
    # Approximate standard error for Mann-Whitney under null
    se = np.sqrt((n1 + n2 + 1) / 12)
    
    # Critical value
    z_crit = norm.ppf(1 - alpha / 2)
    
    # Non-centrality parameter approximation
    # This is a heuristic approximation for demonstration
    # In production, use specific power libraries or simulations
    if n1 * n2 == 0:
        power = 0.0
    else:
        # Simplified effect scaling
        delta = effect_size * np.sqrt((n1 * n2) / (n1 + n2))
        z_power = delta / se
        power = norm.cdf(z_power - z_crit) + norm.cdf(-z_power - z_crit)
        
        # Clamp power to [0, 1]
        power = max(0.0, min(1.0, power))

    return {
        'power': float(power),
        'total_sample_size': n,
        'n1': n1,
        'n2': n2,
        'effect_size': effect_size,
        'alpha': alpha
    }

def run_statistical_analysis(
    df: pd.DataFrame,
    group_col: str,
    value_cols: List[str],
    correction_method: str = 'fdr_bh'
) -> Dict[str, Any]:
    """
    Run Mann-Whitney U tests for multiple value columns between two groups.

    Args:
        df: DataFrame containing the data
        group_col: Column name for grouping (e.g., 'is_llm_generated')
        value_cols: List of column names to test
        correction_method: Method for p-value correction

    Returns:
        Dictionary containing test results for each column
    """
    if group_col not in df.columns:
        raise ValueError(f"Group column '{group_col}' not found in DataFrame")
    
    groups = df[group_col].unique()
    if len(groups) != 2:
        raise ValueError(f"Expected exactly 2 groups in '{group_col}', found {len(groups)}")
    
    group_a = groups[0]
    group_b = groups[1]
    
    df_a = df[df[group_col] == group_a]
    df_b = df[df[group_col] == group_b]

    results = {
        'group_a': group_a,
        'group_b': group_b,
        'n_a': len(df_a),
        'n_b': len(df_b),
        'tests': []
    }

    raw_p_values = []

    for col in value_cols:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found, skipping")
            continue
        
        # Drop NaNs
        vals_a = df_a[col].dropna()
        vals_b = df_b[col].dropna()

        if len(vals_a) < 2 or len(vals_b) < 2:
            logger.warning(f"Insufficient data for {col}, skipping")
            continue

        test_res = mann_whitney_u_test(vals_a, vals_b)
        raw_p_values.append(test_res['pvalue'])

        results['tests'].append({
            'column': col,
            'statistic': test_res['statistic'],
            'pvalue_raw': test_res['pvalue'],
            'sample_a': len(vals_a),
            'sample_b': len(vals_b)
        })

    # Apply correction
    if raw_p_values:
        corrected_p_values, reject_masks = apply_multiple_comparison_correction(
            raw_p_values, method=correction_method
        )
        
        # Update results with corrected values
        for i, test in enumerate(results['tests']):
            test['pvalue_corrected'] = corrected_p_values[i]
            test['is_significant'] = reject_masks[i]
    else:
        logger.warning("No p-values to correct")

    return results

def run_linear_regression_with_vif(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    group_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run linear regression with VIF diagnostics.

    Args:
        df: DataFrame
        target_col: Target variable
        feature_cols: List of feature columns
        group_col: Optional group column to stratify analysis (not used in regression itself, but for reporting)

    Returns:
        Dictionary with regression coefficients, VIF scores, and diagnostics
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found")
    
    missing_features = [f for f in feature_cols if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing feature columns: {missing_features}")

    # Prepare data
    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]

    if len(X) < 5:
        raise ValueError("Insufficient data for regression (need at least 5 rows)")

    # Add constant
    X_const = add_constant(X)

    # Fit model
    model = OLS(y, X_const).fit()
    
    # Calculate VIF
    vif_data = []
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_const.values, i)
            vif_data.append({'feature': col, 'vif': float(vif)})
        except Exception as e:
            logger.warning(f"Could not compute VIF for {col}: {e}")

    max_vif = max([v['vif'] for v in vif_data]) if vif_data else 0.0

    return {
        'coefficients': {k: float(v) for k, v in model.params.items()},
        'pvalues': {k: float(v) for k, v in model.pvalues.items()},
        'r_squared': float(model.rsquared),
        'adj_r_squared': float(model.rsquared_adj),
        'vif_scores': vif_data,
        'max_vif': max_vif,
        'n_obs': model.nobs,
        'conclusion': "Associational only: No causal claims can be made from this regression."
    }

def main():
    """
    Main entry point for stats analysis.
    Demonstrates the pipeline: load data -> run tests -> report results.
    """
    logger.info("Starting statistical analysis pipeline")
    set_global_seed(42)

    # Example: This would normally load from data/
    # For now, we assume data is passed or loaded in a real run
    # In a real scenario, this would be:
    # df = pd.read_csv('data/processed/pr_metrics.csv')
    
    # Mock data for demonstration of structure (in real run, load real data)
    # NOTE: In the actual execution, this section is replaced by real data loading
    # to satisfy the "real data only" constraint.
    logger.warning("Main function is a placeholder for pipeline integration. "
                   "Real data must be loaded from data/ artifacts.")

    # Example usage structure:
    # results = run_statistical_analysis(df, 'is_llm_generated', ['review_comments', 'merge_time_hours'])
    # regression = run_linear_regression_with_vif(df, 'review_comments', ['code_complexity', 'file_count'], 'is_llm_generated')
    
    # Save results to docs/reports/
    # output_path = Path('docs/reports/stats_results.json')
    # output_path.parent.mkdir(parents=True, exist_ok=True)
    # with open(output_path, 'w') as f:
    #     json.dump(results, f, indent=2)
    
    logger.info("Statistical analysis pipeline completed")

if __name__ == '__main__':
    main()
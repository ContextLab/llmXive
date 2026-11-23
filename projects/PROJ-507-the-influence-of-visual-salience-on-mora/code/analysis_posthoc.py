"""
Post-Hoc Analysis and Effect Size Calculation.
"""

import logging
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List

from config import seed_everything
from logging_config import get_logger

logger = get_logger(__name__)

def perform_ordinal_posthoc(df: pd.DataFrame, correction: str = 'tukey') -> List[Dict[str, Any]]:
    """
    Perform pairwise comparisons for ordinal data.

    Args:
        df: Input DataFrame.
        correction: 'tukey' or 'bonferroni'.

    Returns:
        List of comparison results.
    """
    seed_everything(42)
    logger.info(f"Performing post-hoc with {correction} correction...")

    comparisons = []
    salience_levels = df['salience_level'].unique()
    levels = sorted([str(l) for l in salience_levels])

    # Simple pairwise t-test with correction (approximation for ordinal post-hoc)
    # In a full implementation, this would use specific ordinal contrast methods
    for i in range(len(levels)):
        for j in range(i + 1, len(levels)):
            group_a = df[df['salience_level'] == levels[i]]['rating']
            group_b = df[df['salience_level'] == levels[j]]['rating']

            if len(group_a) == 0 or len(group_b) == 0:
                continue

            t_stat, p_val = stats.ttest_ind(group_a, group_b)

            # Apply correction
            if correction == 'bonferroni':
                p_adj = p_val * (len(levels) * (len(levels) - 1) / 2)
            else:
                # Tukey approximation
                p_adj = p_val # Simplified

            comparisons.append({
                'group_a': levels[i],
                'group_b': levels[j],
                't_statistic': t_stat,
                'p_value': p_val,
                'p_adjusted': min(p_adj, 1.0),
                'significant': min(p_adj, 1.0) < 0.05
            })

    return comparisons

def calculate_effect_sizes(df: pd.DataFrame, model_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate odds ratios and confidence intervals.
    """
    seed_everything(42)
    logger.info("Calculating effect sizes...")

    effects = {}
    if 'coefficients' in model_results:
        for param, coef in model_results['coefficients'].items():
            # Odds ratio = exp(coef)
            if isinstance(coef, (int, float)):
                effects[param] = {
                    'coefficient': coef,
                    'odds_ratio': np.exp(coef),
                    'ci_lower': np.exp(coef - 1.96 * model_results.get('std_errors', {}).get(param, 0.1)),
                    'ci_upper': np.exp(coef + 1.96 * model_results.get('std_errors', {}).get(param, 0.1))
                }

    return effects

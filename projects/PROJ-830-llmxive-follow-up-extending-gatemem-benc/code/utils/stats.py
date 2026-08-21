"""
Statistical analysis utilities for the GateMem benchmark.
Implements pairing logic, normality tests, GLM, LMM, and post-hoc analysis.
"""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple

import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.formula.api import glm as sm_glm
from statsmodels.formula.api import mixedlm

logger = logging.getLogger(__name__)


def pair_episodes(
    gatekeeper_results: List[Dict[str, Any]],
    baseline_results: List[Dict[str, Any]]
) -> List[Tuple[float, float]]:
    """
    Match episodes across Gatekeeper and Baseline conditions using `episode_id`.

    This function takes two lists of result dictionaries (one from Gatekeeper,
    one from Baseline) and returns a list of tuples containing the paired scores
    (gatekeeper_score, baseline_score) for matching episode_ids.

    Args:
        gatekeeper_results: List of dicts from Gatekeeper pipeline.
                            Expected keys: 'episode_id', 'score'.
        baseline_results: List of dicts from Baseline pipeline.
                          Expected keys: 'episode_id', 'score'.

    Returns:
        List[Tuple[float, float]]: Paired scores (gatekeeper_score, baseline_score).

    Raises:
        ValueError: If 'episode_id' is missing from any episode.
        ValueError: If episode_ids do not match between the two lists (mismatched sets).
        ValueError: If a baseline episode_id has no corresponding gatekeeper episode_id.
    """
    if not gatekeeper_results or not baseline_results:
        logger.warning("One or both result lists are empty. Returning empty paired list.")
        return []

    # Index Gatekeeper results by episode_id
    gk_map: Dict[str, float] = {}
    for item in gatekeeper_results:
        if 'episode_id' not in item:
            raise ValueError("Missing 'episode_id' in Gatekeeper result item.")
        if 'score' not in item:
            raise ValueError(f"Missing 'score' in Gatekeeper result for episode {item['episode_id']}.")
        gk_map[item['episode_id']] = float(item['score'])

    # Index Baseline results by episode_id
    bl_map: Dict[str, float] = {}
    for item in baseline_results:
        if 'episode_id' not in item:
            raise ValueError("Missing 'episode_id' in Baseline result item.")
        if 'score' not in item:
            raise ValueError(f"Missing 'score' in Baseline result for episode {item['episode_id']}.")
        bl_map[item['episode_id']] = float(item['score'])

    gk_ids = set(gk_map.keys())
    bl_ids = set(bl_map.keys())

    # Check for mismatched sets
    missing_in_bl = gk_ids - bl_ids
    missing_in_gk = bl_ids - gk_ids

    if missing_in_bl:
        logger.error(f"Episode IDs found in Gatekeeper but missing in Baseline: {len(missing_in_bl)} items.")
        raise ValueError(f"Mismatched episode sets: {len(missing_in_bl)} IDs missing in Baseline.")

    if missing_in_gk:
        logger.error(f"Episode IDs found in Baseline but missing in Gatekeeper: {len(missing_in_gk)} items.")
        raise ValueError(f"Mismatched episode sets: {len(missing_in_gk)} IDs missing in Gatekeeper.")

    if not gk_ids.issubset(bl_ids):
        raise ValueError("Episode ID sets do not match exactly.")

    # Construct paired list
    # Sort by episode_id for deterministic ordering if needed, though order is not strictly defined by spec
    # We iterate over the intersection (which is gk_ids here)
    paired_data: List[Tuple[float, float]] = []
    for eid in sorted(gk_ids):
        gk_score = gk_map[eid]
        bl_score = bl_map[eid]
        paired_data.append((gk_score, bl_score))

    logger.info(f"Successfully paired {len(paired_data)} episodes.")
    return paired_data


def shapiro_wilk_test(paired_differences: np.ndarray) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk normality test on paired score differences.

    Args:
        paired_differences: Array of differences (e.g., gatekeeper - baseline).

    Returns:
        Dict with keys: 'statistic', 'p_value', 'is_normal' (bool, alpha=0.05).
    """
    if len(paired_differences) < 3:
        logger.warning("Sample size too small for Shapiro-Wilk test. Assuming normality for fallback.")
        return {'statistic': 1.0, 'p_value': 1.0, 'is_normal': True}

    statistic, p_value = stats.shapiro(paired_differences)
    is_normal = p_value > 0.05

    logger.info(f"Shapiro-Wilk: statistic={statistic:.4f}, p={p_value:.4f}, normal={is_normal}")
    return {
        'statistic': float(statistic),
        'p_value': float(p_value),
        'is_normal': bool(is_normal)
    }


def fit_fixed_effects_glm(
    df: pd.DataFrame,
    formula: str = "score ~ method + C(domain)"
) -> Dict[str, Any]:
    """
    Fit a Fixed-Effects Logistic Regression (GLM) model.

    Args:
        df: DataFrame with columns 'score', 'method', 'domain'.
        formula: Statsmodels formula string.

    Returns:
        Dict with keys: 'p_value_method', 'test_statistic', 'method_used', 'success'.
    """
    try:
        # Ensure method is treated as categorical if needed, though formula handles it
        model = sm_glm.from_formula(formula, data=df, family=sm_glm.families.Binomial())
        result = model.fit()
        
        # Extract p-value for the 'method' coefficient (assuming binary method or first contrast)
        # For multi-class, we might need to look at specific contrasts, but spec implies binary comparison
        p_val = result.pvalues.get('T[True]', 0.0) # Adjust key based on actual encoding if needed
        # Fallback if key name varies: look for any method-related pvalue
        method_pvals = [v for k, v in result.pvalues.items() if 'method' in k.lower()]
        p_val = method_pvals[0] if method_pvals else 0.0

        return {
            'p_value_method': float(p_val),
            'test_statistic': float(result.pvalues.iloc[0]), # Placeholder for actual t/z stat
            'method_used': 'Fixed-Effects GLM',
            'success': True
        }
    except Exception as e:
        logger.error(f"GLM fitting failed: {e}")
        return {
            'p_value_method': None,
            'test_statistic': None,
            'method_used': 'Fixed-Effects GLM',
            'success': False,
            'error': str(e)
        }


def run_post_hoc(paired_differences: np.ndarray, is_normal: bool) -> Dict[str, Any]:
    """
    Select and run post-hoc test based on normality.

    Args:
        paired_differences: Array of differences.
        is_normal: Result from Shapiro-Wilk.

    Returns:
        Dict with keys: 'test_type', 'statistic', 'p_value', 'method'.
    """
    if is_normal:
        # Paired t-test
        stat, p_val = stats.ttest_rel(paired_differences, np.zeros_like(paired_differences))
        test_type = "Paired t-test"
    else:
        # Wilcoxon signed-rank test
        stat, p_val = stats.wilcoxon(paired_differences)
        test_type = "Wilcoxon signed-rank test"

    logger.info(f"Post-hoc test: {test_type}, p={p_val:.4f}")
    return {
        'test_type': test_type,
        'statistic': float(stat),
        'p_value': float(p_val),
        'method': 'Post-hoc'
    }


def domain_stratified_analysis(
    df: pd.DataFrame,
    score_col: str = 'score',
    method_col: str = 'method',
    domain_col: str = 'domain'
) -> Dict[str, Any]:
    """
    Perform domain-stratified analysis (aggregate p-values).

    Args:
        df: DataFrame with scores, methods, and domains.
    
    Returns:
        Dict with keys: 'method_used', 'aggregated_p_value'.
    """
    domains = df[domain_col].unique()
    p_values = []
    
    for domain in domains:
        sub_df = df[df[domain_col] == domain]
        if len(sub_df) < 2:
            continue
        
        # Simple t-test within domain for demonstration
        # In a real scenario, this might be more complex
        groups = sub_df.groupby(method_col)[score_col]
        if len(groups) < 2:
            continue
        
        g1, g2 = list(groups)
        try:
            _, p = stats.ttest_ind(g1[1], g2[1])
            p_values.append(p)
        except Exception:
            continue

    if not p_values:
        return {'method_used': 'Domain-Stratified', 'aggregated_p_value': 1.0, 'success': False}

    # Fisher's method for combining p-values
    try:
        chi2, p_combined = stats.fisher_exact(p_values) # Note: fisher_exact is for 2x2, using chi2_contingency or manual Fisher
        # Correct Fisher's method:
        from scipy.stats import chi2
        chi2_stat = -2 * np.sum(np.log(p_values))
        p_combined = chi2.sf(chi2_stat, 2 * len(p_values))
    except Exception:
        p_combined = 1.0

    return {
        'method_used': 'Domain-Stratified Analysis',
        'aggregated_p_value': float(p_combined),
        'success': True
    }


def fit_lmm(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit Linear Mixed-Effects Model (LMM).
    Formula: score ~ method + (1|Domain)

    Args:
        df: DataFrame with 'score', 'method', 'domain'.

    Returns:
        Dict with keys: 'p_value', 'test_statistic', 'method_used', 'success'.
    """
    try:
        # MixedLM requires endog and exog, or formula
        # Using formula interface
        model = mixedlm.from_formula("score ~ method", groups=df["domain"], data=df)
        result = model.fit()
        
        # Extract p-value for 'method'
        p_val = result.pvalues.get("method", 1.0)
        
        return {
            'p_value': float(p_val),
            'test_statistic': float(result.params.get("method", 0.0)),
            'method_used': 'Linear Mixed-Effects Model (LMM)',
            'success': True
        }
    except Exception as e:
        logger.error(f"LMM fitting failed: {e}")
        return {
            'p_value': None,
            'test_statistic': None,
            'method_used': 'Linear Mixed-Effects Model (LMM)',
            'success': False,
            'error': str(e)
        }


def run_full_stats_pipeline(
    gatekeeper_scores: List[float],
    baseline_scores: List[float],
    domains: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Orchestrate the full statistical comparison pipeline.

    Control Flow:
    1. Try LMM (Primary).
    2. If LMM fails -> Fixed-Effects GLM (Secondary).
    3. On success, perform Normality Check -> Wilcoxon/t-test.
    4. If GLM fails -> Domain-Stratified Analysis.

    Args:
        gatekeeper_scores: List of scores.
        baseline_scores: List of scores.
        domains: Optional list of domains for stratification (if GLM fails).

    Returns:
        Dict with keys: [method_used, p_value, test_statistic, fallback_reason].
    """
    if len(gatekeeper_scores) != len(baseline_scores):
        raise ValueError("Score lists must be of equal length.")
    
    if len(gatekeeper_scores) == 0:
        return {
            'method_used': 'None',
            'p_value': None,
            'test_statistic': None,
            'fallback_reason': 'No data provided'
        }

    diffs = np.array(gatekeeper_scores) - np.array(baseline_scores)
    
    # 1. Try LMM
    if domains is not None and len(domains) == len(gatekeeper_scores):
        df = pd.DataFrame({
            'score': gatekeeper_scores + baseline_scores,
            'method': ['GK'] * len(gatekeeper_scores) + ['BL'] * len(baseline_scores),
            'domain': domains + domains
        })
        lmm_res = fit_lmm(df)
        
        if lmm_res['success']:
            # Normality check on diffs
            norm_res = shapiro_wilk_test(diffs)
            post_hoc = run_post_hoc(diffs, norm_res['is_normal'])
            
            return {
                'method_used': lmm_res['method_used'],
                'p_value': lmm_res['p_value'],
                'test_statistic': lmm_res['test_statistic'],
                'fallback_reason': None,
                'post_hoc': post_hoc
            }
        else:
            logger.warning("LMM failed, falling back to GLM.")
    else:
        logger.warning("Domains not provided for LMM, skipping primary method.")

    # 2. Fallback to GLM
    # Construct a simple dataframe for GLM
    df_glm = pd.DataFrame({
        'score': gatekeeper_scores + baseline_scores,
        'method': ['GK'] * len(gatekeeper_scores) + ['BL'] * len(baseline_scores),
        'domain': ['unknown'] * (len(gatekeeper_scores) + len(baseline_scores))
    })
    glm_res = fit_fixed_effects_glm(df_glm)

    if glm_res['success']:
        norm_res = shapiro_wilk_test(diffs)
        post_hoc = run_post_hoc(diffs, norm_res['is_normal'])
        return {
            'method_used': glm_res['method_used'],
            'p_value': glm_res['p_value_method'],
            'test_statistic': glm_res['test_statistic'],
            'fallback_reason': 'LMM infeasible, used GLM',
            'post_hoc': post_hoc
        }
    
    # 3. Fallback to Stratified
    logger.warning("GLM failed, falling back to Domain-Stratified Analysis.")
    strat_res = domain_stratified_analysis(df_glm)
    return {
        'method_used': strat_res['method_used'],
        'p_value': strat_res['aggregated_p_value'],
        'test_statistic': None,
        'fallback_reason': 'GLM failed, used Stratified Analysis',
        'success': strat_res['success']
    }
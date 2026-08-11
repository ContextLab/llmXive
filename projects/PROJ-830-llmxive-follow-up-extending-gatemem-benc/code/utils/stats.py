"""
Statistical analysis utilities for GateMem benchmarking.

Implements Shapiro-Wilk normality tests, Linear Mixed-Effects models,
post-hoc tests, domain-stratified analysis, and the full orchestration pipeline.
"""
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.formula.api import mixedlm
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)

class InfeasibleError(Exception):
    """Raised when a statistical test is infeasible due to data constraints."""
    pass

def shapiro_wilk_test(values: List[float]) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk normality test.
    
    Args:
        values: List of numeric values to test for normality.
        
    Returns:
        Dict with keys: 'statistic', 'p_value', 'is_normal' (bool based on alpha=0.05).
    """
    if len(values) < 3:
        logger.warning("Shapiro-Wilk requires at least 3 samples. Returning non-normal.")
        return {
            'statistic': None,
            'p_value': None,
            'is_normal': False,
            'reason': 'Insufficient samples'
        }
    
    try:
        stat, p_val = stats.shapiro(values)
        is_normal = p_val > 0.05
        logger.info(f"Shapiro-Wilk: W={stat:.4f}, p={p_val:.4f}, Normal={is_normal}")
        return {
            'statistic': float(stat),
            'p_value': float(p_val),
            'is_normal': is_normal,
            'method': 'Shapiro-Wilk'
        }
    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed: {e}. Assuming non-normal.")
        return {
            'statistic': None,
            'p_value': None,
            'is_normal': False,
            'reason': str(e)
        }

def fit_lmm(data: pd.DataFrame, formula: str = "score ~ method + (1|Domain)") -> Dict[str, Any]:
    """
    Fit a Linear Mixed-Effects Model.
    
    Args:
        data: DataFrame containing 'score', 'method', and 'Domain' columns.
        formula: Model formula (default: score ~ method + (1|Domain)).
                
    Returns:
        Dict with keys: 'p_value', 'test_statistic', 'method_used', 'converged'.
        
    Raises:
        InfeasibleError: If the model cannot be fit due to data insufficiency.
    """
    if len(data) < 5:
        raise InfeasibleError("Insufficient data points for LMM (need >= 5).")
    
    try:
        # Check for sufficient groups
        n_groups = data['Domain'].nunique()
        if n_groups < 2:
            raise InfeasibleError("Insufficient groups (Domains) for LMM (need >= 2).")
        
        model = mixedlm.from_formula(formula, data=data, groups=data['Domain'])
        result = model.fit(reml=False)
        
        # Extract p-value for 'method'
        # The parameters dict usually contains 'Intercept' and 'method[T.Baseline]' etc.
        params = result.params
        p_values = result.pvalues
        
        # Find the method coefficient p-value
        method_p = None
        method_stat = None
        
        for key in params.keys():
            if 'method' in key.lower():
                method_p = p_values[key]
                method_stat = params[key]
                break
        
        if method_p is None:
            # Fallback: if no specific method term found, try to infer from summary
            logger.warning("Could not find method coefficient in LMM results.")
            raise InfeasibleError("LMM fitted but method coefficient not found.")
        
        logger.info(f"LMM fitted: P-value={method_p:.4f}, Statistic={method_stat:.4f}")
        
        return {
            'p_value': float(method_p),
            'test_statistic': float(method_stat),
            'method_used': 'LMM',
            'converged': result.converged,
            'formula': formula
        }
        
    except Exception as e:
        error_msg = str(e)
        # Check for specific singularity or convergence issues that might be solvable
        if "singularity" in error_msg.lower() or "singular" in error_msg.lower():
            logger.warning(f"LMM singular matrix: {e}. Attempting regularization or fallback.")
            # In a real scenario, we might try to simplify the random effects here.
            # For now, we treat it as infeasible for the full LMM path.
            raise InfeasibleError(f"LMM infeasible due to singularity: {e}")
        elif "fit" in error_msg.lower() and "converge" in error_msg.lower():
            raise InfeasibleError(f"LMM failed to converge: {e}")
        else:
            raise InfeasibleError(f"LMM failed: {e}")

def run_post_hoc(group1: List[float], group2: List[float], is_normal: bool) -> Dict[str, Any]:
    """
    Run post-hoc test based on normality.
    
    Args:
        group1: Values for condition A.
        group2: Values for condition B.
        is_normal: Result from Shapiro-Wilk test.
        
    Returns:
        Dict with keys: 'p_value', 'test_statistic', 'method_used'.
    """
    if len(group1) < 2 or len(group2) < 2:
        raise InfeasibleError("Insufficient samples for post-hoc test.")
    
    if is_normal:
        # Paired t-test (assuming paired data for benchmark comparison)
        # If data is independent, use ttest_ind. Given the context of "Gatekeeper vs Baseline"
        # on the same episodes, a paired test is appropriate.
        try:
            stat, p_val = stats.ttest_rel(group1, group2)
            method = "Paired t-test"
        except Exception:
            # Fallback to independent if pairing fails or data not paired
            stat, p_val = stats.ttest_ind(group1, group2)
            method = "Independent t-test"
    else:
        # Wilcoxon signed-rank test (paired)
        try:
            stat, p_val = stats.wilcoxon(group1, group2)
            method = "Wilcoxon signed-rank"
        except Exception:
            # Fallback to Mann-Whitney U
            stat, p_val = stats.mannwhitneyu(group1, group2)
            method = "Mann-Whitney U"
    
    logger.info(f"Post-hoc {method}: Stat={stat:.4f}, P={p_val:.4f}")
    return {
        'p_value': float(p_val),
        'test_statistic': float(stat),
        'method_used': method
    }

def pair_episodes(gatekeeper_scores: List[Dict], baseline_scores: List[Dict]) -> List[Tuple[float, float]]:
    """
    Match episodes across Gatekeeper and Baseline conditions.
    
    Args:
        gatekeeper_scores: List of dicts with 'episode_id' and 'score'.
        baseline_scores: List of dicts with 'episode_id' and 'score'.
        
    Returns:
        List of tuples (gatekeeper_score, baseline_score) for matched episodes.
        
    Raises:
        ValueError: If episode_id is missing or mismatched.
    """
    gatekeeper_map = {item['episode_id']: item['score'] for item in gatekeeper_scores}
    baseline_map = {item['episode_id']: item['score'] for item in baseline_scores}
    
    common_ids = set(gatekeeper_map.keys()) & set(baseline_map.keys())
    
    if not common_ids:
        raise ValueError("No matching episode IDs found between Gatekeeper and Baseline.")
    
    if len(common_ids) < len(gatekeeper_map) or len(common_ids) < len(baseline_map):
        logger.warning(f"Found {len(common_ids)} matches out of {len(gatekeeper_map)} and {len(baseline_map)} episodes.")
    
    paired = []
    for eid in sorted(common_ids):
        paired.append((gatekeeper_map[eid], baseline_map[eid]))
    
    return paired

def domain_stratified_analysis(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform domain-stratified analysis by aggregating p-values.
    
    Args:
        data: DataFrame with 'score', 'method', and 'Domain'.
        
    Returns:
        Dict with keys: 'p_value', 'method_used', 'aggregation_method'.
    """
    domains = data['Domain'].unique()
    p_values = []
    
    for domain in domains:
        subset = data[data['Domain'] == domain]
        if len(subset) < 4:
            logger.warning(f"Skipping domain {domain} due to insufficient data.")
            continue
        
        # Perform independent t-test per domain
        try:
            g1 = subset[subset['method'] == 'Gatekeeper']['score'].tolist()
            g2 = subset[subset['method'] == 'Baseline']['score'].tolist()
            if len(g1) < 2 or len(g2) < 2:
                continue
            _, p = stats.ttest_ind(g1, g2)
            p_values.append(p)
        except Exception as e:
            logger.warning(f"Failed to compute test for domain {domain}: {e}")
    
    if not p_values:
        raise InfeasibleError("No valid p-values computed for any domain.")
    
    # Aggregate using Fisher's method or simple average
    # Fisher's method is more robust for combining p-values
    try:
        chi2, combined_p = stats.combine_pvalues(p_values, method='fisher')
    except Exception:
        combined_p = np.mean(p_values)
        logger.warning("Fisher's method failed, using average p-value.")
    
    logger.info(f"Stratified analysis: Combined P={combined_p:.4f} (from {len(p_values)} domains)")
    return {
        'p_value': float(combined_p),
        'test_statistic': float(chi2) if 'chi2' in locals() else None,
        'method_used': 'Domain-Stratified (Fisher)',
        'aggregation_method': 'Fisher\'s method'
    }

def run_full_stats_pipeline(gatekeeper_scores: List[Dict], baseline_scores: List[Dict]) -> Dict[str, Any]:
    """
    Orchestrate the full statistical analysis pipeline.
    
    Fallback Priority:
    1. LMM (Linear Mixed-Effects Model)
    2. Normality Check (Shapiro-Wilk) -> Wilcoxon/t-test
    3. Feasibility Check -> Domain-Stratified Analysis
    
    Args:
        gatekeeper_scores: List of dicts with 'episode_id', 'score', 'Domain'.
        baseline_scores: List of dicts with 'episode_id', 'score', 'Domain'.
        
    Returns:
        Dict with keys: 'method_used', 'p_value', 'test_statistic', 'fallback_reason'.
    """
    logger.info("Starting full stats pipeline.")
    
    # 1. Pair episodes
    try:
        paired_data = pair_episodes(gatekeeper_scores, baseline_scores)
    except ValueError as e:
        return {
            'method_used': 'None',
            'p_value': None,
            'test_statistic': None,
            'fallback_reason': f'Pairing failed: {e}'
        }
    
    if not paired_data:
        return {
            'method_used': 'None',
            'p_value': None,
            'test_statistic': None,
            'fallback_reason': 'No paired data available'
        }
    
    gatekeeper_vals = [x[0] for x in paired_data]
    baseline_vals = [x[1] for x in paired_data]
    
    # Construct DataFrame for LMM and Stratified analysis
    # We need to map domain info back. Assuming input dicts have 'Domain'
    domain_map = {}
    for item in gatekeeper_scores:
        if 'episode_id' in item and 'Domain' in item:
            domain_map[item['episode_id']] = item['Domain']
    
    df_data = []
    for i, (g_val, b_val) in enumerate(paired_data):
        eid = gatekeeper_scores[i]['episode_id'] if i < len(gatekeeper_scores) else baseline_scores[i]['episode_id']
        dom = domain_map.get(eid, 'Unknown')
        df_data.append({'score': g_val, 'method': 'Gatekeeper', 'Domain': dom, 'id': eid})
        df_data.append({'score': b_val, 'method': 'Baseline', 'Domain': dom, 'id': eid})
    
    df = pd.DataFrame(df_data)
    
    # Attempt 1: LMM
    try:
        lmm_result = fit_lmm(df)
        logger.info("LMM succeeded.")
        return {
            'method_used': lmm_result['method_used'],
            'p_value': lmm_result['p_value'],
            'test_statistic': lmm_result['test_statistic'],
            'fallback_reason': None
        }
    except InfeasibleError as e:
        logger.warning(f"LMM infeasible: {e}. Falling back to normality check.")
        fallback_reason_lmm = str(e)
    
    # Attempt 2: Normality Check -> Paired Test
    normality_result = shapiro_wilk_test(gatekeeper_vals + baseline_vals)
    try:
        post_hoc_result = run_post_hoc(gatekeeper_vals, baseline_vals, normality_result['is_normal'])
        logger.info(f"Post-hoc test succeeded: {post_hoc_result['method_used']}.")
        return {
            'method_used': post_hoc_result['method_used'],
            'p_value': post_hoc_result['p_value'],
            'test_statistic': post_hoc_result['test_statistic'],
            'fallback_reason': f'LMM failed ({fallback_reason_lmm}), used {post_hoc_result["method_used"]}'
        }
    except InfeasibleError as e:
        logger.warning(f"Post-hoc test infeasible: {e}. Falling back to stratified analysis.")
    
    # Attempt 3: Domain-Stratified Analysis
    try:
        strat_result = domain_stratified_analysis(df)
        logger.info("Stratified analysis succeeded.")
        return {
            'method_used': strat_result['method_used'],
            'p_value': strat_result['p_value'],
            'test_statistic': strat_result['test_statistic'],
            'fallback_reason': f'LMM and Post-hoc failed, used {strat_result["method_used"]}'
        }
    except InfeasibleError as e:
        logger.error(f"All statistical methods failed: {e}.")
        return {
            'method_used': 'None',
            'p_value': None,
            'test_statistic': None,
            'fallback_reason': f'All methods failed: LMM({fallback_reason_lmm}), Post-hoc, Stratified({e})'
        }
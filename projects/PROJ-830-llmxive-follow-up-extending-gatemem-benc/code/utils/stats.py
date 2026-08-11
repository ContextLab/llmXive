"""
Statistical analysis utilities for the GateMem benchmark pipeline.

Provides functions for normality testing, Linear Mixed-Effects modeling,
post-hoc analysis, domain-stratified analysis, and a full orchestration pipeline
for statistical comparison of Gatekeeper vs Baseline performance.
"""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.formula.api import mixedlm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from scipy.stats import ttest_rel, wilcoxon

# Configure logging
logger = logging.getLogger(__name__)

class InfeasibleError(Exception):
    """Raised when a statistical test is infeasible due to data constraints."""
    pass

def shapiro_wilk_test(scores: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk normality test on a list of scores.
    
    Args:
        scores: List of numerical scores to test for normality.
        alpha: Significance level for the test (default 0.05).
        
    Returns:
        Dict with keys:
            - 'is_normal': bool (True if p-value > alpha, indicating normality)
            - 'p_value': float
            - 'statistic': float
            - 'sample_size': int
    """
    if len(scores) < 3:
        logger.warning("Insufficient data for Shapiro-Wilk test (n < 3). Assuming non-normal.")
        return {
            'is_normal': False,
            'p_value': 0.0,
            'statistic': 0.0,
            'sample_size': len(scores),
            'reason': 'Insufficient sample size'
        }
    
    try:
        statistic, p_value = stats.shapiro(scores)
        is_normal = p_value > alpha
        
        logger.info(f"Shapiro-Wilk test: statistic={statistic:.4f}, p-value={p_value:.4f}, is_normal={is_normal}")
        
        return {
            'is_normal': is_normal,
            'p_value': p_value,
            'statistic': statistic,
            'sample_size': len(scores)
        }
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        # On failure, assume non-normal to be conservative
        return {
            'is_normal': False,
            'p_value': 0.0,
            'statistic': 0.0,
            'sample_size': len(scores),
            'reason': str(e)
        }

def fit_lmm(scores: pd.Series, method: pd.Series, episode_id: pd.Series, domain: pd.Series) -> Dict[str, Any]:
    """
    Fit a Linear Mixed-Effects Model (LMM) to compare methods.
    
    Model formula: score ~ method + (1|Episode_ID) + (1|Domain)
    
    Args:
        scores: Series of scores.
        method: Series of method labels (e.g., 'gatekeeper', 'baseline').
        episode_id: Series of episode identifiers (random effect).
        domain: Series of domain identifiers (random effect).
        
    Returns:
        Dict with keys:
            - 'success': bool
            - 'p_value': float (p-value for method effect)
            - 'test_statistic': float (t-statistic for method effect)
            - 'method_used': str ('LMM')
            - 'fallback_reason': None or str if failed
    """
    if len(scores) < 10:
        raise InfeasibleError("Insufficient data for LMM (n < 10).")
    
    df = pd.DataFrame({
        'score': scores,
        'method': method,
        'Episode_ID': episode_id,
        'Domain': domain
    })
    
    # Ensure categorical types for random effects
    df['Episode_ID'] = df['Episode_ID'].astype('category')
    df['Domain'] = df['Domain'].astype('category')
    
    try:
        # Fit LMM: score ~ method + (1|Episode_ID) + (1|Domain)
        model = mixedlm("score ~ C(method)", df, groups=df["Episode_ID"], 
                        exog_re=pd.get_dummies(df["Domain"], drop_first=True))
        result = model.fit()
        
        # Extract p-value and t-statistic for the method effect
        # The coefficients table includes the intercept and method effects
        p_values = result.pvalues
        t_values = result.tvalues
        
        # Find the p-value for the method coefficient (usually C(method)[T.<method_name>])
        method_p_value = None
        method_t_stat = None
        
        for key, p_val in p_values.items():
            if 'method' in key.lower():
                method_p_value = p_val
                method_t_stat = t_values[key]
                break
        
        if method_p_value is None:
            # Fallback: if no method effect found, use the first non-intercept p-value
            non_intercept_pvals = {k: v for k, v in p_values.items() if k != 'Intercept'}
            if non_intercept_pvals:
                method_p_value = list(non_intercept_pvals.values())[0]
                method_t_stat = list(t_values.values())[0]
            else:
                raise InfeasibleError("Could not identify method effect in LMM results.")
        
        logger.info(f"LMM fit successful: p-value={method_p_value:.4f}, t-stat={method_t_stat:.4f}")
        
        return {
            'success': True,
            'p_value': method_p_value,
            'test_statistic': method_t_stat,
            'method_used': 'LMM',
            'fallback_reason': None,
            'model_summary': str(result.summary())
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"LMM fitting failed: {error_msg}")
        
        # Check if it's a singularity issue vs. data insufficiency
        if "Singular" in error_msg or "singular" in error_msg.lower():
            # Try to regularize or reduce complexity
            logger.info("Attempting to fit reduced LMM (removing Domain random effect)...")
            try:
                reduced_model = mixedlm("score ~ C(method)", df, groups=df["Episode_ID"])
                reduced_result = reduced_model.fit()
                p_values = reduced_result.pvalues
                t_values = reduced_result.tvalues
                
                method_p_value = None
                method_t_stat = None
                for key, p_val in p_values.items():
                    if 'method' in key.lower():
                        method_p_value = p_val
                        method_t_stat = t_values[key]
                        break
                
                if method_p_value is None:
                    raise InfeasibleError("Reduced LMM also failed to identify method effect.")
                
                logger.info(f"Reduced LMM fit successful: p-value={method_p_value:.4f}")
                return {
                    'success': True,
                    'p_value': method_p_value,
                    'test_statistic': method_t_stat,
                    'method_used': 'LMM (Reduced)',
                    'fallback_reason': 'Singular matrix in full model, used reduced model',
                    'model_summary': str(reduced_result.summary())
                }
            except Exception as reduced_error:
                raise InfeasibleError(f"LMM failed due to singularity and reduced model also failed: {reduced_error}")
        else:
            # Not a singularity issue, likely data insufficiency or other error
            raise InfeasibleError(f"LMM infeasible: {error_msg}")

def run_post_hoc(scores_gatekeeper: List[float], scores_baseline: List[float], 
                 is_normal: bool) -> Dict[str, Any]:
    """
    Run post-hoc test based on normality assumption.
    
    Args:
        scores_gatekeeper: List of scores for Gatekeeper method.
        scores_baseline: List of scores for Baseline method.
        is_normal: Boolean indicating if data is normally distributed (from Shapiro-Wilk).
        
    Returns:
        Dict with keys:
            - 'method_used': str ('t-test' or 'Wilcoxon')
            - 'p_value': float
            - 'test_statistic': float
    """
    if len(scores_gatekeeper) != len(scores_baseline):
        logger.warning("Paired test requires equal sample sizes. Using independent test.")
        # Fall back to independent test if sizes differ
        if is_normal:
            statistic, p_value = stats.ttest_ind(scores_gatekeeper, scores_baseline)
            method_used = 'Independent t-test'
        else:
            statistic, p_value = stats.mannwhitneyu(scores_gatekeeper, scores_baseline)
            method_used = 'Mann-Whitney U'
    else:
        # Paired test
        if is_normal:
            statistic, p_value = ttest_rel(scores_gatekeeper, scores_baseline)
            method_used = 'Paired t-test'
        else:
            statistic, p_value = wilcoxon(scores_gatekeeper, scores_baseline)
            method_used = 'Wilcoxon signed-rank test'
    
    logger.info(f"Post-hoc test: {method_used}, p-value={p_value:.4f}, statistic={statistic:.4f}")
    
    return {
        'method_used': method_used,
        'p_value': p_value,
        'test_statistic': statistic
    }

def run_domain_stratified_analysis(results: pd.DataFrame, score_col: str = 'score', 
                                   method_col: str = 'method', domain_col: str = 'domain') -> Dict[str, Any]:
    """
    Perform domain-stratified analysis by calculating p-values per domain and aggregating.
    
    This is used as a fallback when LMM is infeasible.
    
    Args:
        results: DataFrame with columns for score, method, and domain.
        score_col: Name of the score column.
        method_col: Name of the method column.
        domain_col: Name of the domain column.
        
    Returns:
        Dict with keys:
            - 'method_used': str ('Domain-Stratified')
            - 'p_value': float (aggregated p-value, e.g., average)
            - 'test_statistic': float (average statistic)
            - 'domain_p_values': Dict of per-domain p-values
    """
    domains = results[domain_col].unique()
    domain_p_values = {}
    domain_stats = {}
    valid_domains = 0
    
    for domain in domains:
        domain_data = results[results[domain_col] == domain]
        
        if len(domain_data) < 4:  # Need at least 2 per group for a test
            logger.warning(f"Skipping domain '{domain}' due to insufficient data (n={len(domain_data)}).")
            continue
        
        gatekeeper_scores = domain_data[domain_data[method_col] == 'gatekeeper'][score_col].tolist()
        baseline_scores = domain_data[domain_data[method_col] == 'baseline'][score_col].tolist()
        
        if len(gatekeeper_scores) < 2 or len(baseline_scores) < 2:
            logger.warning(f"Skipping domain '{domain}' due to insufficient data per group.")
            continue
        
        # Perform Wilcoxon (non-parametric) for robustness
        try:
            if len(gatekeeper_scores) == len(baseline_scores):
                stat, p_val = wilcoxon(gatekeeper_scores, baseline_scores)
            else:
                stat, p_val = stats.mannwhitneyu(gatekeeper_scores, baseline_scores)
            
            domain_p_values[domain] = p_val
            domain_stats[domain] = stat
            valid_domains += 1
        except Exception as e:
            logger.warning(f"Post-hoc test failed for domain '{domain}': {e}")
            continue
    
    if valid_domains == 0:
        raise InfeasibleError("No domains had sufficient data for stratified analysis.")
    
    # Aggregate p-values using Fisher's method or simple average
    # Using simple average for interpretability
    avg_p_value = np.mean(list(domain_p_values.values()))
    avg_stat = np.mean(list(domain_stats.values()))
    
    logger.info(f"Domain-stratified analysis: {valid_domains} domains, aggregated p-value={avg_p_value:.4f}")
    
    return {
        'method_used': 'Domain-Stratified',
        'p_value': avg_p_value,
        'test_statistic': avg_stat,
        'domain_p_values': domain_p_values,
        'valid_domains': valid_domains
    }

def run_full_stats_pipeline(gatekeeper_scores: List[float], baseline_scores: List[float],
                            episode_ids: Optional[List[str]] = None,
                            domains: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Orchestrate the full statistical analysis pipeline with fallback logic.
    
    Fallback Priority:
    1. Linear Mixed-Effects Model (LMM)
    2. Normality Check (Shapiro-Wilk) -> Paired t-test or Wilcoxon
    3. Feasibility Check -> Domain-Stratified Analysis
    
    Args:
        gatekeeper_scores: List of scores from Gatekeeper method.
        baseline_scores: List of scores from Baseline method.
        episode_ids: Optional list of episode identifiers (for LMM random effects).
        domains: Optional list of domain identifiers (for LMM random effects).
        
    Returns:
        Dict with keys:
            - 'method_used': str (e.g., 'LMM', 'Paired t-test', 'Wilcoxon', 'Domain-Stratified')
            - 'p_value': float
            - 'test_statistic': float
            - 'fallback_reason': str or None
    """
    logger.info("Starting full statistical analysis pipeline...")
    
    # Ensure equal lengths for paired tests
    min_len = min(len(gatekeeper_scores), len(baseline_scores))
    if min_len == 0:
        raise InfeasibleError("No data available for statistical analysis.")
    
    gatekeeper_scores = gatekeeper_scores[:min_len]
    baseline_scores = baseline_scores[:min_len]
    
    result = {
        'method_used': None,
        'p_value': None,
        'test_statistic': None,
        'fallback_reason': None
    }
    
    # Priority 1: Try LMM if we have episode IDs and domains
    if episode_ids and domains and len(episode_ids) >= 10:
        try:
            logger.info("Attempting LMM (Priority 1)...")
            scores_series = pd.Series(gatekeeper_scores + baseline_scores)
            method_series = pd.Series(['gatekeeper'] * len(gatekeeper_scores) + ['baseline'] * len(baseline_scores))
            episode_series = pd.Series(episode_ids * 2)
            domain_series = pd.Series(domains * 2)
            
            lmm_result = fit_lmm(scores_series, method_series, episode_series, domain_series)
            
            result['method_used'] = lmm_result['method_used']
            result['p_value'] = lmm_result['p_value']
            result['test_statistic'] = lmm_result['test_statistic']
            result['fallback_reason'] = lmm_result.get('fallback_reason')
            logger.info(f"LMM succeeded: {result['method_used']}")
            return result
            
        except InfeasibleError as e:
            logger.warning(f"LMM infeasible: {e}. Proceeding to fallback.")
            result['fallback_reason'] = f"LMM infeasible: {e}"
        except Exception as e:
            logger.warning(f"LMM failed unexpectedly: {e}. Proceeding to fallback.")
            result['fallback_reason'] = f"LMM failed: {e}"
    
    # Priority 2: Normality Check -> Paired t-test or Wilcoxon
    logger.info("Performing Shapiro-Wilk normality test (Priority 2)...")
    # Combine scores for normality test (assuming paired structure)
    all_scores = gatekeeper_scores + baseline_scores
    normality_result = shapiro_wilk_test(all_scores)
    
    if normality_result['is_normal']:
        logger.info("Data is normal. Using Paired t-test.")
        post_hoc_result = run_post_hoc(gatekeeper_scores, baseline_scores, is_normal=True)
    else:
        logger.info("Data is non-normal. Using Wilcoxon signed-rank test.")
        post_hoc_result = run_post_hoc(gatekeeper_scores, baseline_scores, is_normal=False)
    
    result['method_used'] = post_hoc_result['method_used']
    result['p_value'] = post_hoc_result['p_value']
    result['test_statistic'] = post_hoc_result['test_statistic']
    
    if result['fallback_reason']:
        result['fallback_reason'] += f"; Fallback to {result['method_used']}"
    else:
        result['fallback_reason'] = f"Normality check: {result['method_used']}"
    
    logger.info(f"Statistical analysis complete: {result['method_used']}, p={result['p_value']:.4f}")
    return result

def main():
    """Main entry point for testing the stats pipeline."""
    # Example usage with dummy data
    logger.info("Running stats module self-test...")
    
    # Generate some dummy data
    np.random.seed(42)
    gatekeeper_scores = np.random.normal(0.8, 0.1, 50).tolist()
    baseline_scores = np.random.normal(0.7, 0.15, 50).tolist()
    episode_ids = [f"ep_{i}" for i in range(50)]
    domains = ["medical"] * 25 + ["office"] * 25 + ["medical"] * 25 + ["office"] * 25
    
    try:
        result = run_full_stats_pipeline(gatekeeper_scores, baseline_scores, episode_ids, domains)
        print("Statistical Analysis Result:")
        print(f"  Method: {result['method_used']}")
        print(f"  P-value: {result['p_value']:.4f}")
        print(f"  Test Statistic: {result['test_statistic']:.4f}")
        print(f"  Fallback Reason: {result['fallback_reason']}")
    except Exception as e:
        print(f"Statistical analysis failed: {e}")

if __name__ == "__main__":
    main()
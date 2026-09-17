import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.formula.api import glm as sm_glm
from statsmodels.genmod.families import Binomial

logger = logging.getLogger(__name__)

def shapiro_wilk_test(data: Union[List[float], np.ndarray]) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk normality test on a 1D array of data.
    
    Args:
        data: 1D array of numerical values (paired differences).
        
    Returns:
        Dict with keys: 'p_value', 'statistic', 'method' (Shapiro-Wilk).
    """
    if len(data) < 3:
        logger.warning("Sample size too small for Shapiro-Wilk test (< 3). Returning None.")
        return {
            'p_value': None,
            'test_statistic': None,
            'method': 'Shapiro-Wilk (skipped: N < 3)',
            'reason': 'Insufficient sample size'
        }
    
    try:
        stat, p_val = stats.shapiro(data)
        return {
            'p_value': float(p_val),
            'test_statistic': float(stat),
            'method': 'Shapiro-Wilk'
        }
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return {
            'p_value': None,
            'test_statistic': None,
            'method': 'Shapiro-Wilk (failed)',
            'reason': str(e)
        }

def fit_fixed_effects_glm(
    scores: np.ndarray,
    methods: np.ndarray,
    domains: np.ndarray
) -> Dict[str, Any]:
    """
    Fit a Fixed-Effects Logistic Regression (GLM) using statsmodels.
    Formula: score ~ method + C(Domain)
    
    Args:
        scores: Array of continuous/ordinal scores (e.g., Utility).
        methods: Array of method labels (e.g., 'gatekeeper', 'baseline').
        domains: Array of domain labels (e.g., 'medical', 'office').
        
    Returns:
        Dict with keys: 'p_value', 'test_statistic', 'method', 'coefficients'.
    """
    if len(scores) < 10:
        logger.warning("Sample size too small for GLM (< 10). Returning None.")
        return {
            'p_value': None,
            'test_statistic': None,
            'method': 'Fixed-Effects GLM (skipped: N < 10)',
            'reason': 'Insufficient sample size'
        }

    try:
        df = pd.DataFrame({
            'score': scores,
            'method': pd.Categorical(methods),
            'Domain': pd.Categorical(domains)
        })
        
        # Fit GLM with Binomial family if scores are binary (0/1), 
        # otherwise use Gaussian family for continuous scores.
        # Heuristic: if unique values <= 2, treat as binary.
        if len(np.unique(scores)) <= 2:
            family = Binomial()
            logger.info("Detected binary scores. Using Binomial family for GLM.")
        else:
            from statsmodels.genmod.families import Gaussian
            family = Gaussian()
            logger.info("Detected continuous scores. Using Gaussian family for GLM.")

        model = sm_glm('score ~ method + C(Domain)', data=df, family=family)
        result = model.fit()
        
        # Extract p-value for the 'method' coefficient
        # The result summary table has parameters as rows
        params_table = result.summary2().tables[1]
        p_values = params_table['P>|t|'] if 'P>|t|' in params_table.columns else params_table['P>|z|']
        
        # Find the p-value for the method coefficient (usually the second row if intercept is first)
        # We look for the row containing 'method[T.baseline]' or similar
        method_p_val = None
        method_stat = None
        
        for idx, row in params_table.iterrows():
            if 'method' in str(idx):
                method_p_val = float(row['P>|t|']) if 'P>|t|' in row else float(row['P>|z|'])
                method_stat = float(row['Coef.'])
                break
                
        if method_p_val is None:
            # Fallback: try to get the second coefficient (first non-intercept)
            # This assumes the model formula order: Intercept, method, Domain...
            # But this is fragile; better to rely on the loop above.
            logger.warning("Could not isolate method p-value from GLM results.")
            # Use the first non-intercept p-value as a proxy if we can't find 'method'
            # This is a fallback for edge cases in parsing
            for idx, row in params_table.iterrows():
                if 'method' in str(idx).lower() or (isinstance(idx, str) and not idx.startswith('Intercept')):
                     method_p_val = float(row['P>|t|']) if 'P>|t|' in row else float(row['P>|z|'])
                     method_stat = float(row['Coef.'])
                     break

        return {
            'p_value': method_p_val,
            'test_statistic': method_stat,
            'method': 'Fixed-Effects GLM',
            'coefficients': result.params.to_dict(),
            'aic': float(result.aic),
            'bic': float(result.bic)
        }
    except Exception as e:
        logger.error(f"Fixed-Effects GLM failed: {e}")
        return {
            'p_value': None,
            'test_statistic': None,
            'method': 'Fixed-Effects GLM (failed)',
            'reason': str(e)
        }

def run_mcnemar_test(
    gatekeeper_scores: np.ndarray,
    baseline_scores: np.ndarray
) -> Dict[str, Any]:
    """
    Run McNemar's Test for paired binary outcomes.
    
    Args:
        gatekeeper_scores: Binary array (0/1) of Gatekeeper outcomes.
        baseline_scores: Binary array (0/1) of Baseline outcomes.
        
    Returns:
        Dict with keys: 'p_value', 'test_statistic', 'method' (McNemar).
    """
    if len(gatekeeper_scores) != len(baseline_scores):
        raise ValueError("Input arrays must have the same length for paired test.")
    
    if len(gatekeeper_scores) == 0:
        return {
            'p_value': None,
            'test_statistic': None,
            'method': 'McNemar (skipped: empty)',
            'reason': 'No data'
        }

    try:
        # Construct contingency table
        # b: Gatekeeper=0, Baseline=1
        # c: Gatekeeper=1, Baseline=0
        b = np.sum((gatekeeper_scores == 0) & (baseline_scores == 1))
        c = np.sum((gatekeeper_scores == 1) & (baseline_scores == 0))
        
        # McNemar's test statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
        # If b+c is 0, the statistic is 0 and p-value is 1.0 (no difference possible)
        if (b + c) == 0:
            chi2 = 0.0
            p_val = 1.0
        else:
            chi2 = (abs(b - c) - 1)**2 / (b + c)
            p_val = 1 - stats.chi2.cdf(chi2, df=1)
        
        return {
            'p_value': float(p_val),
            'test_statistic': float(chi2),
            'method': 'McNemar\'s Test',
            'contingency': {'b': int(b), 'c': int(c)}
        }
    except Exception as e:
        logger.error(f"McNemar's Test failed: {e}")
        return {
            'p_value': None,
            'test_statistic': None,
            'method': 'McNemar\'s Test (failed)',
            'reason': str(e)
        }

def run_full_stats_pipeline(
    paired_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Orchestrates the full statistical analysis pipeline.
    
    Control Flow:
    1. Primary: Run McNemar's Test (for binary Access Control outcomes).
    2. Secondary: Run Fixed-Effects GLM (for continuous/ordinal Utility/Forgetting).
    3. Normality Check: If GLM used, perform Shapiro-Wilk on paired differences.
    4. Fallback: If GLM fails -> Domain-Stratified Analysis (average p-values).
    
    Args:
        paired_data: List of dicts with keys [episode_id, score, method, domain].
        
    Returns:
        Dict with keys: [method_used, p_value, test_statistic, fallback_reason].
    """
    if not paired_data:
        return {
            'method_used': 'None',
            'p_value': None,
            'test_statistic': None,
            'fallback_reason': 'Empty input data'
        }

    # Prepare data
    df = pd.DataFrame(paired_data)
    
    # Check if outcome is binary (0/1) -> McNemar
    unique_scores = df['score'].unique()
    is_binary = len(unique_scores) <= 2 and set(unique_scores).issubset({0, 1, 0.0, 1.0})
    
    result = {
        'method_used': None,
        'p_value': None,
        'test_statistic': None,
        'fallback_reason': None
    }

    if is_binary:
        # Primary: McNemar's Test
        logger.info("Detected binary outcome. Running McNemar's Test.")
        gatekeeper_scores = df[df['method'] == 'gatekeeper']['score'].values
        baseline_scores = df[df['method'] == 'baseline']['score'].values
        
        # Ensure alignment by episode_id if possible, but assuming input is already paired
        # If not aligned by index, we assume the list order is consistent for the two methods
        # For robustness, we pivot to wide format if episode_id is present
        if 'episode_id' in df.columns:
            wide = df.pivot(index='episode_id', columns='method', values='score')
            if 'gatekeeper' in wide.columns and 'baseline' in wide.columns:
                gatekeeper_scores = wide['gatekeeper'].values
                baseline_scores = wide['baseline'].values
            else:
                return {
                    'method_used': 'None',
                    'p_value': None,
                    'test_statistic': None,
                    'fallback_reason': 'Missing method columns in pivot'
                }
        
        mcnemar_res = run_mcnemar_test(gatekeeper_scores, baseline_scores)
        result['method_used'] = mcnemar_res['method']
        result['p_value'] = mcnemar_res['p_value']
        result['test_statistic'] = mcnemar_res['test_statistic']
        if mcnemar_res['p_value'] is None:
            result['fallback_reason'] = mcnemar_res.get('reason', 'McNemar failed')
        return result

    else:
        # Secondary: Fixed-Effects GLM
        logger.info("Detected continuous outcome. Running Fixed-Effects GLM.")
        scores = df['score'].values
        methods = df['method'].values
        domains = df['domain'].values if 'domain' in df.columns else np.array(['default'] * len(df))
        
        glm_res = fit_fixed_effects_glm(scores, methods, domains)
        
        if glm_res['p_value'] is not None:
            result['method_used'] = glm_res['method']
            result['p_value'] = glm_res['p_value']
            result['test_statistic'] = glm_res['test_statistic']
            
            # Normality Check (Shapiro-Wilk) on paired differences
            # We need to calculate differences for each episode
            if 'episode_id' in df.columns:
                wide = df.pivot(index='episode_id', columns='method', values='score')
                if 'gatekeeper' in wide.columns and 'baseline' in wide.columns:
                    diffs = wide['gatekeeper'] - wide['baseline']
                    shapiro_res = shapiro_wilk_test(diffs.values)
                    if shapiro_res['p_value'] is not None:
                        logger.info(f"Shapiro-Wilk p-value: {shapiro_res['p_value']}. Normality: {'Yes' if shapiro_res['p_value'] > 0.05 else 'No'}")
                        result['normality_check'] = shapiro_res
                    else:
                        result['normality_check'] = shapiro_res
            return result
        else:
            # Fallback: Domain-Stratified Analysis
            logger.warning("GLM failed. Attempting Domain-Stratified Analysis (fallback).")
            result['method_used'] = 'Domain-Stratified Fallback'
            result['fallback_reason'] = glm_res.get('reason', 'GLM failed')
            
            if 'domain' in df.columns:
                domains = df['domain'].unique()
                p_values = []
                for d in domains:
                    sub_df = df[df['domain'] == d]
                    if len(sub_df) >= 4: # Minimum for a small GLM
                        sub_res = fit_fixed_effects_glm(
                            sub_df['score'].values,
                            sub_df['method'].values,
                            np.array(['default'] * len(sub_df))
                        )
                        if sub_res['p_value'] is not None:
                            p_values.append(sub_res['p_value'])
                
                if p_values:
                    # Fisher's method or simple average? Task says "average p-values"
                    avg_p = np.mean(p_values)
                    result['p_value'] = float(avg_p)
                    result['test_statistic'] = None # No single test statistic for averaged p-values
                    result['fallback_details'] = {
                        'domains_analyzed': len(p_values),
                        'p_values': p_values
                    }
                else:
                    result['p_value'] = None
                    result['fallback_reason'] += "; No domains had sufficient data for stratified analysis."
            else:
                result['p_value'] = None
                result['fallback_reason'] += "; No domain column available for stratification."
            
            return result
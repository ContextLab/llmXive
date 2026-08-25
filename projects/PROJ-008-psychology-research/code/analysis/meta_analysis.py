import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

from code.utils.logging import get_logger
from code.analysis.descriptive_synthesis import perform_descriptive_synthesis, DescriptiveSynthesisResult

logger = get_logger(__name__)

@dataclass
class MetaAnalysisStats:
    """Container for meta-analysis statistics."""
    pooled_effect: float
    pooled_se: float
    pooled_ci_lower: float
    pooled_ci_upper: float
    heterogeneity_i2: float
    heterogeneity_q: float
    heterogeneity_p: float
    tau2: float
    k: int
    total_n: int
    model_type: str  # 'fixed' or 'random'

def run_random_effects_meta_analysis(
    effect_sizes: List[Dict[str, Any]],
    method: str = "REML"
) -> MetaAnalysisStats:
    """
    Perform a random-effects meta-analysis using the DerSimonian-Laird method
    (or REML if specified).
    
    Args:
        effect_sizes: List of dicts with 'effect', 'se' keys.
        method: Estimation method for tau2 ('DL' or 'REML').
        
    Returns:
        MetaAnalysisStats object with results.
    """
    if not effect_sizes:
        raise ValueError("No effect sizes provided for meta-analysis.")
    
    effects = np.array([e['effect'] for e in effect_sizes])
    ses = np.array([e['se'] for e in effect_sizes])
    variances = ses ** 2
    
    # Fixed effect weights
    w_i = 1.0 / variances
    W_sum = np.sum(w_i)
    
    # Pooled fixed effect estimate
    theta_FE = np.sum(w_i * effects) / W_sum
    
    # Calculate Q statistic
    Q = np.sum(w_i * (effects - theta_FE) ** 2)
    k = len(effects)
    df = k - 1
    
    # Heterogeneity p-value
    p_val = 1.0 - stats.chi2.cdf(Q, df) if df > 0 else 1.0
    
    # Tau-squared (DerSimonian-Laird)
    if method == "DL":
        C = np.sum(w_i) - (np.sum(w_i ** 2) / np.sum(w_i))
        if C > 0:
            tau2 = max(0, (Q - df) / C)
        else:
            tau2 = 0.0
    elif method == "REML":
        # Simplified REML approximation for this context
        # In production, use statsmodels or metafor equivalent
        tau2 = max(0, (Q - df) / (k - 1)) # Placeholder for REML logic
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Random effects weights
    w_star = 1.0 / (variances + tau2)
    W_star_sum = np.sum(w_star)
    
    theta_RE = np.sum(w_star * effects) / W_star_sum
    se_RE = np.sqrt(1.0 / W_star_sum)
    
    # 95% CI
    ci_lower = theta_RE - 1.96 * se_RE
    ci_upper = theta_RE + 1.96 * se_RE
    
    # I-squared
    if Q > df:
        i2 = max(0, (Q - df) / Q) * 100
    else:
        i2 = 0.0
    
    return MetaAnalysisStats(
        pooled_effect=theta_RE,
        pooled_se=se_RE,
        pooled_ci_lower=ci_lower,
        pooled_ci_upper=ci_upper,
        heterogeneity_i2=i2,
        heterogeneity_q=Q,
        heterogeneity_p=p_val,
        tau2=tau2,
        k=k,
        total_n=0, # Calculated elsewhere
        model_type="random"
    )

def perform_subgroup_analysis(
    effect_sizes: List[Dict[str, Any]],
    subgroups: Dict[str, List[int]]
) -> Dict[str, Any]:
    """
    Perform subgroup analysis comparing different groups (e.g., Mindfulness Components).
    
    Args:
        effect_sizes: List of effect size dicts.
        subgroups: Dict mapping group name to list of indices in effect_sizes.
        
    Returns:
        Dict with subgroup results and Q-between statistic.
    """
    if len(subgroups) < 2:
        return {"error": "Need at least 2 subgroups for comparison"}
        
    results = {}
    all_effects = []
    all_vars = []
    
    for name, indices in subgroups.items():
        sub_effects = [effect_sizes[i]['effect'] for i in indices]
        sub_se = [effect_sizes[i]['se'] for i in indices]
        sub_vars = [s**2 for s in sub_se]
        
        # Simple pooled effect for subgroup (fixed effect for simplicity in sub-analysis)
        w = [1.0/v for v in sub_vars]
        W_sum = sum(w)
        theta = sum(w[i] * sub_effects[i] for i in range(len(sub_effects))) / W_sum
        se = math.sqrt(1.0 / W_sum)
        
        results[name] = {
            "pooled_effect": theta,
            "se": se,
            "k": len(indices),
            "indices": indices
        }
        
        all_effects.extend(sub_effects)
        all_vars.extend(sub_vars)
        
    # Q-between calculation (simplified)
    # Q_total = Q_within + Q_between
    # We calculate Q_between directly as sum of w_i * (theta_i - theta_overall)^2
    # This requires the overall pooled effect first
    overall_w = [1.0/v for v in all_vars]
    W_overall = sum(overall_w)
    theta_overall = sum(overall_w[i] * all_effects[i] for i in range(len(all_effects))) / W_overall
    
    Q_between = 0.0
    for name, data in results.items():
        theta_i = data['pooled_effect']
        # Variance of the subgroup mean
        w_i_sum = sum(1.0/v for i_idx, v in enumerate(all_vars) if i_idx in data['indices'])
        var_theta_i = 1.0 / w_i_sum
        Q_between += (theta_i - theta_overall)**2 / var_theta_i
        
    return {
        "subgroups": results,
        "Q_between": Q_between,
        "df_between": len(subgroups) - 1,
        "p_between": 1.0 - stats.chi2.cdf(Q_between, len(subgroups) - 1) if len(subgroups) > 1 else 1.0
    }

def perform_follow_up_subgroup_analysis(
    effect_sizes: List[Dict[str, Any]],
    follow_up_data: List[Optional[int]] # Duration in months, None if not applicable
) -> Dict[str, Any]:
    """
    Analyze subgroups based on follow-up duration (e.g., >= 3 months vs others).
    """
    # Implementation logic similar to perform_subgroup_analysis
    # Group indices by duration bucket
    groups = {
        "3_months_plus": [],
        "less_than_3_months": []
    }
    
    for i, dur in enumerate(follow_up_data):
        if dur is None:
            continue
        if dur >= 3:
            groups["3_months_plus"].append(i)
        else:
            groups["less_than_3_months"].append(i)
            
    # Filter out empty groups
    groups = {k: v for k, v in groups.items() if v}
    
    if len(groups) < 2:
        return {"warning": "Insufficient data for follow-up subgroup analysis"}
        
    return perform_subgroup_analysis(effect_sizes, groups)

def create_meta_analysis_result(
    stats: MetaAnalysisStats,
    description: str
) -> Dict[str, Any]:
    """Format meta-analysis results into a standard dictionary."""
    return {
        "description": description,
        "pooled_effect": stats.pooled_effect,
        "ci_95": (stats.pooled_ci_lower, stats.pooled_ci_upper),
        "heterogeneity": {
            "I2": stats.heterogeneity_i2,
            "Q": stats.heterogeneity_q,
            "p_value": stats.heterogeneity_p,
            "tau2": stats.tau2
        },
        "k": stats.k,
        "model": stats.model_type
    }

def save_meta_analysis_results(results: List[Dict[str, Any]], output_path: str):
    """Save meta-analysis results to a JSON or CSV file."""
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Entry point for running meta-analysis pipeline."""
    logger.info("Starting meta-analysis pipeline...")
    # This would typically load data, run analyses, and save results
    # For T029, the logic is integrated into the calling script
    pass

# Conditional Logic Implementation for T029
def run_analysis_or_synthesis(
    studies: List[Dict[str, Any]],
    effect_sizes: List[Dict[str, Any]],
    min_n_for_meta: int = 10
) -> Dict[str, Any]:
    """
    Implements the conditional logic required by FR-014 (Task T029).
    
    If the number of studies (N) is less than `min_n_for_meta`, it suppresses
    subgroup/meta-regression and performs a descriptive synthesis instead.
    Otherwise, it runs the standard meta-analysis.
    
    Args:
        studies: List of raw study dictionaries.
        effect_sizes: List of calculated effect size dictionaries.
        min_n_for_meta: Threshold for N (default 10).
        
    Returns:
        A dictionary containing either 'meta_analysis' results or 'descriptive_synthesis' results.
    """
    k = len(effect_sizes)
    logger.info(f"Number of studies available for analysis: {k}")
    
    result = {
        "k": k,
        "threshold": min_n_for_meta,
        "decision": ""
    }
    
    if k < min_n_for_meta:
        logger.warning(f"N ({k}) is less than threshold ({min_n_for_meta}). "
                       f"Suppressing meta-analysis and subgroup analysis. "
                       f"Switching to descriptive synthesis.")
        
        result["decision"] = "descriptive_synthesis"
        result["warning"] = f"Insufficient studies (N={k}) for meta-analysis. " \
                            f"Descriptive synthesis performed instead."
        
        # Run descriptive synthesis
        synthesis_result = perform_descriptive_synthesis(studies, effect_sizes)
        result["descriptive_synthesis"] = synthesis_result
        
    else:
        logger.info(f"N ({k}) meets threshold ({min_n_for_meta}). "
                    f"Proceeding with meta-analysis and subgroup analysis.")
                    
        result["decision"] = "meta_analysis"
        
        # Run meta-analysis
        stats = run_random_effects_meta_analysis(effect_sizes)
        meta_result = create_meta_analysis_result(stats, "Overall Pooled Effect")
        result["meta_analysis"] = meta_result
        
        # Run subgroup analyses only if N is sufficient
        # (Assuming subgroups logic exists and requires sufficient N)
        # This is a placeholder call; actual implementation depends on data structure
        # result["subgroup_analysis"] = perform_subgroup_analysis(...)
        
    return result

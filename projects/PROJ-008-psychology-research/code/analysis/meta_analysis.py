import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

from code.data.models import MetaAnalysisResult
from code.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class MetaAnalysisStats:
    pooled_effect: float
    pooled_se: float
    pooled_ci_low: float
    pooled_ci_high: float
    i_squared: float
    q_statistic: float
    q_p_value: float
    tau_squared: float
    heterogeneity: str

def run_random_effects_meta_analysis(
    effect_sizes: List[float],
    ses: List[float],
    study_ids: List[str]
) -> MetaAnalysisStats:
    """
    Perform a random-effects meta-analysis using the DerSimonian-Laird method.
    
    Args:
        effect_sizes: List of effect sizes (Hedges' g)
        ses: List of standard errors for each effect size
        study_ids: List of study identifiers
        
    Returns:
        MetaAnalysisStats object with pooled estimates and heterogeneity metrics
    """
    if len(effect_sizes) != len(ses):
        raise ValueError("effect_sizes and ses must have the same length")
    
    if len(effect_sizes) == 0:
        raise ValueError("At least one effect size is required")
        
    k = len(effect_sizes)
    yi = np.array(effect_sizes)
    vi = np.array([se ** 2 for se in ses])  # Variance = SE^2
    
    # Fixed-effect weights
    wi = 1.0 / vi
    
    # Fixed-effect pooled estimate
    y_bar = np.sum(wi * yi) / np.sum(wi)
    
    # Q statistic (heterogeneity)
    q = np.sum(wi * (yi - y_bar) ** 2)
    
    # Degrees of freedom
    df = k - 1
    
    # P-value for Q statistic
    q_p_value = 1.0 - _chi2_cdf(q, df) if df > 0 else 1.0
    
    # DerSimonian-Laird tau^2 calculation
    c = np.sum(wi) - (np.sum(wi ** 2) / np.sum(wi))
    tau_squared = max(0, (q - df) / c) if c > 0 else 0
    
    # Random-effects weights
    vi_re = vi + tau_squared
    wi_re = 1.0 / vi_re
    
    # Random-effects pooled estimate
    y_bar_re = np.sum(wi_re * yi) / np.sum(wi_re)
    se_re = math.sqrt(1.0 / np.sum(wi_re))
    
    # 95% CI
    ci_low = y_bar_re - 1.96 * se_re
    ci_high = y_bar_re + 1.96 * se_re
    
    # I^2 statistic
    i_squared = max(0, (q - df) / q * 100) if q > 0 else 0
    
    # Heterogeneity classification
    if i_squared < 25:
        heterogeneity = "low"
    elif i_squared < 50:
        heterogeneity = "moderate"
    else:
        heterogeneity = "high"
        
    return MetaAnalysisStats(
        pooled_effect=y_bar_re,
        pooled_se=se_re,
        pooled_ci_low=ci_low,
        pooled_ci_high=ci_high,
        i_squared=i_squared,
        q_statistic=q,
        q_p_value=q_p_value,
        tau_squared=tau_squared,
        heterogeneity=heterogeneity
    )

def _chi2_cdf(x: float, df: int) -> float:
    """
    Approximate chi-squared CDF using the incomplete gamma function.
    This is a simplified implementation for common cases.
    """
    if df <= 0:
        return 0.0
    if x <= 0:
        return 0.0
        
    # Use scipy if available, otherwise a simple approximation
    try:
        from scipy.stats import chi2
        return chi2.cdf(x, df)
    except ImportError:
        # Fallback approximation for small df
        # This is a simplified version; for production, use scipy
        if df == 1:
            from math import sqrt, exp
            # Chi2(1) is the square of a standard normal
            # CDF(x) = 2 * Phi(sqrt(x)) - 1
            z = math.sqrt(x)
            phi = 0.5 * (1 + math.erf(z / math.sqrt(2)))
            return 2 * phi - 1
        else:
            # Simple numerical integration approximation
            # This is not highly accurate but provides a fallback
            n_points = 1000
            dx = x / n_points
            total = 0.0
            for i in range(n_points):
                xi = (i + 0.5) * dx
                if xi > 0:
                    log_pdf = ((df / 2) - 1) * math.log(xi) - (xi / 2) - (df / 2) * math.log(2) - math.lgamma(df / 2)
                    pdf = math.exp(log_pdf)
                    total += pdf * dx
            return min(1.0, max(0.0, total))

def perform_subgroup_analysis(
    effect_sizes: List[float],
    ses: List[float],
    study_ids: List[str],
    subgroup_labels: List[str],
    min_studies_per_subgroup: int = 10
) -> Dict[str, Any]:
    """
    Perform subgroup analysis with Cochran's Q test for between-group differences.
    
    Implements FR-014: If N < 10 in any subgroup, suppress statistical testing
    and return descriptive synthesis instead.
    
    Args:
        effect_sizes: List of effect sizes
        ses: List of standard errors
        study_ids: List of study identifiers
        subgroup_labels: List of subgroup labels for each study
        min_studies_per_subgroup: Minimum studies required for statistical testing (default 10)
        
    Returns:
        Dictionary with subgroup results and testing status
    """
    unique_groups = list(set(subgroup_labels))
    results = {}
    testing_allowed = True
    warnings = []
    
    # Check if statistical testing is allowed
    for group in unique_groups:
        group_count = sum(1 for label in subgroup_labels if label == group)
        if group_count < min_studies_per_subgroup:
            testing_allowed = False
            warnings.append(f"Subgroup '{group}' has only {group_count} studies (minimum {min_studies_per_subgroup} required for statistical testing)")
    
    if not testing_allowed:
        logger.warning("Subgroup analysis suppressed due to insufficient studies. Returning descriptive synthesis.")
        for group in unique_groups:
            group_indices = [i for i, label in enumerate(subgroup_labels) if label == group]
            group_effects = [effect_sizes[i] for i in group_indices]
            group_ses = [ses[i] for i in group_indices]
            
            results[group] = {
                "n_studies": len(group_indices),
                "mean_effect": np.mean(group_effects) if group_effects else None,
                "std_effect": np.std(group_effects) if len(group_effects) > 1 else None,
                "min_effect": min(group_effects) if group_effects else None,
                "max_effect": max(group_effects) if group_effects else None,
                "statistical_test": None,
                "descriptive_synthesis": True
            }
        
        results["warnings"] = warnings
        results["testing_suppressed"] = True
        return results
    
    # Perform statistical subgroup analysis
    group_stats = {}
    all_q_between = 0.0
    
    for group in unique_groups:
        group_indices = [i for i, label in enumerate(subgroup_labels) if label == group]
        group_effects = [effect_sizes[i] for i in group_indices]
        group_ses = [ses[i] for i in group_indices]
        
        if len(group_effects) == 0:
            continue
            
        # Calculate within-group heterogeneity
        stats = run_random_effects_meta_analysis(group_effects, group_ses, 
                                                [study_ids[i] for i in group_indices])
        
        group_stats[group] = {
            "n_studies": len(group_indices),
            "pooled_effect": stats.pooled_effect,
            "pooled_se": stats.pooled_se,
            "ci_low": stats.pooled_ci_low,
            "ci_high": stats.pooled_ci_high,
            "i_squared": stats.i_squared,
            "q_within": stats.q_statistic,
            "df_within": len(group_effects) - 1
        }
        
        # Contribution to Q_between
        # Q_between = sum(w_g * (theta_g - theta_overall)^2)
        # We'll calculate this after getting overall estimate
    
    # Calculate overall pooled effect for Q_between
    overall_stats = run_random_effects_meta_analysis(effect_sizes, ses, study_ids)
    theta_overall = overall_stats.pooled_effect
    
    # Q_between calculation
    q_between = 0.0
    for group, stats in group_stats.items():
        w_g = 1.0 / (stats["pooled_se"] ** 2)  # Weight for subgroup
        q_between += w_g * (stats["pooled_effect"] - theta_overall) ** 2
    
    # Degrees of freedom for Q_between
    df_between = len(unique_groups) - 1
    
    # P-value for Q_between
    q_between_p = 1.0 - _chi2_cdf(q_between, df_between) if df_between > 0 else 1.0
    
    results = {
        "subgroups": group_stats,
        "q_between": q_between,
        "df_between": df_between,
        "q_between_p_value": q_between_p,
        "testing_suppressed": False,
        "warnings": []
    }
    
    return results

def create_meta_analysis_result(
    stats: MetaAnalysisStats,
    description: str = "Meta-analysis result"
) -> MetaAnalysisResult:
    """Create a MetaAnalysisResult dataclass instance from stats."""
    return MetaAnalysisResult(
        pooled_effect=stats.pooled_effect,
        pooled_se=stats.pooled_se,
        ci_low=stats.pooled_ci_low,
        ci_high=stats.pooled_ci_high,
        i_squared=stats.i_squared,
        tau_squared=stats.tau_squared,
        q_statistic=stats.q_statistic,
        q_p_value=stats.q_p_value,
        heterogeneity=stats.heterogeneity,
        description=description,
        n_studies=len(stats.q_statistic) if hasattr(stats.q_statistic, '__len__') else 1
    )

def save_meta_analysis_results(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """Save meta-analysis results to a JSON file."""
    import json
    from pathlib import Path
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Meta-analysis results saved to {output_path}")

def perform_follow_up_subgroup_analysis(
    effect_sizes: List[float],
    ses: List[float],
    study_ids: List[str],
    follow_up_durations: List[Optional[float]],  # in months
    follow_up_threshold: float = 3.0  # 3 months
) -> Dict[str, Any]:
    """
    Perform subgroup analysis based on follow-up duration (3-month vs others).
    
    Implements FR-014: Suppress analysis if N < 10 in either subgroup.
    
    Args:
        effect_sizes: List of effect sizes
        ses: List of standard errors
        study_ids: List of study identifiers
        follow_up_durations: List of follow-up durations in months (None for no follow-up)
        follow_up_threshold: Threshold for categorization (default 3 months)
        
    Returns:
        Dictionary with subgroup analysis results
    """
    # Categorize studies
    short_followup = []
    long_followup = []
    short_indices = []
    long_indices = []
    
    for i, duration in enumerate(follow_up_durations):
        if duration is None:
            continue  # Skip studies without follow-up
        elif duration < follow_up_threshold:
            short_followup.append(effect_sizes[i])
            short_indices.append(i)
        else:
            long_followup.append(effect_sizes[i])
            long_indices.append(i)
    
    results = {}
    testing_allowed = True
    warnings = []
    
    # Check minimum sample size
    if len(short_followup) < 10:
        testing_allowed = False
        warnings.append(f"Short follow-up subgroup has only {len(short_followup)} studies (minimum 10 required)")
    
    if len(long_followup) < 10:
        testing_allowed = False
        warnings.append(f"Long follow-up subgroup has only {len(long_followup)} studies (minimum 10 required)")
    
    if not testing_allowed:
        logger.warning("Follow-up subgroup analysis suppressed due to insufficient studies.")
        results["short_followup"] = {
            "n_studies": len(short_followup),
            "mean_effect": np.mean(short_followup) if short_followup else None,
            "descriptive_synthesis": True
        }
        results["long_followup"] = {
            "n_studies": len(long_followup),
            "mean_effect": np.mean(long_followup) if long_followup else None,
            "descriptive_synthesis": True
        }
        results["warnings"] = warnings
        results["testing_suppressed"] = True
        return results
    
    # Perform statistical analysis
    short_ses = [ses[i] for i in short_indices]
    long_ses = [ses[i] for i in long_indices]
    
    short_stats = run_random_effects_meta_analysis(
        short_followup, short_ses,
        [study_ids[i] for i in short_indices]
    )
    
    long_stats = run_random_effects_meta_analysis(
        long_followup, long_ses,
        [study_ids[i] for i in long_indices]
    )
    
    results = {
        "short_followup": {
            "n_studies": len(short_followup),
            "pooled_effect": short_stats.pooled_effect,
            "ci_low": short_stats.pooled_ci_low,
            "ci_high": short_stats.pooled_ci_high,
            "i_squared": short_stats.i_squared
        },
        "long_followup": {
            "n_studies": len(long_followup),
            "pooled_effect": long_stats.pooled_effect,
            "ci_low": long_stats.pooled_ci_low,
            "ci_high": long_stats.pooled_ci_high,
            "i_squared": long_stats.i_squared
        },
        "testing_suppressed": False,
        "warnings": []
    }
    
    return results

def main():
    """Main entry point for meta-analysis module."""
    logger.info("Meta-analysis module loaded successfully")
    logger.info("Functions available:")
    logger.info("  - run_random_effects_meta_analysis")
    logger.info("  - perform_subgroup_analysis")
    logger.info("  - perform_follow_up_subgroup_analysis")
    logger.info("  - create_meta_analysis_result")
    logger.info("  - save_meta_analysis_results")

if __name__ == "__main__":
    main()

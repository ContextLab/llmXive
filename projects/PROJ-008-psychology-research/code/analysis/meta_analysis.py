import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import math
import numpy as np
import pandas as pd
from code.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class MetaAnalysisStats:
    """Statistics for the overall meta-analysis."""
    pooled_effect: float
    pooled_se: float
    z_score: float
    p_value: float
    ci_lower: float
    ci_upper: float
    i_squared: float
    q_statistic: float
    df: int
    tau_squared: float

@dataclass
class SubgroupResult:
    """Results for a single subgroup."""
    domain: str
    n_studies: int
    pooled_effect: float
    pooled_se: float
    ci_lower: float
    ci_upper: float
    z_score: float
    p_value: float
    i_squared: float
    q_statistic: float
    df: int

@dataclass
class SubgroupAnalysisResult:
    """Container for subgroup analysis results."""
    overall_stats: Optional[MetaAnalysisStats]
    subgroup_stats: List[SubgroupResult]
    between_q: float
    between_df: int
    between_p_value: float

def calculate_hedges_g_correction(j: float) -> float:
    """Calculate the correction factor for small sample bias."""
    # J approximation: 1 - (3 / (4 * df - 1))
    return j

def run_random_effects_meta_analysis(effect_sizes: List[float], ses: List[float]) -> MetaAnalysisStats:
    """
    Perform a random-effects meta-analysis.
    
    Args:
        effect_sizes: List of Hedges' g values.
        ses: List of standard errors.
        
    Returns:
        MetaAnalysisStats object with pooled results and heterogeneity.
    """
    if not effect_sizes or len(effect_sizes) == 0:
        raise ValueError("Effect size list cannot be empty.")
        
    n = len(effect_sizes)
    if n == 1:
        # If only one study, return its stats but heterogeneity is undefined
        g = effect_sizes[0]
        se = ses[0]
        return MetaAnalysisStats(
            pooled_effect=g,
            pooled_se=se,
            z_score=g / se if se != 0 else 0.0,
            p_value=1.0, # Undefined for n=1, defaulting
            ci_lower=g - 1.96 * se,
            ci_upper=g + 1.96 * se,
            i_squared=0.0,
            q_statistic=0.0,
            df=0,
            tau_squared=0.0
        )

    # Weights for fixed effect (1/se^2)
    w_fixed = [1.0 / (se ** 2) if se > 0 else 0.0 for se in ses]
    sum_w = sum(w_fixed)
    
    if sum_w == 0:
        raise ValueError("Sum of weights is zero. Check standard errors.")

    # Pooled effect (fixed effect estimate)
    g_pool = sum(w * g for w, g in zip(w_fixed, effect_sizes)) / sum_w
    
    # Q statistic (Cochran's Q)
    q_stat = sum(w * (g - g_pool) ** 2 for w, g in zip(w_fixed, effect_sizes))
    df = n - 1
    
    # Tau^2 (DerSimonian-Laird estimator)
    c = sum(w_fixed) - (sum(w ** 2 for w in w_fixed) / sum_w)
    if c <= 0:
        tau_sq = 0.0
    else:
        tau_sq = max(0.0, (q_stat - df) / c)
        
    # Random effects weights
    w_random = [1.0 / ((se ** 2) + tau_sq) if ((se ** 2) + tau_sq) > 0 else 0.0 for se in ses]
    sum_w_rand = sum(w_random)
    
    if sum_w_rand == 0:
        # Fallback to fixed if random weights fail (rare edge case)
        w_random = w_fixed
        sum_w_rand = sum_w

    # Pooled effect (random effects)
    g_pool_re = sum(w * g for w, g in zip(w_random, effect_sizes)) / sum_w_rand
    se_pool_re = math.sqrt(1.0 / sum_w_rand) if sum_w_rand > 0 else 0.0
    
    z_score = g_pool_re / se_pool_re if se_pool_re > 0 else 0.0
    
    # P-value (two-tailed) using normal approximation
    # Using scipy if available, otherwise manual approximation
    try:
        from scipy.stats import norm
        p_val = 2 * (1 - norm.cdf(abs(z_score)))
    except ImportError:
        # Manual approximation
        p_val = 2 * (1 - (1 / (1 + math.exp(-0.07056 * z_score**3 - 1.5976 * z_score))))

    # I^2 (Higgins & Thompson)
    # I^2 = max(0, (Q - df) / Q)
    i_sq = max(0.0, (q_stat - df) / q_stat * 100) if q_stat > 0 else 0.0

    ci_lower = g_pool_re - 1.96 * se_pool_re
    ci_upper = g_pool_re + 1.96 * se_pool_re

    return MetaAnalysisStats(
        pooled_effect=g_pool_re,
        pooled_se=se_pool_re,
        z_score=z_score,
        p_value=p_val,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        i_squared=i_sq,
        q_statistic=q_stat,
        df=df,
        tau_squared=tau_sq
    )

def perform_subgroup_analysis(df: pd.DataFrame, subgroup_col: str) -> SubgroupAnalysisResult:
    """
    Perform subgroup analysis on the dataframe grouped by a specific column.
    
    Args:
        df: DataFrame containing 'hedges_g' and 'se' columns.
        subgroup_col: The column name to group by (e.g., 'social_skill_domain').
        
    Returns:
        SubgroupAnalysisResult with stats for each subgroup and between-group heterogeneity.
    """
    if subgroup_col not in df.columns:
        raise ValueError(f"Column '{subgroup_col}' not found in dataframe.")
        
    if 'hedges_g' not in df.columns or 'se' not in df.columns:
        raise ValueError("DataFrame must contain 'hedges_g' and 'se' columns.")

    groups = df.groupby(subgroup_col)
    subgroup_results = []
    all_effects = []
    all_ses = []
    group_effects = []
    group_ses = []
    group_ns = []

    logger.info(f"Performing subgroup analysis on column: {subgroup_col}")

    for name, group in groups:
        g_list = group['hedges_g'].tolist()
        se_list = group['se'].tolist()
        
        all_effects.extend(g_list)
        all_ses.extend(se_list)
        
        group_ns.append(len(g_list))
        
        if len(g_list) == 0:
            continue
            
        stats = run_random_effects_meta_analysis(g_list, se_list)
        
        subgroup_results.append(SubgroupResult(
            domain=str(name),
            n_studies=len(g_list),
            pooled_effect=stats.pooled_effect,
            pooled_se=stats.pooled_se,
            ci_lower=stats.ci_lower,
            ci_upper=stats.ci_upper,
            z_score=stats.z_score,
            p_value=stats.p_value,
            i_squared=stats.i_squared,
            q_statistic=stats.q_statistic,
            df=stats.df
        ))
        
        # For between-group Q calculation, we need the pooled effect of each group
        # and the variance of that pooled effect
        group_effects.append(stats.pooled_effect)
        group_ses.append(stats.pooled_se)

    if not subgroup_results:
        return SubgroupAnalysisResult(
            overall_stats=None,
            subgroup_stats=[],
            between_q=0.0,
            between_df=0,
            between_p_value=1.0
        )

    # Calculate overall stats
    overall_stats = run_random_effects_meta_analysis(all_effects, all_ses)

    # Calculate Between-Group Heterogeneity (Q_between)
    # Q_between = Sum(W_i * (G_i - G_overall)^2)
    # Where W_i is 1 / SE_i^2 for the subgroup pooled effect
    # G_overall is the overall pooled effect
    
    w_between = []
    for se in group_ses:
        if se > 0:
            w_between.append(1.0 / (se ** 2))
        else:
            w_between.append(0.0)
            
    sum_w_between = sum(w_between)
    
    if sum_w_between == 0:
        q_between = 0.0
    else:
        # Weighted average of subgroup effects
        g_overall_weighted = sum(w * g for w, g in zip(w_between, group_effects)) / sum_w_between
        q_between = sum(w * (g - g_overall_weighted) ** 2 for w, g in zip(w_between, group_effects))
        
    # Degrees of freedom for between = k - 1 (k = number of subgroups)
    k = len(subgroup_results)
    df_between = k - 1 if k > 1 else 0
    
    # P-value for Q_between
    if df_between <= 0:
        p_between = 1.0
    else:
        try:
            from scipy.stats import chi2
            p_between = 1 - chi2.cdf(q_between, df_between)
        except ImportError:
            # Fallback: if Q is large, p is small, otherwise 1.0
            p_between = 0.01 if q_between > df_between + 2 * math.sqrt(2 * df_between) else 1.0

    return SubgroupAnalysisResult(
        overall_stats=overall_stats,
        subgroup_stats=subgroup_results,
        between_q=q_between,
        between_df=df_between,
        between_p_value=p_between
    )

def perform_follow_up_subgroup_analysis(df: pd.DataFrame, follow_up_col: str = 'follow_up') -> SubgroupAnalysisResult:
    """
    Specific implementation for follow-up duration analysis.
    Groups by '3-month' vs 'others' based on the follow_up string.
    
    Args:
        df: DataFrame.
        follow_up_col: Column name.
        
    Returns:
        SubgroupAnalysisResult.
    """
    # Create a temporary categorical column
    def categorize_followup(val):
        if pd.isna(val) or not val:
            return 'not-reported'
        val_str = str(val).lower()
        if '3-month' in val_str or '3 month' in val_str:
            return '3-month'
        return 'other'
        
    df_temp = df.copy()
    df_temp['temp_category'] = df_temp[follow_up_col].apply(categorize_followup)
    
    return perform_subgroup_analysis(df_temp, 'temp_category')

def create_meta_analysis_result(df: pd.DataFrame, subgroup_col: str) -> Dict[str, Any]:
    """
    Orchestrates the analysis and returns a dictionary suitable for JSON serialization.
    
    Args:
        df: Cleaned study dataframe with effect sizes.
        subgroup_col: Column to subgroup by.
        
    Returns:
        Dictionary with analysis results.
    """
    result = perform_subgroup_analysis(df, subgroup_col)
    
    output = {
        "overall": {
            "pooled_effect": result.overall_stats.pooled_effect,
            "ci_lower": result.overall_stats.ci_lower,
            "ci_upper": result.overall_stats.ci_upper,
            "i_squared": result.overall_stats.i_squared,
            "p_value": result.overall_stats.p_value
        },
        "subgroups": [
            {
                "name": sub.domain,
                "n_studies": sub.n_studies,
                "pooled_effect": sub.pooled_effect,
                "ci_lower": sub.ci_lower,
                "ci_upper": sub.ci_upper,
                "i_squared": sub.i_squared
            }
            for sub in result.subgroup_stats
        ],
        "between_group_test": {
            "q_statistic": result.between_q,
            "df": result.between_df,
            "p_value": result.between_p_value
        }
    }
    return output

def save_meta_analysis_results(result: Dict[str, Any], output_path: str):
    """Saves the analysis result to a JSON file."""
    import json
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved meta-analysis results to {output_path}")

def main():
    """
    Main entry point for the meta-analysis script.
    Expects:
      --input: Path to CSV with cleaned studies and calculated effect sizes.
      --output: Path to JSON output.
      --subgroup: Column name for subgroup analysis (default: 'social_skill_domain').
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run meta-analysis with subgroup analysis.")
    parser.add_argument('--input', required=True, help='Input CSV file path.')
    parser.add_argument('--output', required=True, help='Output JSON file path.')
    parser.add_argument('--subgroup', default='social_skill_domain', help='Column to subgroup by.')
    parser.add_argument('--plots-dir', default='viz', help='Directory for plots (if needed).')
    
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.input}")
    try:
        df = pd.read_csv(args.input)
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        return 1
        
    required_cols = ['hedges_g', 'se', args.subgroup]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns in input CSV: {missing}")
        return 1
        
    # Filter out rows with NaN effect sizes or SEs
    df_clean = df.dropna(subset=['hedges_g', 'se'])
    
    if len(df_clean) == 0:
        logger.warning("No valid studies found after cleaning. Outputting empty result.")
        save_meta_analysis_results({"subgroups": [], "overall": None}, args.output)
        return 0
        
    logger.info(f"Running subgroup analysis on '{args.subgroup}' with {len(df_clean)} studies.")
    analysis_result = create_meta_analysis_result(df_clean, args.subgroup)
    
    save_meta_analysis_results(analysis_result, args.output)
    logger.info("Meta-analysis completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())

import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import math
import numpy as np
import pandas as pd
from scipy import stats

from code.utils.logging import get_logger
from code.utils.config import get_data_path, get_output_path

logger = get_logger(__name__)

@dataclass
class MetaAnalysisStats:
    """Container for meta-analysis statistics."""
    pooled_effect: float
    se: float
    ci_lower: float
    ci_upper: float
    k: int
    i_squared: float
    q_stat: float
    q_pval: float
    tau_squared: float

@dataclass
class SubgroupResult:
    """Result for a single subgroup analysis."""
    subgroup_name: str
    pooled_effect: float
    se: float
    ci_lower: float
    ci_upper: float
    k: int
    i_squared: float
    q_stat: float
    q_pval: float
    tau_squared: float

@dataclass
class SubgroupAnalysisResult:
    """Result for a full subgroup analysis across multiple groups."""
    analysis_name: str
    between_q_stat: float
    between_q_pval: float
    subgroup_results: List[SubgroupResult] = field(default_factory=list)

def calculate_hedges_g_correction(n_treatment: int, n_control: int) -> float:
    """Calculate the small-sample correction factor J."""
    df = n_treatment + n_control - 2
    if df <= 0:
        return 1.0
    # Approximation of J = 1 - 3/(4*df - 1)
    return 1.0 - (3.0 / (4.0 * df - 1.0))

def run_random_effects_meta_analysis(
    effects: List[float],
    ses: List[float]
) -> MetaAnalysisStats:
    """
    Perform a random-effects meta-analysis using the DerSimonian-Laird method.
    
    Args:
        effects: List of effect sizes (Hedges' g).
        ses: List of standard errors for each effect size.
        
    Returns:
        MetaAnalysisStats object with pooled results and heterogeneity metrics.
    """
    if len(effects) != len(ses) or len(effects) == 0:
        raise ValueError("Effects and SEs lists must be non-empty and of equal length.")
    
    k = len(effects)
    effects_arr = np.array(effects)
    ses_arr = np.array(ses)
    variances = ses_arr ** 2
    
    # Fixed effect weights (inverse variance)
    w_i = 1.0 / variances
    
    # Pooled effect (fixed)
    mu_FE = np.sum(w_i * effects_arr) / np.sum(w_i)
    
    # Q statistic for heterogeneity
    Q = np.sum(w_i * (effects_arr - mu_FE) ** 2)
    
    # Degrees of freedom for Q
    df_q = k - 1
    
    # P-value for Q
    q_pval = 1.0 - stats.chi2.cdf(Q, df_q) if df_q > 0 else 1.0
    
    # DerSimonian-Laird estimator for tau^2
    C = np.sum(w_i) - (np.sum(w_i ** 2) / np.sum(w_i))
    if C > 0:
        tau_sq = max(0.0, (Q - df_q) / C)
    else:
        tau_sq = 0.0
    
    # Random effects weights
    w_star_i = 1.0 / (variances + tau_sq)
    
    # Pooled effect (random)
    mu_RE = np.sum(w_star_i * effects_arr) / np.sum(w_star_i)
    
    # Standard error of pooled effect
    se_RE = math.sqrt(1.0 / np.sum(w_star_i))
    
    # 95% CI
    ci_lower = mu_RE - 1.96 * se_RE
    ci_upper = mu_RE + 1.96 * se_RE
    
    # I-squared (inconsistency)
    if Q > df_q:
        i_sq = 100.0 * (Q - df_q) / Q
    else:
        i_sq = 0.0
    
    return MetaAnalysisStats(
        pooled_effect=mu_RE,
        se=se_RE,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        k=k,
        i_squared=i_sq,
        q_stat=Q,
        q_pval=q_pval,
        tau_squared=tau_sq
    )

def perform_subgroup_analysis(
    df: pd.DataFrame,
    group_col: str,
    effect_col: str = 'hedges_g',
    se_col: str = 'se'
) -> SubgroupAnalysisResult:
    """
    Perform subgroup analysis by splitting data based on a categorical column.
    
    Args:
        df: DataFrame containing effect sizes and grouping variable.
        group_col: Column name for grouping (e.g., 'delivery_format').
        effect_col: Column name for effect sizes.
        se_col: Column name for standard errors.
        
    Returns:
        SubgroupAnalysisResult object.
    """
    if group_col not in df.columns:
        raise ValueError(f"Group column '{group_col}' not found in DataFrame.")
    
    groups = df[group_col].unique()
    subgroup_results = []
    all_effects = []
    all_vars = [] # For between-group Q calculation
    
    logger.info(f"Performing subgroup analysis for '{group_col}' with {len(groups)} groups.")
    
    for grp in groups:
        if pd.isna(grp):
            continue
        sub_df = df[df[group_col] == grp].copy()
        
        if len(sub_df) < 2:
            logger.warning(f"Subgroup '{grp}' has fewer than 2 studies. Skipping meta-analysis for this group.")
            # Still include in between-group calc if possible, but mark as skipped in result
            subgroup_results.append(SubgroupResult(
                subgroup_name=str(grp),
                pooled_effect=np.nan,
                se=np.nan,
                ci_lower=np.nan,
                ci_upper=np.nan,
                k=len(sub_df),
                i_squared=np.nan,
                q_stat=np.nan,
                q_pval=np.nan,
                tau_squared=np.nan
            ))
            continue
        
        effects = sub_df[effect_col].tolist()
        ses = sub_df[se_col].tolist()
        
        stats_res = run_random_effects_meta_analysis(effects, ses)
        
        subgroup_results.append(SubgroupResult(
            subgroup_name=str(grp),
            pooled_effect=stats_res.pooled_effect,
            se=stats_res.se,
            ci_lower=stats_res.ci_lower,
            ci_upper=stats_res.ci_upper,
            k=stats_res.k,
            i_squared=stats_res.i_squared,
            q_stat=stats_res.q_stat,
            q_pval=stats_res.q_pval,
            tau_squared=stats_res.tau_squared
        ))
        
        # Collect for between-group test
        all_effects.extend(effects)
        all_vars.extend([s**2 for s in ses])
    
    # Between-group Q test (simplified: assuming independence of subgroups)
    # Q_between = Q_total - Q_within
    # This is a standard approximation in meta-analysis
    
    # Calculate Q_within (sum of Qs from subgroups)
    q_within = sum(r.q_stat for r in subgroup_results if not np.isnan(r.q_stat))
    df_within = sum(r.k - 1 for r in subgroup_results if not np.isnan(r.q_stat))
    
    # Calculate Q_total on the whole dataset (ignoring groups)
    if len(all_effects) >= 2:
        stats_total = run_random_effects_meta_analysis(all_effects, [math.sqrt(v) for v in all_vars])
        q_total = stats_total.q_stat
        df_total = len(all_effects) - 1
        
        q_between = q_total - q_within
        df_between = df_total - df_within
        
        if df_between > 0:
            p_between = 1.0 - stats.chi2.cdf(q_between, df_between)
        else:
            q_between = np.nan
            p_between = np.nan
    else:
        q_between = np.nan
        p_between = np.nan
        
    return SubgroupAnalysisResult(
        analysis_name=f"Subgroup Analysis: {group_col}",
        between_q_stat=q_between,
        between_q_pval=p_between,
        subgroup_results=subgroup_results
    )

def perform_follow_up_subgroup_analysis(
    df: pd.DataFrame,
    follow_up_col: str = 'follow_up',
    effect_col: str = 'hedges_g',
    se_col: str = 'se'
) -> SubgroupAnalysisResult:
    """
    Perform subgroup analysis based on follow-up duration.
    Groups: '3-month' vs 'others'.
    
    Logic:
    - If follow_up string contains '3' and 'month' (case insensitive), classify as '3-month'.
    - Otherwise, classify as 'others'.
    
    Args:
        df: DataFrame with study data.
        follow_up_col: Column name for follow-up duration.
        effect_col: Column name for effect sizes.
        se_col: Column name for standard errors.
        
    Returns:
        SubgroupAnalysisResult object.
    """
    if follow_up_col not in df.columns:
        raise ValueError(f"Follow-up column '{follow_up_col}' not found in DataFrame.")
    
    def categorize_follow_up(val):
        if pd.isna(val) or val == '':
            return 'others'
        val_str = str(val).lower()
        # Check for 3-month indicators
        if '3' in val_str and ('month' in val_str or 'mo' in val_str):
            return '3-month'
        return 'others'
    
    df_temp = df.copy()
    df_temp['follow_up_group'] = df_temp[follow_up_col].apply(categorize_follow_up)
    
    # Log distribution
    group_counts = df_temp['follow_up_group'].value_counts()
    logger.info(f"Follow-up distribution: {group_counts.to_dict()}")
    
    return perform_subgroup_analysis(
        df_temp,
        group_col='follow_up_group',
        effect_col=effect_col,
        se_col=se_col
    )

def create_meta_analysis_result(
    df: pd.DataFrame,
    output_path: str
) -> Dict[str, Any]:
    """
    Run all relevant subgroup analyses and save results.
    
    Args:
        df: Cleaned study DataFrame.
        output_path: Path to save the results JSON/CSV.
        
    Returns:
        Dictionary containing all analysis results.
    """
    results = {}
    
    # 1. Overall Meta-Analysis
    if len(df) >= 2:
        overall = run_random_effects_meta_analysis(
            df['hedges_g'].tolist(),
            df['se'].tolist()
        )
        results['overall'] = {
            'pooled_effect': overall.pooled_effect,
            'se': overall.se,
            'ci_lower': overall.ci_lower,
            'ci_upper': overall.ci_upper,
            'k': overall.k,
            'i_squared': overall.i_squared,
            'q_stat': overall.q_stat,
            'q_pval': overall.q_pval,
            'tau_squared': overall.tau_squared
        }
    else:
        results['overall'] = {'error': 'Insufficient studies for meta-analysis (N < 2)'}
    
    # 2. Subgroup: Mindfulness Components
    if 'intervention_components' in df.columns:
        # Binary: present/absent
        def has_mindfulness(val):
            if pd.isna(val) or val == '':
                return 'absent'
            # Assuming list or string representation of components
            # If it's a list, check length; if string, check if not empty
            if isinstance(val, list):
                return 'present' if len(val) > 0 else 'absent'
            return 'present' if val else 'absent'
        
        df_temp = df.copy()
        df_temp['mindfulness_binary'] = df_temp['intervention_components'].apply(has_mindfulness)
        results['mindfulness_subgroup'] = perform_subgroup_analysis(
            df_temp, 'mindfulness_binary'
        ).__dict__
    
    # 3. Subgroup: Delivery Format
    if 'delivery_format' in df.columns:
        results['delivery_format_subgroup'] = perform_subgroup_analysis(
            df, 'delivery_format'
        ).__dict__
    
    # 4. Subgroup: Social Skill Domain
    if 'social_skill_domain' in df.columns:
        results['domain_subgroup'] = perform_subgroup_analysis(
            df, 'social_skill_domain'
        ).__dict__
    
    # 5. Subgroup: Follow-up Duration (T032)
    if 'follow_up' in df.columns:
        results['follow_up_subgroup'] = perform_follow_up_subgroup_analysis(
            df, 'follow_up'
        ).__dict__
    
    # Save results
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Convert non-serializable objects (like dataclasses) to dict
    serializable_results = {}
    for k, v in results.items():
        if hasattr(v, '__dict__'):
            serializable_results[k] = v.__dict__
        else:
            serializable_results[k] = v
    
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, default=str)
    
    logger.info(f"Meta-analysis results saved to {output_path}")
    return results

def save_meta_analysis_results(results: Dict[str, Any], output_path: str):
    """Helper to save results if not already done in create_meta_analysis_result."""
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

def main():
    """
    Entry point for running meta-analysis on cleaned data.
    Expects data/processed/cleaned_studies.csv to exist.
    """
    data_path = get_data_path()
    input_file = os.path.join(data_path, 'processed', 'cleaned_studies.csv')
    output_file = os.path.join(data_path, 'processed', 'meta_analysis_results.json')
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T021 (verify_output) has run successfully and generated cleaned_studies.csv.")
        return 1
    
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} studies from {input_file}")
        
        # Check required columns
        required_cols = ['hedges_g', 'se']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logger.error(f"Missing required columns in input data: {missing}")
            return 1
        
        results = create_meta_analysis_result(df, output_file)
        logger.info("Meta-analysis completed successfully.")
        return 0
        
    except Exception as e:
        logger.exception(f"Error during meta-analysis: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
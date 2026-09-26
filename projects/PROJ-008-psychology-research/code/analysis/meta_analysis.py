"""
Meta-analysis engine for pooling effect sizes and performing subgroup analyses.
"""
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import math
import numpy as np
import pandas as pd
from code.utils.logging import get_logger
from code.utils.config import get_config

logger = get_logger(__name__)
config = get_config()

@dataclass
class MetaAnalysisStats:
    pooled_effect_size: float
    se: float
    ci_lower: float
    ci_upper: float
    i_squared: float
    q_statistic: float
    df: int
    p_value: float
    model_type: str  # 'fixed' or 'random'

@dataclass
class SubgroupResult:
    subgroup_name: str
    n_studies: int
    pooled_effect_size: float
    se: float
    ci_lower: float
    ci_upper: float
    i_squared: float
    q_statistic: float
    df: int
    p_value: float
    model_type: str

@dataclass
class SubgroupAnalysisResult:
    results: List[SubgroupResult] = field(default_factory=list)
    q_between: float = 0.0
    p_between: float = 1.0
    df_between: int = 0

def calculate_hedges_g_correction(j: float) -> float:
    """Calculate Hedges' g correction factor for small sample bias."""
    return 1.0 - (3.0 / (4.0 * j - 1.0))

def run_random_effects_meta_analysis(effect_sizes: List[Dict[str, Any]]) -> MetaAnalysisStats:
    """
    Perform random-effects meta-analysis using the DerSimonian-Laird method.
    
    Args:
        effect_sizes: List of dicts with keys 'hedges_g', 'se'
        
    Returns:
        MetaAnalysisStats object with pooled results
    """
    if not effect_sizes:
        raise ValueError("No effect sizes provided for meta-analysis")
        
    k = len(effect_sizes)
    g = np.array([es['hedges_g'] for es in effect_sizes])
    se = np.array([es['se'] for es in effect_sizes])
    v = se ** 2  # Variance of effect sizes
    
    # Fixed-effects weights
    w_fe = 1.0 / v
    sum_w = np.sum(w_fe)
    sum_wg = np.sum(w_fe * g)
    theta_fe = sum_wg / sum_w
    
    # Calculate Q statistic
    q = np.sum(w_fe * (g - theta_fe) ** 2)
    df = k - 1
    
    # DerSimonian-Laird estimator for tau^2
    if df > 0:
        c = sum_w - (np.sum(w_fe ** 2) / sum_w)
        tau_sq = max(0, (q - df) / c) if c > 0 else 0
    else:
        tau_sq = 0
        
    # Random-effects weights
    v_re = v + tau_sq
    w_re = 1.0 / v_re
    sum_w_re = np.sum(w_re)
    sum_wg_re = np.sum(w_re * g)
    theta_re = sum_wg_re / sum_w_re
    
    # Standard error of pooled effect
    se_re = np.sqrt(1.0 / sum_w_re)
    
    # 95% CI
    z_95 = 1.96
    ci_lower = theta_re - z_95 * se_re
    ci_upper = theta_re + z_95 * se_re
    
    # Heterogeneity I^2
    i_squared = max(0, (q - df) / q * 100) if q > 0 else 0
    
    # P-value for Q statistic (chi-square)
    from scipy.stats import chi2
    p_value = 1 - chi2.cdf(q, df) if df > 0 else 1.0
    
    model_type = 'random' if i_squared > 50 else 'fixed'
    
    return MetaAnalysisStats(
        pooled_effect_size=theta_re,
        se=se_re,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        i_squared=i_squared,
        q_statistic=q,
        df=df,
        p_value=p_value,
        model_type=model_type
    )

def perform_subgroup_analysis(
    effect_sizes: List[Dict[str, Any]], 
    subgroup_var: str, 
    df: pd.DataFrame
) -> SubgroupAnalysisResult:
    """
    Perform subgroup analysis based on a categorical variable.
    
    Args:
        effect_sizes: List of effect size dicts
        subgroup_var: Column name in df to group by
        df: DataFrame containing study metadata
        
    Returns:
        SubgroupAnalysisResult object
    """
    if not effect_sizes or len(effect_sizes) != len(df):
        raise ValueError("Mismatch between effect sizes and dataframe length")
        
    # Create mapping from study_id to effect size
    es_map = {es.get('study_id', f'study_{i}'): es for i, es in enumerate(effect_sizes)}
    
    # Add effect sizes to df
    df_temp = df.copy()
    df_temp['hedges_g'] = [es_map.get(sid, {}).get('hedges_g', 0) for sid in df_temp['id']]
    df_temp['se'] = [es_map.get(sid, {}).get('se', 0) for sid in df_temp['id']]
    
    # Group by subgroup variable
    groups = df_temp.groupby(subgroup_var)
    results = []
    
    for name, group in groups:
        group_es = [
            {'hedges_g': row['hedges_g'], 'se': row['se']}
            for _, row in group.iterrows()
            if pd.notna(row['hedges_g']) and pd.notna(row['se'])
        ]
        
        if len(group_es) < 2:
            logger.warning(f"Subgroup '{name}' has fewer than 2 studies, skipping meta-analysis")
            continue
            
        stats = run_random_effects_meta_analysis(group_es)
        
        results.append(SubgroupResult(
            subgroup_name=str(name),
            n_studies=len(group_es),
            pooled_effect_size=stats.pooled_effect_size,
            se=stats.se,
            ci_lower=stats.ci_lower,
            ci_upper=stats.ci_upper,
            i_squared=stats.i_squared,
            q_statistic=stats.q_statistic,
            df=stats.df,
            p_value=stats.p_value,
            model_type=stats.model_type
        ))
    
    # Calculate Q_between (test for differences between subgroups)
    # Simplified: weighted sum of squares between subgroup means and overall mean
    if len(results) > 1:
        overall_stats = run_random_effects_meta_analysis(effect_sizes)
        q_between = 0
        for res in results:
            diff = res.pooled_effect_size - overall_stats.pooled_effect_size
            q_between += (res.n_studies * (diff ** 2)) / (res.se ** 2) if res.se > 0 else 0
        
        from scipy.stats import chi2
        p_between = 1 - chi2.cdf(q_between, len(results) - 1)
        df_between = len(results) - 1
    else:
        q_between = 0
        p_between = 1.0
        df_between = 0
        
    return SubgroupAnalysisResult(
        results=results,
        q_between=q_between,
        p_between=p_between,
        df_between=df_between
    )

def parse_follow_up_to_days(follow_up_str: str) -> Optional[int]:
    """Parse follow-up duration string to days."""
    if not follow_up_str or pd.isna(follow_up_str):
        return None
        
    follow_up_str = str(follow_up_str).lower()
    
    # Common patterns
    if 'month' in follow_up_str:
        months = float(follow_up_str.split()[0])
        return int(months * 30.44)  # Average days per month
    elif 'week' in follow_up_str:
        weeks = float(follow_up_str.split()[0])
        return int(weeks * 7)
    elif 'day' in follow_up_str:
        days = float(follow_up_str.split()[0])
        return int(days)
    elif 'year' in follow_up_str:
        years = float(follow_up_str.split()[0])
        return int(years * 365.25)
    else:
        # Try to extract any number
        import re
        match = re.search(r'(\d+\.?\d*)', follow_up_str)
        if match:
            return int(float(match.group(1)))
        return None

def perform_follow_up_subgroup_analysis(
    effect_sizes: List[Dict[str, Any]],
    df: pd.DataFrame
) -> SubgroupAnalysisResult:
    """
    Perform subgroup analysis based on follow-up duration (<90 days vs >=90 days).
    """
    df_temp = df.copy()
    df_temp['follow_up_days'] = df_temp['follow_up'].apply(parse_follow_up_to_days)
    
    # Create binary grouping
    df_temp['follow_up_group'] = df_temp['follow_up_days'].apply(
        lambda x: '<90 days' if x is not None and x < 90 else '>=90 days' if x is not None else 'missing'
    )
    
    # Filter out missing
    df_filtered = df_temp[df_temp['follow_up_group'] != 'missing']
    
    if len(df_filtered) < 4:
        logger.warning("Insufficient studies with follow-up data for subgroup analysis")
        return SubgroupAnalysisResult(results=[])
        
    return perform_subgroup_analysis(effect_sizes, 'follow_up_group', df_filtered)

def perform_blinding_bias_quantification(
    effect_sizes: List[Dict[str, Any]],
    df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Quantify blinding bias by comparing pooled effect sizes between blinded and unblinded studies.
    
    This addresses Constitution Principle VII and FR-005 by measuring expectation bias
    in outcome assessment.
    
    Args:
        effect_sizes: List of effect size dicts with 'study_id', 'hedges_g', 'se'
        df: DataFrame with study metadata including 'blinded_assessment_flag'
        
    Returns:
        Dict with blinding bias analysis results
    """
    if not effect_sizes or len(effect_sizes) != len(df):
        raise ValueError("Mismatch between effect sizes and dataframe length")
        
    # Create mapping from study_id to effect size
    es_map = {es.get('study_id', f'study_{i}'): es for i, es in enumerate(effect_sizes)}
    
    # Add effect sizes and blinding status to df
    df_temp = df.copy()
    df_temp['hedges_g'] = [es_map.get(sid, {}).get('hedges_g', np.nan) for sid in df_temp['id']]
    df_temp['se'] = [es_map.get(sid, {}).get('se', np.nan) for sid in df_temp['id']]
    
    # Ensure blinded_assessment_flag is boolean
    if 'blinded_assessment_flag' not in df_temp.columns:
        logger.warning("Column 'blinded_assessment_flag' not found in dataframe")
        return {
            'status': 'skipped',
            'reason': 'Missing blinded_assessment_flag column',
            'blinded_n': 0,
            'unblinded_n': 0
        }
    
    df_temp['blinded_assessment_flag'] = df_temp['blinded_assessment_flag'].astype(bool)
    
    # Group by blinding status
    blinded_studies = df_temp[df_temp['blinded_assessment_flag'] == True]
    unblinded_studies = df_temp[df_temp['blinded_assessment_flag'] == False]
    
    n_blinded = len(blinded_studies)
    n_unblinded = len(unblinded_studies)
    
    logger.info(f"Blinding bias analysis: {n_blinded} blinded, {n_unblinded} unblinded studies")
    
    # Check minimum sample size requirement
    if n_blinded < 3 or n_unblinded < 3:
        logger.warning(
            f"Insufficient studies for blinding bias analysis: "
            f"blinded={n_blinded} (need >=3), unblinded={n_unblinded} (need >=3). "
            f"Skipping analysis and logging warning."
        )
        return {
            'status': 'skipped',
            'reason': f'Insufficient sample size (blinded={n_blinded}, unblinded={n_unblinded})',
            'blinded_n': n_blinded,
            'unblinded_n': n_unblinded
        }
    
    # Calculate pooled effect sizes for each group
    blinded_es = [
        {'hedges_g': row['hedges_g'], 'se': row['se']}
        for _, row in blinded_studies.iterrows()
        if pd.notna(row['hedges_g']) and pd.notna(row['se'])
    ]
    
    unblinded_es = [
        {'hedges_g': row['hedges_g'], 'se': row['se']}
        for _, row in unblinded_studies.iterrows()
        if pd.notna(row['hedges_g']) and pd.notna(row['se'])
    ]
    
    if len(blinded_es) < 2 or len(unblinded_es) < 2:
        logger.warning("Insufficient valid effect sizes in one or both groups")
        return {
            'status': 'skipped',
            'reason': 'Insufficient valid effect sizes in groups',
            'blinded_n': len(blinded_es),
            'unblinded_n': len(unblinded_es)
        }
    
    blinded_stats = run_random_effects_meta_analysis(blinded_es)
    unblinded_stats = run_random_effects_meta_analysis(unblinded_es)
    
    # Calculate difference in effect sizes
    diff = unblinded_stats.pooled_effect_size - blinded_stats.pooled_effect_size
    se_diff = np.sqrt(blinded_stats.se**2 + unblinded_stats.se**2)
    
    # Calculate z-score and p-value for the difference
    z_score = diff / se_diff if se_diff > 0 else 0
    from scipy.stats import norm
    p_value = 2 * (1 - norm.cdf(abs(z_score)))
    
    # Determine significance
    is_significant = p_value < 0.05
    
    result = {
        'status': 'completed',
        'blinded_n': n_blinded,
        'unblinded_n': n_unblinded,
        'blinded_effect_size': blinded_stats.pooled_effect_size,
        'blinded_se': blinded_stats.se,
        'blinded_ci_lower': blinded_stats.ci_lower,
        'blinded_ci_upper': blinded_stats.ci_upper,
        'unblinded_effect_size': unblinded_stats.pooled_effect_size,
        'unblinded_se': unblinded_stats.se,
        'unblinded_ci_lower': unblinded_stats.ci_lower,
        'unblinded_ci_upper': unblinded_stats.ci_upper,
        'difference': diff,
        'se_difference': se_diff,
        'z_score': z_score,
        'p_value': p_value,
        'is_significant': is_significant,
        'interpretation': (
            f"{'Significant' if is_significant else 'No significant'} difference in effect sizes "
            f"between blinded (g={blinded_stats.pooled_effect_size:.3f}) and unblinded "
            f"(g={unblinded_stats.pooled_effect_size:.3f}) studies (p={p_value:.4f}). "
            f"Difference: {diff:.3f}."
        )
    }
    
    logger.info(f"Blinding bias analysis complete: {result['interpretation']}")
    return result

def create_meta_analysis_result(
    stats: MetaAnalysisStats,
    subgroup_results: Optional[Dict[str, SubgroupAnalysisResult]] = None,
    blinding_bias: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a comprehensive meta-analysis result dictionary."""
    result = {
        'pooled_effect_size': stats.pooled_effect_size,
        'se': stats.se,
        'ci_lower': stats.ci_lower,
        'ci_upper': stats.ci_upper,
        'i_squared': stats.i_squared,
        'q_statistic': stats.q_statistic,
        'df': stats.df,
        'p_value': stats.p_value,
        'model_type': stats.model_type
    }
    
    if subgroup_results:
        result['subgroup_analyses'] = {}
        for name, sub_result in subgroup_results.items():
            result['subgroup_analyses'][name] = {
                'results': [
                    {
                        'subgroup_name': r.subgroup_name,
                        'n_studies': r.n_studies,
                        'pooled_effect_size': r.pooled_effect_size,
                        'se': r.se,
                        'ci_lower': r.ci_lower,
                        'ci_upper': r.ci_upper,
                        'i_squared': r.i_squared,
                        'q_statistic': r.q_statistic,
                        'df': r.df,
                        'p_value': r.p_value,
                        'model_type': r.model_type
                    }
                    for r in sub_result.results
                ],
                'q_between': sub_result.q_between,
                'p_between': sub_result.p_between,
                'df_between': sub_result.df_between
            }
    
    if blinding_bias:
        result['blinding_bias_analysis'] = blinding_bias
        
    return result

def save_meta_analysis_results(results: Dict[str, Any], output_path: str):
    """Save meta-analysis results to JSON file."""
    import json
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Meta-analysis results saved to {output_path}")

def main():
    """Main entry point for meta-analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run meta-analysis on effect sizes')
    parser.add_argument('--input', type=str, required=True, help='Input CSV with effect sizes')
    parser.add_argument('--output', type=str, required=True, help='Output JSON for results')
    parser.add_argument('--plots-dir', type=str, default='viz/', help='Directory for plots')
    args = parser.parse_args()
    
    logger.info(f"Loading effect sizes from {args.input}")
    df_es = pd.read_csv(args.input)
    
    # Load study metadata for subgroup analysis
    # Assuming effect sizes CSV has 'study_id' that maps to cleaned studies
    cleaned_studies_path = os.path.join(os.path.dirname(args.input), '..', 'processed', 'cleaned_studies.csv')
    if os.path.exists(cleaned_studies_path):
        df_studies = pd.read_csv(cleaned_studies_path)
    else:
        logger.warning("Cleaned studies file not found, skipping subgroup analyses")
        df_studies = None
    
    # Convert to list of dicts for meta-analysis
    effect_sizes = df_es.to_dict('records')
    
    # Run main meta-analysis
    logger.info("Running random-effects meta-analysis")
    stats = run_random_effects_meta_analysis(effect_sizes)
    logger.info(f"Pooled effect size: {stats.pooled_effect_size:.3f} (95% CI: {stats.ci_lower:.3f} to {stats.ci_upper:.3f})")
    logger.info(f"Heterogeneity: I² = {stats.i_squared:.1f}%, Q = {stats.q_statistic:.3f}, p = {stats.p_value:.4f}")
    
    results = create_meta_analysis_result(stats)
    
    # Perform subgroup analyses if study metadata available
    if df_studies is not None and len(df_studies) > 0:
        logger.info("Performing subgroup analyses")
        
        # Mindfulness components (binary)
        if 'intervention_components' in df_studies.columns:
            df_studies['mindfulness_present'] = df_studies['intervention_components'].apply(
                lambda x: 'present' if x and x != '[]' and x != 'nan' and x != 'none' else 'absent'
            )
            subgroup_results = perform_subgroup_analysis(effect_sizes, 'mindfulness_present', df_studies)
            results['subgroup_analyses']['mindfulness_components'] = {
                'results': [
                    {
                        'subgroup_name': r.subgroup_name,
                        'n_studies': r.n_studies,
                        'pooled_effect_size': r.pooled_effect_size,
                        'se': r.se,
                        'ci_lower': r.ci_lower,
                        'ci_upper': r.ci_upper,
                        'i_squared': r.i_squared,
                        'q_between': subgroup_results.q_between,
                        'p_between': subgroup_results.p_between
                    }
                    for r in subgroup_results.results
                ]
            }
        
        # Delivery format
        if 'delivery_format' in df_studies.columns:
            subgroup_results = perform_subgroup_analysis(effect_sizes, 'delivery_format', df_studies)
            results['subgroup_analyses']['delivery_format'] = {
                'results': [
                    {
                        'subgroup_name': r.subgroup_name,
                        'n_studies': r.n_studies,
                        'pooled_effect_size': r.pooled_effect_size,
                        'se': r.se,
                        'ci_lower': r.ci_lower,
                        'ci_upper': r.ci_upper,
                        'i_squared': r.i_squared,
                        'q_between': subgroup_results.q_between,
                        'p_between': subgroup_results.p_between
                    }
                    for r in subgroup_results.results
                ]
            }
        
        # Social skill domain
        if 'social_skill_domain' in df_studies.columns:
            subgroup_results = perform_subgroup_analysis(effect_sizes, 'social_skill_domain', df_studies)
            results['subgroup_analyses']['social_skill_domain'] = {
                'results': [
                    {
                        'subgroup_name': r.subgroup_name,
                        'n_studies': r.n_studies,
                        'pooled_effect_size': r.pooled_effect_size,
                        'se': r.se,
                        'ci_lower': r.ci_lower,
                        'ci_upper': r.ci_upper,
                        'i_squared': r.i_squared,
                        'q_between': subgroup_results.q_between,
                        'p_between': subgroup_results.p_between
                    }
                    for r in subgroup_results.results
                ]
            }
        
        # Follow-up duration
        if 'follow_up' in df_studies.columns:
            follow_up_results = perform_follow_up_subgroup_analysis(effect_sizes, df_studies)
            results['subgroup_analyses']['follow_up_duration'] = {
                'results': [
                    {
                        'subgroup_name': r.subgroup_name,
                        'n_studies': r.n_studies,
                        'pooled_effect_size': r.pooled_effect_size,
                        'se': r.se,
                        'ci_lower': r.ci_lower,
                        'ci_upper': r.ci_upper,
                        'i_squared': r.i_squared,
                        'q_between': follow_up_results.q_between,
                        'p_between': follow_up_results.p_between
                    }
                    for r in follow_up_results.results
                ]
            }
        
        # Blinding bias quantification (T033b)
        logger.info("Performing blinding bias quantification (T033b)")
        blinding_bias = perform_blinding_bias_quantification(effect_sizes, df_studies)
        results['blinding_bias_analysis'] = blinding_bias
        
        # Log blinding bias results
        if blinding_bias['status'] == 'completed':
            logger.info(f"Blinding bias difference: {blinding_bias['difference']:.3f} (p={blinding_bias['p_value']:.4f})")
            if blinding_bias['is_significant']:
                logger.warning(
                    "Significant blinding bias detected: unblinded studies show larger effects. "
                    "This suggests expectation bias in outcome assessment (Kahneman-simulated review concern)."
                )
        else:
            logger.warning(f"Blinding bias analysis skipped: {blinding_bias.get('reason', 'Unknown reason')}")
    
    # Save results
    save_meta_analysis_results(results, args.output)
    logger.info(f"Meta-analysis complete. Results saved to {args.output}")

if __name__ == '__main__':
    main()
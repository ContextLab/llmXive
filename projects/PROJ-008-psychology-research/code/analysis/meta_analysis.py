import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import math
import numpy as np
import pandas as pd
from scipy import stats
from code.utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class MetaAnalysisStats:
    pooled_effect: float
    se: float
    ci_lower: float
    ci_upper: float
    i_squared: float
    q_statistic: float
    p_value: float

@dataclass
class SubgroupResult:
    group_name: str
    n_studies: int
    pooled_effect: float
    se: float
    ci_lower: float
    ci_upper: float

@dataclass
class SubgroupAnalysisResult:
    subgroup_results: List[SubgroupResult]
    heterogeneity_between_groups: float
    p_value: float

def calculate_hedges_g_correction(j: float, effect: float) -> float:
    """Apply small-sample correction to Hedges' g."""
    return j * effect

def run_random_effects_meta_analysis(effect_sizes: List[float], ses: List[float]) -> MetaAnalysisStats:
    """Run random-effects meta-analysis using inverse variance weighting."""
    n = len(effect_sizes)
    if n == 0:
        raise ValueError("No effect sizes provided")
    
    # Calculate weights (inverse variance)
    weights = [1 / (se ** 2) for se in ses]
    total_weight = sum(weights)
    
    # Pooled effect
    pooled = sum(w * e for w, e in zip(weights, effect_sizes)) / total_weight
    
    # Standard error of pooled effect
    se_pooled = math.sqrt(1 / total_weight)
    
    # 95% CI
    ci_lower = pooled - 1.96 * se_pooled
    ci_upper = pooled + 1.96 * se_pooled
    
    # Heterogeneity (simplified I² calculation)
    # Q statistic
    q = sum(w * (e - pooled) ** 2 for w, e in zip(weights, effect_sizes))
    
    # Tau² (between-study variance) - simplified estimator
    df = n - 1
    if df > 0:
        tau_squared = max(0, (q - df) / (sum(weights) - sum(w**2 for w in weights) / total_weight))
    else:
        tau_squared = 0
    
    # I² = (Q - df) / Q
    if q > df:
        i_squared = (q - df) / q
    else:
        i_squared = 0
    
    # P-value for Q statistic (chi-square with df-1)
    p_value = 1 - stats.chi2.cdf(q, df) if df > 0 else 1.0
    
    return MetaAnalysisStats(
        pooled_effect=pooled,
        se=se_pooled,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        i_squared=i_squared,
        q_statistic=q,
        p_value=p_value
    )

def perform_subgroup_analysis(df: pd.DataFrame, group_column: str) -> SubgroupAnalysisResult:
    """Perform subgroup analysis by a categorical column."""
    groups = df[group_column].unique()
    subgroup_results = []
    
    for group in groups:
        if pd.isna(group):
            continue
        subset = df[df[group_column] == group]
        if len(subset) == 0:
            continue
        
        effects = subset["hedges_g"].tolist()
        ses = subset["se"].tolist()
        
        if len(effects) == 0:
            continue
        
        stats_result = run_random_effects_meta_analysis(effects, ses)
        subgroup_results.append(SubgroupResult(
            group_name=str(group),
            n_studies=len(effects),
            pooled_effect=stats_result.pooled_effect,
            se=stats_result.se,
            ci_lower=stats_result.ci_lower,
            ci_upper=stats_result.ci_upper
        ))
    
    # Calculate heterogeneity between groups (simplified)
    if len(subgroup_results) < 2:
        return SubgroupAnalysisResult(
            subgroup_results=subgroup_results,
            heterogeneity_between_groups=0.0,
            p_value=1.0
        )
    
    # Simplified Q-test for subgroup differences
    overall_pooled = sum(r.pooled_effect * r.n_studies for r in subgroup_results) / sum(r.n_studies for r in subgroup_results)
    q_between = sum(r.n_studies * (r.pooled_effect - overall_pooled) ** 2 for r in subgroup_results)
    p_value = 1 - stats.chi2.cdf(q_between, len(subgroup_results) - 1)
    
    return SubgroupAnalysisResult(
        subgroup_results=subgroup_results,
        heterogeneity_between_groups=q_between,
        p_value=p_value
    )

def parse_follow_up_to_days(follow_up_str: str) -> Optional[int]:
    """Parse follow-up string to days."""
    if not follow_up_str or follow_up_str == "null":
        return None
    
    follow_up_str = str(follow_up_str).lower()
    
    if "month" in follow_up_str:
        match = re.search(r"(\d+)\s*month", follow_up_str)
        if match:
            return int(match.group(1)) * 30
    elif "week" in follow_up_str:
        match = re.search(r"(\d+)\s*week", follow_up_str)
        if match:
            return int(match.group(1)) * 7
    elif "day" in follow_up_str:
        match = re.search(r"(\d+)\s*day", follow_up_str)
        if match:
            return int(match.group(1))
    
    return None

def perform_follow_up_subgroup_analysis(df: pd.DataFrame) -> SubgroupAnalysisResult:
    """Perform follow-up duration subgroup analysis."""
    # Group by <90 days vs >=90 days
    df["follow_up_days"] = df["follow_up"].apply(parse_follow_up_to_days)
    
    groups = [
        ("<90 days", df[(df["follow_up_days"] < 90) | (df["follow_up_days"].isna())]),
        (">=90 days", df[(df["follow_up_days"] >= 90)])
    ]
    
    subgroup_results = []
    for group_name, subset in groups:
        if len(subset) == 0:
            continue
        
        effects = subset["hedges_g"].tolist()
        ses = subset["se"].tolist()
        
        if len(effects) == 0:
            continue
        
        stats_result = run_random_effects_meta_analysis(effects, ses)
        subgroup_results.append(SubgroupResult(
            group_name=group_name,
            n_studies=len(effects),
            pooled_effect=stats_result.pooled_effect,
            se=stats_result.se,
            ci_lower=stats_result.ci_lower,
            ci_upper=stats_result.ci_upper
        ))
    
    # Calculate heterogeneity
    if len(subgroup_results) < 2:
        return SubgroupAnalysisResult(
            subgroup_results=subgroup_results,
            heterogeneity_between_groups=0.0,
            p_value=1.0
        )
    
    overall_pooled = sum(r.pooled_effect * r.n_studies for r in subgroup_results) / sum(r.n_studies for r in subgroup_results)
    q_between = sum(r.n_studies * (r.pooled_effect - overall_pooled) ** 2 for r in subgroup_results)
    p_value = 1 - stats.chi2.cdf(q_between, len(subgroup_results) - 1)
    
    return SubgroupAnalysisResult(
        subgroup_results=subgroup_results,
        heterogeneity_between_groups=q_between,
        p_value=p_value
    )

def perform_blinding_bias_quantification(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Quantify blinding bias by comparing effect sizes between blinded and unblinded studies.
    
    Logic:
    1. If N >= 10, calculate the difference in pooled effect sizes between the two groups.
    2. If N < 10, return None and log a warning.
    3. Output: Quantify the difference and report p-value.
    """
    n_total = len(df)
    
    if n_total < 10:
        logger.warning(f"Insufficient studies (N={n_total} < 10) for blinding bias quantification.")
        return None
    
    # Separate by blinding status
    blinded = df[df["blinded_assessment_flag"] == True]
    unblinded = df[df["blinded_assessment_flag"] == False]
    
    if len(blinded) == 0 or len(unblinded) == 0:
        logger.warning("Cannot perform blinding bias analysis: one group is empty.")
        return None
    
    # Calculate pooled effects for each group
    blinded_stats = run_random_effects_meta_analysis(
        blinded["hedges_g"].tolist(),
        blinded["se"].tolist()
    )
    
    unblinded_stats = run_random_effects_meta_analysis(
        unblinded["hedges_g"].tolist(),
        unblinded["se"].tolist()
    )
    
    # Calculate difference
    effect_difference = unblinded_stats.pooled_effect - blinded_stats.pooled_effect
    
    # Calculate standard error of difference (simplified)
    se_diff = math.sqrt(blinded_stats.se**2 + unblinded_stats.se**2)
    
    # Z-test for difference
    z_stat = effect_difference / se_diff if se_diff > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    return {
        "blinded_pooled": blinded_stats.pooled_effect,
        "unblinded_pooled": unblinded_stats.pooled_effect,
        "effect_difference": effect_difference,
        "se_difference": se_diff,
        "z_statistic": z_stat,
        "p_value": p_value,
        "n_blinded": len(blinded),
        "n_unblinded": len(unblinded)
    }

def create_meta_analysis_result(df: pd.DataFrame) -> Dict[str, Any]:
    """Create a comprehensive meta-analysis result."""
    effects = df["hedges_g"].tolist()
    ses = df["se"].tolist()
    
    if len(effects) == 0:
        return {}
    
    overall_stats = run_random_effects_meta_analysis(effects, ses)
    
    # Subgroup by social skill domain
    domain_analysis = perform_subgroup_analysis(df, "social_skill_domain")
    
    # Subgroup by delivery format
    format_analysis = perform_subgroup_analysis(df, "delivery_format")
    
    # Blinding bias quantification
    blinding_result = perform_blinding_bias_quantification(df)
    
    return {
        "overall": {
            "pooled_effect": overall_stats.pooled_effect,
            "se": overall_stats.se,
            "ci_lower": overall_stats.ci_lower,
            "ci_upper": overall_stats.ci_upper,
            "i_squared": overall_stats.i_squared,
            "q_statistic": overall_stats.q_statistic,
            "p_value": overall_stats.p_value
        },
        "by_domain": {
            "subgroups": [r.__dict__ for r in domain_analysis.subgroup_results],
            "heterogeneity": domain_analysis.heterogeneity_between_groups,
            "p_value": domain_analysis.p_value
        },
        "by_format": {
            "subgroups": [r.__dict__ for r in format_analysis.subgroup_results],
            "heterogeneity": format_analysis.heterogeneity_between_groups,
            "p_value": format_analysis.p_value
        },
        "blinding_bias": blinding_result
    }

def save_meta_analysis_results(result: Dict[str, Any], output_path: str) -> None:
    """Save meta-analysis results to JSON."""
    import json
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

def main():
    """Entry point for meta-analysis script."""
    import argparse
    from code.utils.config import get_data_path

    parser = argparse.ArgumentParser(description="Run meta-analysis")
    parser.add_argument("--input", type=str, required=True, help="Input CSV with effect sizes")
    parser.add_argument("--output", type=str, required=True, help="Output JSON for results")
    parser.add_argument("--plots-dir", type=str, default="viz/", help="Directory for plots")
    args = parser.parse_args()

    input_file = Path(args.input)
    output_file = Path(args.output)
    plots_dir = Path(args.plots_dir)
    
    plots_dir.mkdir(parents=True, exist_ok=True)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading effect sizes from {input_file}")
    
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} studies")
    
    if len(df) == 0:
        logger.warning("No studies found for meta-analysis")
        return

    # Run meta-analysis
    result = create_meta_analysis_result(df)
    
    # Save results
    save_meta_analysis_results(result, output_file)
    logger.info(f"Saved meta-analysis results to {output_file}")

if __name__ == "__main__":
    main()
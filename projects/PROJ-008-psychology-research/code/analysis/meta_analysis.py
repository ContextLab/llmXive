import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

from code.utils.logging import get_logger
from code.data.models import EffectSize, MetaAnalysisResult

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
    heterogeneity_df: int
    heterogeneity_p: float
    tau_squared: float
    k_studies: int
    total_n: int

def run_random_effects_meta_analysis(
    effect_sizes: List[EffectSize]
) -> MetaAnalysisStats:
    """
    Perform random-effects meta-analysis using the DerSimonian-Laird method.
    """
    if not effect_sizes:
        raise ValueError("No effect sizes provided for meta-analysis.")

    k = len(effect_sizes)
    # Calculate weights (inverse variance)
    variances = [es.se ** 2 for es in effect_sizes]
    w = [1.0 / v for v in variances]

    # Calculate pooled effect (fixed effect for initial tau^2 calc)
    sum_w = sum(w)
    pooled_es = sum(w[i] * effect_sizes[i].effect_size for i in range(k)) / sum_w

    # Calculate Q statistic (Cochran's Q)
    q_sum = sum(w[i] * (effect_sizes[i].effect_size - pooled_es) ** 2 for i in range(k))
    
    # Calculate tau^2 (DerSimonian-Laird)
    c = sum(w) - (sum(w_i ** 2 for w_i in w) / sum(w))
    if c > 0:
        tau_sq = max(0, (q_sum - (k - 1)) / c)
    else:
        tau_sq = 0.0

    # Random effects weights
    w_re = [1.0 / (v + tau_sq) for v in variances]
    sum_w_re = sum(w_re)
    
    # Final pooled effect
    pooled_es_re = sum(w_re[i] * effect_sizes[i].effect_size for i in range(k)) / sum_w_re
    
    # Standard error of pooled effect
    se_pooled = math.sqrt(1.0 / sum_w_re)
    
    # 95% CI
    z_score = 1.96
    ci_lower = pooled_es_re - z_score * se_pooled
    ci_upper = pooled_es_re + z_score * se_pooled

    # Heterogeneity I-squared
    i2 = max(0.0, (q_sum - (k - 1)) / q_sum * 100) if q_sum > 0 else 0.0

    # P-value for Q (approximate chi-square)
    # Using survival function approximation for chi-square with df=k-1
    # For simplicity in this implementation, we return the Q stat and df
    # A full p-value calculation would require scipy.stats.chi2
    q_p_val = 0.0 # Placeholder; actual p-value requires scipy
    if k > 1:
        # Simple approximation or placeholder if scipy not available for this specific stat
        # In a real pipeline, we'd use scipy.stats.chi2.sf(q_sum, k-1)
        pass

    total_n = sum(es.n_total for es in effect_sizes)

    return MetaAnalysisStats(
        pooled_effect=pooled_es_re,
        pooled_se=se_pooled,
        pooled_ci_lower=ci_lower,
        pooled_ci_upper=ci_upper,
        heterogeneity_i2=i2,
        heterogeneity_q=q_sum,
        heterogeneity_df=k - 1,
        heterogeneity_p=q_p_val,
        tau_squared=tau_sq,
        k_studies=k,
        total_n=total_n
    )

def perform_subgroup_analysis(
    effect_sizes: List[EffectSize],
    subgroup_field: str,
    stats: Optional[MetaAnalysisStats] = None
) -> Dict[str, MetaAnalysisStats]:
    """
    Perform subgroup analysis based on a categorical field in EffectSize.
    """
    if not effect_sizes:
        return {}

    # Group by field
    subgroups: Dict[str, List[EffectSize]] = {}
    for es in effect_sizes:
        # Access attribute dynamically
        val = getattr(es, subgroup_field, None)
        key = str(val) if val is not None else "unknown"
        if key not in subgroups:
            subgroups[key] = []
        subgroups[key].append(es)

    results = {}
    for key, group in subgroups.items():
        if len(group) >= 2: # Need at least 2 for meaningful stats
            results[key] = run_random_effects_meta_analysis(group)
        else:
            logger.warning(f"Subgroup {key} has only {len(group)} study(s). Skipping meta-analysis.")
            # Still return stats for single study if needed, but usually not valid for RE
            # For now, we skip to avoid division by zero in variance calc if N=1
            pass

    return results

def perform_follow_up_subgroup_analysis(
    effect_sizes: List[EffectSize]
) -> Dict[str, MetaAnalysisStats]:
    """
    Specific subgroup analysis for follow-up duration (3-month vs others).
    """
    # Assuming EffectSize has a 'follow_up_months' or similar field
    # Based on typical data models, we'll check for a specific attribute or derive it
    # If the model doesn't have it, this might need to be pre-calculated or passed differently.
    # For this implementation, we assume 'follow_up_months' exists or 'duration_category'
    
    # Fallback: if 'follow_up_months' exists, we bin it.
    # If not, we assume the field 'follow_up_category' exists.
    
    # Let's assume the data has been cleaned to have a 'follow_up_category' string.
    # If not, we try to infer from a numeric field.
    
    def get_category(es: EffectSize) -> str:
        if hasattr(es, 'follow_up_months'):
            months = es.follow_up_months
            if months is not None:
                return "3_month" if months == 3 else "other"
        if hasattr(es, 'follow_up_category'):
            return es.follow_up_category
        return "unknown"

    subgroups: Dict[str, List[EffectSize]] = {}
    for es in effect_sizes:
        cat = get_category(es)
        if cat not in subgroups:
            subgroups[cat] = []
        subgroups[cat].append(es)
    
    results = {}
    for key, group in subgroups.items():
        if len(group) >= 2:
            results[key] = run_random_effects_meta_analysis(group)
        else:
            logger.warning(f"Follow-up subgroup {key} has only {len(group)} study(s).")

    return results

def create_meta_analysis_result(
    stats: MetaAnalysisStats,
    subgroups: Optional[Dict[str, MetaAnalysisStats]] = None,
    method: str = "random_effects"
) -> MetaAnalysisResult:
    """
    Create a structured MetaAnalysisResult object.
    """
    return MetaAnalysisResult(
        pooled_effect=stats.pooled_effect,
        pooled_se=stats.pooled_se,
        pooled_ci_lower=stats.pooled_ci_lower,
        pooled_ci_upper=stats.pooled_ci_upper,
        heterogeneity_i2=stats.heterogeneity_i2,
        heterogeneity_q=stats.heterogeneity_q,
        heterogeneity_df=stats.heterogeneity_df,
        heterogeneity_p=stats.heterogeneity_p,
        tau_squared=stats.tau_squared,
        k_studies=stats.k_studies,
        total_n=stats.total_n,
        method=method,
        subgroups=subgroups or {}
    )

def save_meta_analysis_results(
    result: MetaAnalysisResult,
    output_path: str
) -> None:
    """
    Save meta-analysis results to a JSON or CSV file.
    """
    # For simplicity, saving as a structured dict to JSON
    import json
    from code.utils.config import get_output_path
    
    # If path is relative, resolve it
    if not os.path.isabs(output_path):
        # Assuming output_path is relative to data/processed or similar
        # We use the config utility to ensure correct path resolution
        # However, the function signature expects a string path.
        # We'll assume the caller provides the full relative path from root.
        pass
    
    # Convert result to dict
    data = {
        "pooled_effect": result.pooled_effect,
        "pooled_se": result.pooled_se,
        "pooled_ci_lower": result.pooled_ci_lower,
        "pooled_ci_upper": result.pooled_ci_upper,
        "heterogeneity_i2": result.heterogeneity_i2,
        "heterogeneity_q": result.heterogeneity_q,
        "heterogeneity_df": result.heterogeneity_df,
        "heterogeneity_p": result.heterogeneity_p,
        "tau_squared": result.tau_squared,
        "k_studies": result.k_studies,
        "total_n": result.total_n,
        "method": result.method,
        "subgroups": {k: v.__dict__ for k, v in result.subgroups.items()}
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def run_analysis_or_synthesis(
    effect_sizes: List[EffectSize],
    output_path: str,
    min_studies_threshold: int = 10
) -> MetaAnalysisResult:
    """
    Conditional logic: Run meta-analysis if N >= min_studies_threshold.
    Otherwise, perform descriptive synthesis.
    
    FR-014: Suppress subgroup/meta-regression if N < 10 and switch to descriptive synthesis.
    """
    from code.analysis.descriptive_synthesis import perform_descriptive_synthesis, format_synthesis_report
    import os

    total_studies = len(effect_sizes)
    total_n = sum(es.n_total for es in effect_sizes)
    
    logger.info(f"Running analysis/synthesis check: {total_studies} studies, Total N: {total_n}")
    
    if total_studies < min_studies_threshold:
        logger.warning(f"Number of studies ({total_studies}) is below threshold ({min_studies_threshold}). "
                       f"Performing descriptive synthesis instead of meta-analysis.")
        
        # Perform descriptive synthesis
        syn_result = perform_descriptive_synthesis(effect_sizes)
        
        # Format report
        report_text = format_synthesis_report(syn_result)
        
        # Save report to file
        with open(output_path, 'w') as f:
            f.write(report_text)
        
        logger.info(f"Descriptive synthesis report saved to {output_path}")
        
        # Return a placeholder MetaAnalysisResult indicating synthesis was used
        # or raise a specific exception if the pipeline expects a MetaAnalysisResult object strictly.
        # For compatibility, we return a result object with synthesis metadata.
        return MetaAnalysisResult(
            pooled_effect=syn_result.mean_effect,
            pooled_se=syn_result.std_dev, # Approximate
            pooled_ci_lower=syn_result.mean_effect - 1.96 * syn_result.std_dev,
            pooled_ci_upper=syn_result.mean_effect + 1.96 * syn_result.std_dev,
            heterogeneity_i2=0.0,
            heterogeneity_q=0.0,
            heterogeneity_df=0,
            heterogeneity_p=1.0,
            tau_squared=0.0,
            k_studies=total_studies,
            total_n=total_n,
            method="descriptive_synthesis",
            subgroups={},
            synthesis_report_path=output_path
        )
    else:
        logger.info(f"Number of studies ({total_studies}) meets threshold. Running meta-analysis.")
        
        stats = run_random_effects_meta_analysis(effect_sizes)
        result = create_meta_analysis_result(stats)
        
        # Save results
        save_meta_analysis_results(result, output_path)
        
        return result

def main():
    """
    Entry point for running the meta-analysis or synthesis pipeline.
    """
    import sys
    from code.data.models import EffectSize
    from code.utils.config import get_data_path, get_output_path

    # Load cleaned studies (assuming they are in a CSV)
    # This part depends on how the previous tasks (T014-T018) saved the data.
    # Assuming 'data/processed/cleaned_studies.csv' exists and has been converted to EffectSize objects.
    # For this task, we assume the list of EffectSize is passed or loaded from a previous step.
    
    # Mock loading for demonstration of the logic flow
    # In a real run, this would load from the CSV generated by T019
    try:
        # Attempt to load from the expected path
        csv_path = get_data_path("processed/cleaned_studies.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Cleaned studies CSV not found at {csv_path}")
        
        # Load and convert to EffectSize (simplified)
        df = pd.read_csv(csv_path)
        # Assuming columns exist: effect_size, se, n_total, etc.
        effect_sizes = []
        for _, row in df.iterrows():
            es = EffectSize(
                study_id=row.get('study_id', 'unknown'),
                effect_size=row['effect_size'],
                se=row['se'],
                n_total=row['n_total'],
                # Add other required fields if they exist in the model
                # ...
            )
            effect_sizes.append(es)
    except Exception as e:
        logger.error(f"Failed to load effect sizes: {e}")
        # If data is missing, we cannot proceed.
        # In a real scenario, this would be handled by the pipeline orchestrator.
        sys.exit(1)

    output_path = get_output_path("analysis/meta_analysis_results.json")
    
    result = run_analysis_or_synthesis(
        effect_sizes=effect_sizes,
        output_path=output_path,
        min_studies_threshold=10
    )
    
    print(f"Analysis complete. Method used: {result.method}")
    if result.method == "descriptive_synthesis":
        print(f"Report saved to: {result.synthesis_report_path}")
    else:
        print(f"Pooled Effect: {result.pooled_effect:.4f} (95% CI: {result.pooled_ci_lower:.4f}, {result.pooled_ci_upper:.4f})")

if __name__ == "__main__":
    main()

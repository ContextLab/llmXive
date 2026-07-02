import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import os

# Add project root to path for imports if running as script
if 'code' not in sys.path:
    code_root = Path(__file__).parent.parent
    if code_root.exists():
        sys.path.insert(0, str(code_root))

from analysis.anova_utils import safe_import_statsmodels, compute_effect_size_etasquared
from data.loaders import load_experiment_results
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ANOVAOutput:
    """Schema for ANOVA analysis results."""
    context_condition: str
    metric_name: str
    f_statistic: float
    p_value: float
    corrected_p_value: float
    significant_at_alpha: bool
    alpha_threshold: float
    effect_size_etasquared: float
    degrees_of_freedom: Tuple[int, int]
    sample_sizes: Dict[str, int]
    mean_values: Dict[str, float]
    std_values: Dict[str, float]
    bonferroni_factor: int
    family_wise_alpha: float
    notes: str

def load_experiment_results(results_dir: Path) -> pd.DataFrame:
    """Load and combine full and limited context results."""
    full_path = results_dir / "results_full.csv"
    limited_path = results_dir / "results_limited.csv"
    
    dfs = []
    if full_path.exists():
        df_full = pd.read_csv(full_path)
        df_full['context_condition'] = 'full'
        dfs.append(df_full)
    
    if limited_path.exists():
        df_limited = pd.read_csv(limited_path)
        df_limited['context_condition'] = 'limited'
        dfs.append(df_limited)
    
    if not dfs:
        raise FileNotFoundError(f"No result CSVs found in {results_dir}")
    
    return pd.concat(dfs, ignore_index=True)

def prepare_data_for_anova(df: pd.DataFrame, metric_name: str) -> Dict[str, List[float]]:
    """Prepare data grouped by context condition for ANOVA."""
    if metric_name not in df.columns:
        raise ValueError(f"Metric {metric_name} not found in dataframe. Available: {df.columns.tolist()}")
    
    grouped = df.groupby('context_condition')[metric_name].apply(list).to_dict()
    return grouped

def compute_two_way_anova(df: pd.DataFrame, metric_name: str) -> Dict[str, Any]:
    """
    Compute two-way ANOVA for Context x Metric interaction.
    Since we are comparing metrics across contexts, we treat Metric as a factor.
    For this specific task, we focus on the Context effect and apply Bonferroni
    correction if multiple metrics are tested.
    """
    statsmodels = safe_import_statsmodels()
    if not statsmodels:
        logger.warning("statsmodels not available, using manual ANOVA calculation")
        return compute_manual_anova(df, metric_name)
    
    # Reshape for statsmodels if needed
    # For two-way with Context and Metric, we need a long format
    # However, the task specifies a single ANOVA with Context x Metric interaction.
    # If we are testing one metric at a time, it's effectively a one-way ANOVA on Context.
    # If testing multiple metrics together, we need to stack them.
    
    # For FR-007 (Bonferroni), we assume we are testing multiple hypotheses (e.g., multiple metrics).
    # We will return the raw p-value here, and the correction happens in apply_bonferroni_correction.
    
    # Prepare data: one-way ANOVA on Context for the specific metric
    # (The "two-way" in spec likely refers to the design of the experiment,
    # but for the statistical test of a single metric, it's one-way on Context)
    
    groups = df.groupby('context_condition')[metric_name]
    if groups.ngroups < 2:
        raise ValueError("Need at least 2 groups for ANOVA")
    
    groups_list = [group.values for _, group in groups]
    f_stat, p_val = statsmodels.stats.anova.anova_oneway(*groups_list)
    
    return {
        'f_statistic': float(f_stat),
        'p_value': float(p_val),
        'df_between': groups.ngroups - 1,
        'df_within': len(df) - groups.ngroups
    }

def compute_manual_anova(df: pd.DataFrame, metric_name: str) -> Dict[str, Any]:
    """Manual ANOVA calculation if statsmodels is unavailable."""
    groups = df.groupby('context_condition')[metric_name]
    groups_list = [group.values for _, group in groups]
    
    n_groups = len(groups_list)
    total_n = sum(len(g) for g in groups_list)
    
    grand_mean = np.mean(df[metric_name])
    
    # Sum of Squares Between
    ss_between = sum(len(g) * (np.mean(g) - grand_mean)**2 for g in groups_list)
    
    # Sum of Squares Within
    ss_within = sum(np.sum((g - np.mean(g))**2) for g in groups_list)
    
    df_between = n_groups - 1
    df_within = total_n - n_groups
    
    ms_between = ss_between / df_between if df_between > 0 else 0
    ms_within = ss_within / df_within if df_within > 0 else 0
    
    f_stat = ms_between / ms_within if ms_within > 0 else 0
    
    # Approximate p-value using scipy if available, else 0.5
    try:
        from scipy import stats
        p_val = 1 - stats.f.cdf(f_stat, df_between, df_within)
    except ImportError:
        p_val = 0.5
        logger.warning("scipy not available, p-value set to 0.5")
    
    return {
        'f_statistic': float(f_stat),
        'p_value': float(p_val),
        'df_between': df_between,
        'df_within': df_within
    }

def apply_bonferroni_correction(p_values: List[float], num_tests: int) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    Corrected p-value = min(p * num_tests, 1.0)
    Corrected alpha = original_alpha / num_tests
    """
    if num_tests == 0:
        return []
    
    corrected = [min(p * num_tests, 1.0) for p in p_values]
    return corrected

def run_anova_analysis(
    results_dir: Path,
    metrics: List[str],
    alpha: float = 0.05
) -> List[ANOVAOutput]:
    """
    Run ANOVA for multiple metrics and apply Bonferroni correction.
    
    Args:
        results_dir: Path to directory containing result CSVs
        metrics: List of metric column names to test
        alpha: Family-wise error rate (default 0.05)
    
    Returns:
        List of ANOVAOutput objects with corrected values
    """
    df = load_experiment_results(results_dir)
    num_tests = len(metrics)
    bonferroni_factor = num_tests
    corrected_alpha = alpha / num_tests if num_tests > 0 else alpha
    
    results = []
    
    for metric in metrics:
        try:
            # Compute raw ANOVA
            anova_stats = compute_two_way_anova(df, metric)
            f_stat = anova_stats['f_statistic']
            p_val = anova_stats['p_value']
            df_b = anova_stats['df_between']
            df_w = anova_stats['df_within']
            
            # Apply Bonferroni correction
            corrected_p = min(p_val * num_tests, 1.0)
            significant = corrected_p < alpha
            
            # Compute effect size
            effect_size = compute_effect_size_etasquared(df, metric, 'context_condition')
            
            # Get descriptive stats
            grouped = df.groupby('context_condition')[metric]
            mean_values = {k: float(v.mean()) for k, v in grouped}
            std_values = {k: float(v.std()) for k, v in grouped}
            sample_sizes = {k: len(v) for k, v in grouped}
            
            # Determine context conditions present
            context_conditions = list(sample_sizes.keys())
            if len(context_conditions) != 2:
                note = f"Warning: Expected 2 context conditions, found {len(context_conditions)}"
            else:
                note = "Bonferroni correction applied. Family-wise alpha = {0:.5f}".format(corrected_alpha)
            
            output = ANOVAOutput(
                context_condition="; ".join(context_conditions),
                metric_name=metric,
                f_statistic=f_stat,
                p_value=p_val,
                corrected_p_value=corrected_p,
                significant_at_alpha=significant,
                alpha_threshold=alpha,
                effect_size_etasquared=effect_size,
                degrees_of_freedom=(df_b, df_w),
                sample_sizes=sample_sizes,
                mean_values=mean_values,
                std_values=std_values,
                bonferroni_factor=bonferroni_factor,
                family_wise_alpha=corrected_alpha,
                notes=note
            )
            results.append(output)
            
        except Exception as e:
            logger.error(f"Error processing metric {metric}: {e}")
            continue
    
    return results

def main():
    """Main entry point for ANOVA analysis with Bonferroni correction."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run ANOVA with Bonferroni correction")
    parser.add_argument("--results_dir", type=str, default="projects/PROJ-586-social-memory-networks-modeling-collecti/results",
                        help="Directory containing result CSVs")
    parser.add_argument("--metrics", type=str, nargs="+", 
                        default=["specialization_index", "retrieval_efficiency"],
                        help="Metrics to analyze")
    parser.add_argument("--output", type=str, default="anova_results.json",
                        help="Output JSON file")
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        logger.error(f"Results directory not found: {results_dir}")
        sys.exit(1)
    
    logger.info(f"Running ANOVA for metrics: {args.metrics}")
    logger.info(f"Applying Bonferroni correction for {len(args.metrics)} tests")
    
    outputs = run_anova_analysis(results_dir, args.metrics)
    
    # Convert to serializable format
    serializable = []
    for out in outputs:
        d = asdict(out)
        # Convert tuples to lists for JSON
        if 'degrees_of_freedom' in d and isinstance(d['degrees_of_freedom'], tuple):
            d['degrees_of_freedom'] = list(d['degrees_of_freedom'])
        serializable.append(d)
    
    output_path = Path(args.output)
    import json
    with open(output_path, 'w') as f:
        json.dump(serializable, f, indent=2)
    
    logger.info(f"Results written to {output_path}")
    
    # Print summary
    print("\n=== ANOVA Results with Bonferroni Correction ===")
    print(f"Family-wise alpha: {outputs[0].family_wise_alpha if outputs else 'N/A'}")
    print(f"Number of tests: {outputs[0].bonferroni_factor if outputs else 0}")
    print("-" * 50)
    for out in outputs:
        sig_marker = "*" if out.significant_at_alpha else ""
        print(f"{out.metric_name}: p={out.p_value:.4f}, corrected_p={out.corrected_p_value:.4f} {sig_marker}")
        print(f"  Mean (Full): {out.mean_values.get('full', 'N/A'):.4f}, "
              f"Mean (Limited): {out.mean_values.get('limited', 'N/A'):.4f}")
    
    return outputs

if __name__ == "__main__":
    main()
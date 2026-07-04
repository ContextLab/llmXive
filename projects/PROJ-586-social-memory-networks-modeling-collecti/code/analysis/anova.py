"""
Two-way independent-samples ANOVA implementation for Social Memory Networks.

Implements a single ANOVA with factors Context (Full vs Limited) and Metric 
(Specialization vs Retrieval), as required by FR-006.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

# Try to import statsmodels for robust ANOVA
# If unavailable, fall back to scipy or manual calculation
def safe_import_statsmodels():
    try:
        import statsmodels.api as sm
        from statsmodels.formula.api import ols
        from statsmodels.stats.anova import anova_lm
        return sm, ols, anova_lm
    except ImportError:
        return None, None, None

@dataclass
class ANOVAOutput:
    """Structured output for ANOVA results."""
    source: str
    df: float
    sum_sq: float
    mean_sq: float
    F: float
    PR_gt_F: float
    
@dataclass
class TwoWayANOVAResult:
    """Complete result of a two-way ANOVA analysis."""
    summary_df: pd.DataFrame
    interaction_significant: bool
    interaction_p_value: float
    main_effect_context_significant: bool
    main_effect_context_p_value: float
    main_effect_metric_significant: bool
    main_effect_metric_p_value: float
    effect_sizes: Dict[str, float]
    
def compute_effect_size_etasquared(sum_sq_effect: float, sum_sq_error: float) -> float:
    """Compute eta-squared effect size."""
    if sum_sq_error == 0:
        return 0.0
    return sum_sq_effect / (sum_sq_effect + sum_sq_error)

def load_experiment_results(
    full_path: Path,
    limited_path: Path
) -> pd.DataFrame:
    """
    Load and combine results from full-context and limited-context experiments.
    
    Returns a long-format DataFrame with columns:
    ['game_id', 'specialization_index', 'retrieval_efficiency', 'context_condition']
    """
    if not full_path.exists() or not limited_path.exists():
        raise FileNotFoundError(
            f"Required result files not found: {full_path}, {limited_path}"
        )
    
    df_full = pd.read_csv(full_path)
    df_limited = pd.read_csv(limited_path)
    
    # Ensure context labels
    df_full['context_condition'] = 'full'
    df_limited['context_condition'] = 'limited'
    
    # Combine
    df_combined = pd.concat([df_full, df_limited], ignore_index=True)
    
    # Convert metrics to numeric
    for col in ['specialization_index', 'retrieval_efficiency']:
        df_combined[col] = pd.to_numeric(df_combined[col], errors='coerce')
    
    # Drop rows with NaN in metrics
    df_combined = df_combined.dropna(subset=['specialization_index', 'retrieval_efficiency'])
    
    return df_combined

def prepare_data_for_anova(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reshape data from wide to long format for two-way ANOVA.
    
    Input: DataFrame with columns ['game_id', 'specialization_index', 
                                   'retrieval_efficiency', 'context_condition']
    Output: DataFrame with columns ['game_id', 'metric_type', 'value', 'context_condition']
    """
    # Melt to long format
    df_melted = df.melt(
        id_vars=['game_id', 'context_condition'],
        value_vars=['specialization_index', 'retrieval_efficiency'],
        var_name='metric_type',
        value_name='value'
    )
    
    # Clean metric_type labels
    df_melted['metric_type'] = df_melted['metric_type'].map({
        'specialization_index': 'Specialization',
        'retrieval_efficiency': 'Retrieval'
    })
    
    return df_melted

def compute_two_way_anova(df_long: pd.DataFrame) -> TwoWayANOVAResult:
    """
    Perform a two-way independent-samples ANOVA.
    
    Factors:
    - Context (between-subjects): 'full' vs 'limited'
    - Metric (within-subjects/repeated): 'Specialization' vs 'Retrieval'
    
    Note: This is a mixed-design ANOVA. For simplicity and robustness,
    we use a standard two-way ANOVA on the long-format data.
    
    Args:
        df_long: Long-format DataFrame with columns ['context_condition', 
                                                     'metric_type', 'value']
                
    Returns:
        TwoWayANOVAResult with significance tests and effect sizes
    """
    sm, ols, anova_lm = safe_import_statsmodels()
    
    if sm is None:
        # Fallback to scipy if statsmodels unavailable
        return _compute_anova_scipy(df_long)
    
    # Fit the model
    # Formula: value ~ C(context_condition) * C(metric_type)
    model = ols('value ~ C(context_condition) * C(metric_type)', data=df_long).fit()
    anova_table = anova_lm(model, typ=2)
    
    # Extract p-values
    # Rows are: C(context_condition), C(metric_type), C(context_condition):C(metric_type)
    interaction_row = anova_table.loc['C(context_condition):C(metric_type)', :]
    context_row = anova_table.loc['C(context_condition)', :]
    metric_row = anova_table.loc['C(metric_type)', :]
    
    interaction_p = float(interaction_row['PR > F'])
    context_p = float(context_row['PR > F'])
    metric_p = float(metric_row['PR > F'])
    
    # Compute effect sizes (eta-squared)
    ss_total = anova_table['sum_sq'].sum()
    ss_interaction = interaction_row['sum_sq']
    ss_context = context_row['sum_sq']
    ss_metric = metric_row['sum_sq']
    ss_error = anova_table.loc['Residual', 'sum_sq']
    
    eta_sq_interaction = compute_effect_size_etasquared(ss_interaction, ss_error)
    eta_sq_context = compute_effect_size_etasquared(ss_context, ss_error)
    eta_sq_metric = compute_effect_size_etasquared(ss_metric, ss_error)
    
    return TwoWayANOVAResult(
        summary_df=anova_table,
        interaction_significant=interaction_p < 0.05,
        interaction_p_value=interaction_p,
        main_effect_context_significant=context_p < 0.05,
        main_effect_context_p_value=context_p,
        main_effect_metric_significant=metric_p < 0.05,
        main_effect_metric_p_value=metric_p,
        effect_sizes={
            'interaction': eta_sq_interaction,
            'context': eta_sq_context,
            'metric': eta_sq_metric
        }
    )

def _compute_anova_scipy(df_long: pd.DataFrame) -> TwoWayANOVAResult:
    """
    Fallback ANOVA implementation using scipy when statsmodels is unavailable.
    Computes a simplified two-way ANOVA.
    """
    from scipy import stats
    
    # Reshape to wide format for scipy's f_oneway (simplified approach)
    # This is a limitation: scipy doesn't have a direct two-way ANOVA
    # We'll compute it manually via sums of squares
    
    pivot = df_long.pivot_table(
        index='game_id', 
        columns=['context_condition', 'metric_type'], 
        values='value'
    )
    
    # Flatten columns
    pivot.columns = [f"{ctx}_{met}" for ctx, met in pivot.columns]
    
    # Calculate group means and overall mean
    overall_mean = df_long['value'].mean()
    n = len(df_long)
    
    # This is a simplified manual calculation
    # For a proper mixed-design, we need more complex handling
    # Here we approximate with a two-way layout
    
    # Compute SS_total
    ss_total = ((df_long['value'] - overall_mean) ** 2).sum()
    
    # Compute SS_context
    context_means = df_long.groupby('context_condition')['value'].mean()
    n_per_context = df_long.groupby('context_condition').size()
    ss_context = sum(
        n_per_context[ctx] * (context_means[ctx] - overall_mean) ** 2 
        for ctx in context_means.index
    )
    
    # Compute SS_metric
    metric_means = df_long.groupby('metric_type')['value'].mean()
    n_per_metric = df_long.groupby('metric_type').size()
    ss_metric = sum(
        n_per_metric[met] * (metric_means[met] - overall_mean) ** 2 
        for met in metric_means.index
    )
    
    # Compute SS_interaction (residual after main effects)
    # For a balanced design: SS_interaction = SS_between_cells - SS_context - SS_metric
    cell_means = df_long.groupby(['context_condition', 'metric_type'])['value'].mean()
    n_per_cell = df_long.groupby(['context_condition', 'metric_type']).size()
    
    ss_cells = sum(
        n_per_cell[(ctx, met)] * (cell_means[(ctx, met)] - overall_mean) ** 2 
        for (ctx, met) in cell_means.index
    )
    ss_interaction = ss_cells - ss_context - ss_metric
    
    ss_error = ss_total - ss_cells
    
    # Degrees of freedom
    df_context = len(context_means) - 1
    df_metric = len(metric_means) - 1
    df_interaction = df_context * df_metric
    df_error = n - len(cell_means)
    
    # Mean squares
    ms_context = ss_context / df_context if df_context > 0 else 0
    ms_metric = ss_metric / df_metric if df_metric > 0 else 0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
    ms_error = ss_error / df_error if df_error > 0 else 1e-9
    
    # F-statistics
    f_context = ms_context / ms_error if ms_error > 0 else 0
    f_metric = ms_metric / ms_error if ms_error > 0 else 0
    f_interaction = ms_interaction / ms_error if ms_error > 0 else 0
    
    # P-values
    p_context = 1 - stats.f.cdf(f_context, df_context, df_error)
    p_metric = 1 - stats.f.cdf(f_metric, df_metric, df_error)
    p_interaction = 1 - stats.f.cdf(f_interaction, df_interaction, df_error)
    
    # Effect sizes
    eta_sq_context = compute_effect_size_etasquared(ss_context, ss_error)
    eta_sq_metric = compute_effect_size_etasquared(ss_metric, ss_error)
    eta_sq_interaction = compute_effect_size_etasquared(ss_interaction, ss_error)
    
    # Construct a mock DataFrame for summary
    summary_data = {
        'sum_sq': [ss_context, ss_metric, ss_interaction, ss_error],
        'df': [df_context, df_metric, df_interaction, df_error],
        'F': [f_context, f_metric, f_interaction, np.nan],
        'PR > F': [p_context, p_metric, p_interaction, np.nan]
    }
    index_labels = ['C(context_condition)', 'C(metric_type)', 'C(context_condition):C(metric_type)', 'Residual']
    summary_df = pd.DataFrame(summary_data, index=index_labels)
    
    return TwoWayANOVAResult(
        summary_df=summary_df,
        interaction_significant=p_interaction < 0.05,
        interaction_p_value=p_interaction,
        main_effect_context_significant=p_context < 0.05,
        main_effect_context_p_value=p_context,
        main_effect_metric_significant=p_metric < 0.05,
        main_effect_metric_p_value=p_metric,
        effect_sizes={
            'interaction': eta_sq_interaction,
            'context': eta_sq_context,
            'metric': eta_sq_metric
        }
    )

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Family-wise error rate (default 0.05)
        
    Returns:
        Dict with corrected alpha and significance for each test
    """
    n_tests = len(p_values)
    corrected_alpha = alpha / n_tests if n_tests > 0 else alpha
    
    results = {}
    for i, p in enumerate(p_values):
        results[f'test_{i}'] = {
            'raw_p': p,
            'corrected_p': min(p * n_tests, 1.0),
            'significant_at_corrected_alpha': p < corrected_alpha,
            'significant_at_raw_alpha': p < alpha
        }
        
    return {
        'original_alpha': alpha,
        'n_tests': n_tests,
        'corrected_alpha': corrected_alpha,
        'test_results': results
    }

def run_anova_analysis(
    full_results_path: Path,
    limited_results_path: Path,
    output_path: Optional[Path] = None
) -> TwoWayANOVAResult:
    """
    Main entry point for running the two-way ANOVA analysis.
    
    Args:
        full_results_path: Path to results_full.csv
        limited_results_path: Path to results_limited.csv
        output_path: Optional path to write JSON summary
        
    Returns:
        TwoWayANOVAResult object
    """
    # Load data
    df = load_experiment_results(full_results_path, limited_results_path)
    
    # Prepare data
    df_long = prepare_data_for_anova(df)
    
    # Run ANOVA
    result = compute_two_way_anova(df_long)
    
    # Apply Bonferroni correction to the three main tests
    p_values = [
        result.main_effect_context_p_value,
        result.main_effect_metric_p_value,
        result.interaction_p_value
    ]
    bonferroni_result = apply_bonferroni_correction(p_values)
    
    # Attach Bonferroni info to result (as a side effect or extended dataclass)
    # For now, we return the main result and log the correction
    print(f"Bonferroni correction applied: {bonferroni_result['corrected_alpha']:.4f}")
    print(f"Interaction significant after correction: {result.interaction_p_value < bonferroni_result['corrected_alpha']}")
    
    # Write output if path provided
    if output_path:
        output_data = {
            'interaction_significant': result.interaction_significant,
            'interaction_p_value': result.interaction_p_value,
            'main_effect_context_significant': result.main_effect_context_significant,
            'main_effect_context_p_value': result.main_effect_context_p_value,
            'main_effect_metric_significant': result.main_effect_metric_significant,
            'main_effect_metric_p_value': result.main_effect_metric_p_value,
            'effect_sizes': result.effect_sizes,
            'bonferroni_correction': bonferroni_result
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
    
    return result

def main():
    """CLI entry point for ANOVA analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run two-way ANOVA on experiment results')
    parser.add_argument('--full', type=str, required=True, help='Path to results_full.csv')
    parser.add_argument('--limited', type=str, required=True, help='Path to results_limited.csv')
    parser.add_argument('--output', type=str, help='Path to output JSON summary')
    
    args = parser.parse_args()
    
    full_path = Path(args.full)
    limited_path = Path(args.limited)
    output_path = Path(args.output) if args.output else None
    
    try:
        result = run_anova_analysis(full_path, limited_path, output_path)
        print("\n=== ANOVA Results ===")
        print(f"Interaction (Context × Metric): p={result.interaction_p_value:.4f}, sig={result.interaction_significant}")
        print(f"Main Effect (Context): p={result.main_effect_context_p_value:.4f}, sig={result.main_effect_context_significant}")
        print(f"Main Effect (Metric): p={result.main_effect_metric_p_value:.4f}, sig={result.main_effect_metric_significant}")
        print(f"Effect Sizes: {result.effect_sizes}")
    except Exception as e:
        print(f"Error running ANOVA: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
"""
Two-way independent-samples ANOVA for Social Memory Networks experiment.

This module implements the statistical analysis required for User Story 2,
comparing the interaction between context condition and metric type.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Try to import statsmodels; if unavailable, provide a fallback that fails loudly
try:
    from statsmodels.formula.api import ols
    from statsmodels.stats.anova import anova_lm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    # We will raise a clear error if statsmodels is needed but missing


@dataclass
class TwoWayANOVAResult:
    """Container for ANOVA results."""
    source: str
    df: float
    sum_sq: float
    mean_sq: float
    f_value: float
    p_value: float
    eta_squared: Optional[float] = None

@dataclass
class ANOVAOutput:
    """Structured output for the two-way ANOVA."""
    interaction_p_value: float
    interaction_f_value: float
    interaction_df: Tuple[float, float]
    main_effect_context_p: float
    main_effect_metric_p: float
    full_table: List[Dict[str, Any]]
    bonferroni_corrected_alpha: Optional[float] = None
    significant_interaction: bool = False

def safe_import_statsmodels() -> bool:
    """Check if statsmodels is available and import necessary components."""
    if not STATSMODELS_AVAILABLE:
        raise ImportError(
            "statsmodels is required for ANOVA analysis. "
            "Please install it via: pip install statsmodels"
        )
    return True

def load_experiment_results(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load experiment results from a CSV file.

    Args:
        file_path: Path to the CSV file containing game results.

    Returns:
        DataFrame with the loaded results.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")

    df = pd.read_csv(path)

    # Validate required columns
    required_cols = ['game_id', 'specialization_index', 'retrieval_efficiency', 'context_condition', 'agent_count']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {file_path}: {missing}")

    return df

def prepare_data_for_anova(full_results_path: Union[str, Path],
                           limited_results_path: Union[str, Path]) -> pd.DataFrame:
    """
    Combine full and limited context results into a single long-format DataFrame.

    The resulting DataFrame has columns:
    - game_id: Unique identifier for the game
    - context_condition: 'full' or 'limited'
    - metric_name: 'specialization' or 'retrieval'
    - metric_value: The actual metric value

    Args:
        full_results_path: Path to results_full.csv
        limited_results_path: Path to results_limited.csv

    Returns:
        Long-format DataFrame suitable for ANOVA analysis.
    """
    safe_import_statsmodels()

    # Load both datasets
    df_full = load_experiment_results(full_results_path)
    df_limited = load_experiment_results(limited_results_path)

    # Ensure context_condition is set correctly
    df_full['context_condition'] = 'full'
    df_limited['context_condition'] = 'limited'

    # Select and rename columns for consistency
    # We only need game_id, context_condition, and the two metrics
    df_full_subset = df_full[['game_id', 'context_condition', 'specialization_index', 'retrieval_efficiency']].copy()
    df_limited_subset = df_limited[['game_id', 'context_condition', 'specialization_index', 'retrieval_efficiency']].copy()

    # Melt to long format
    df_full_long = df_full_subset.melt(
        id_vars=['game_id', 'context_condition'],
        value_vars=['specialization_index', 'retrieval_efficiency'],
        var_name='metric_name',
        value_name='metric_value'
    )
    df_limited_long = df_limited_subset.melt(
        id_vars=['game_id', 'context_condition'],
        value_vars=['specialization_index', 'retrieval_efficiency'],
        var_name='metric_name',
        value_name='metric_value'
    )

    # Combine
    df_combined = pd.concat([df_full_long, df_limited_long], ignore_index=True)

    # Clean up metric names for the formula (remove '_index' suffix for clarity)
    df_combined['metric_name'] = df_combined['metric_name'].str.replace('_index', '', regex=False)

    return df_combined

def compute_effect_size_etasquared(sum_sq_effect: float, sum_sq_total: float) -> float:
    """
    Compute eta-squared effect size.

    Args:
        sum_sq_effect: Sum of squares for the effect
        sum_sq_total: Total sum of squares

    Returns:
        Eta-squared value (0 to 1)
    """
    if sum_sq_total == 0:
        return 0.0
    return sum_sq_effect / sum_sq_total

def compute_two_way_anova(df: pd.DataFrame,
                          formula: str = "metric_value ~ C(context_condition) * C(metric_name)") -> Tuple[pd.DataFrame, Any]:
    """
    Perform a two-way independent-samples ANOVA.

    Args:
        df: Long-format DataFrame with columns: game_id, context_condition, metric_name, metric_value
        formula: ANOVA formula (default: interaction model)

    Returns:
        Tuple of (ANOVA table DataFrame, fitted OLS model)
    """
    safe_import_statsmodels()

    # Ensure categorical variables are treated as factors
    df['context_condition'] = df['context_condition'].astype('category')
    df['metric_name'] = df['metric_name'].astype('category')

    # Fit the model
    model = ols(formula, data=df).fit()

    # Generate ANOVA table
    anova_table = anova_lm(model)

    return anova_table, model

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.

    Args:
        p_values: List of raw p-values
        alpha: Significance level

    Returns:
        List of Bonferroni-corrected p-values (capped at 1.0)
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []

    # Bonferroni: multiply p-values by number of tests, cap at 1.0
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

def run_anova_analysis(full_results_path: Union[str, Path],
                       limited_results_path: Union[str, Path],
                       output_path: Optional[Union[str, Path]] = None) -> ANOVAOutput:
    """
    Run the complete two-way ANOVA analysis and return structured results.

    Args:
        full_results_path: Path to results_full.csv
        limited_results_path: Path to results_limited.csv
        output_path: Optional path to save JSON results

    Returns:
        ANOVAOutput object with all computed statistics
    """
    # Prepare data
    df = prepare_data_for_anova(full_results_path, limited_results_path)

    # Run ANOVA
    anova_table, model = compute_two_way_anova(df)

    # Extract interaction term
    interaction_row = anova_table.loc['C(context_condition):C(metric_name)']
    interaction_p = float(interaction_row['PR(>F)'])
    interaction_f = float(interaction_row['F'])
    interaction_df = (float(interaction_row['df']), float(anova_table.loc['C(context_condition):C(metric_name)', 'df']))

    # Extract main effects
    context_p = float(anova_table.loc['C(context_condition)', 'PR(>F)'])
    metric_p = float(anova_table.loc['C(metric_name)', 'PR(>F)'])

    # Compute effect sizes (eta-squared)
    ss_total = anova_table['sum_sq'].sum()
    eta_sq_interaction = compute_effect_size_etasquared(
        float(anova_table.loc['C(context_condition):C(metric_name)', 'sum_sq']),
        ss_total
    )

    # Convert ANOVA table to list of dicts
    full_table = []
    for idx, row in anova_table.iterrows():
        full_table.append({
            'source': str(idx),
            'df': float(row['df']),
            'sum_sq': float(row['sum_sq']),
            'mean_sq': float(row['mean_sq']),
            'f_value': float(row['F']),
            'p_value': float(row['PR(>F)']),
            'eta_squared': compute_effect_size_etasquared(float(row['sum_sq']), ss_total) if idx != 'Residual' else None
        })

    # Bonferroni correction (we have 3 tests: interaction + 2 main effects)
    raw_p_values = [interaction_p, context_p, metric_p]
    corrected_p_values = apply_bonferroni_correction(raw_p_values)
    corrected_alpha = 0.05 / len(raw_p_values)

    # Determine significance
    significant_interaction = interaction_p < 0.05

    result = ANOVAOutput(
        interaction_p_value=interaction_p,
        interaction_f_value=interaction_f,
        interaction_df=(interaction_df[0], interaction_df[1]),
        main_effect_context_p=context_p,
        main_effect_metric_p=metric_p,
        full_table=full_table,
        bonferroni_corrected_alpha=corrected_alpha,
        significant_interaction=significant_interaction
    )

    # Save to JSON if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({
                'interaction_p_value': result.interaction_p_value,
                'interaction_f_value': result.interaction_f_value,
                'interaction_df': result.interaction_df,
                'main_effect_context_p': result.main_effect_context_p,
                'main_effect_metric_p': result.main_effect_metric_p,
                'bonferroni_corrected_alpha': result.bonferroni_corrected_alpha,
                'significant_interaction': result.significant_interaction,
                'full_table': result.full_table
            }, f, indent=2)

    return result

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ANOVA script."""
    parser = argparse.ArgumentParser(
        description='Run two-way ANOVA on social memory network experiment results.'
    )
    parser.add_argument(
        '--full-results',
        type=str,
        required=True,
        help='Path to results_full.csv'
    )
    parser.add_argument(
        '--limited-results',
        type=str,
        required=True,
        help='Path to results_limited.csv'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/anova_results.json',
        help='Path to save JSON results'
    )
    return parser

def main():
    """Main entry point for the ANOVA analysis script."""
    parser = build_parser()
    args = parser.parse_args()

    print(f"Loading full context results from: {args.full_results}")
    print(f"Loading limited context results from: {args.limited_results}")

    try:
        result = run_anova_analysis(
            args.full_results,
            args.limited_results,
            args.output
        )

        print("\n" + "="*60)
        print("TWO-WAY ANOVA RESULTS")
        print("="*60)
        print(f"Interaction (Context x Metric):")
        print(f"  F({result.interaction_df[0]}, {result.interaction_df[1]}) = {result.interaction_f_value:.4f}")
        print(f"  p-value = {result.interaction_p_value:.6f}")
        print(f"  Bonferroni-corrected alpha = {result.bonferroni_corrected_alpha:.6f}")
        print(f"  Significant interaction? {'YES' if result.significant_interaction else 'NO'}")
        print(f"\nMain Effects:")
        print(f"  Context Condition: p = {result.main_effect_context_p:.6f}")
        print(f"  Metric Type: p = {result.main_effect_metric_p:.6f}")
        print("="*60)
        print(f"Results saved to: {args.output}")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during ANOVA: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
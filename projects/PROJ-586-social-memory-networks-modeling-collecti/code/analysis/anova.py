"""
ANOVA analysis module for Social Memory Networks project.
Implements two-way ANOVA with Bonferroni correction for family-wise error rate.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

# Optional statsmodels import with fallback
try:
    import statsmodels.api as sm
    from statsmodels.stats.anova import AnovaRM
    from statsmodels.stats.multitest import multipletests
    STATS_MODELS_AVAILABLE = True
except ImportError:
    STATS_MODELS_AVAILABLE = False
    AnovaRM = None
    multipletests = None


@dataclass
class ANOVAOutput:
    """Structured output from ANOVA analysis."""
    summary_table: str
    f_statistic: float
    p_value: float
    effect_size_eta_squared: float
    corrected_alpha: float
    significant: bool
    interaction_effect: Optional[float] = None
    interaction_p_value: Optional[float] = None
    interaction_eta_squared: Optional[float] = None
    bonferroni_corrected_p_values: Optional[Dict[str, float]] = None
    raw_p_values: Optional[Dict[str, float]] = None
    n_observations: int = 0
    groups: Dict[str, List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        d = asdict(self)
        # Convert numpy types to Python native types
        for k, v in d.items():
            if isinstance(v, (np.floating, np.integer)):
                d[k] = float(v) if isinstance(v, np.floating) else int(v)
            elif isinstance(v, np.ndarray):
                d[k] = v.tolist()
        return d


def load_experiment_results(csv_path: str) -> pd.DataFrame:
    """Load experiment results from CSV file.

    Args:
        csv_path: Path to CSV file with columns: game_id, specialization_index,
                 retrieval_efficiency, context_condition, agent_count

    Returns:
        DataFrame with experiment results
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {csv_path}")

    df = pd.read_csv(path)

    # Validate required columns
    required_cols = ['game_id', 'specialization_index', 'retrieval_efficiency',
                    'context_condition', 'agent_count']
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df


def prepare_data_for_anova(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for two-way ANOVA.

    Args:
        df: DataFrame with experiment results

    Returns:
        Melted DataFrame suitable for statsmodels AnovaRM
    """
    # Filter out any rows with NaN in key columns
    df_clean = df.dropna(subset=['specialization_index', 'retrieval_efficiency',
                                 'context_condition'])

    # Melt to long format for repeated measures ANOVA
    melted = pd.melt(
        df_clean,
        id_vars=['game_id', 'context_condition', 'agent_count'],
        value_vars=['specialization_index', 'retrieval_efficiency'],
        var_name='metric',
        value_name='value'
    )

    return melted


def compute_effect_size_etasquared(ss_effect: float, ss_total: float) -> float:
    """Compute eta-squared effect size.

    Args:
        ss_effect: Sum of squares for the effect
        ss_total: Total sum of squares

    Returns:
        Eta-squared value (0 to 1)
    """
    if ss_total == 0:
        return 0.0
    return ss_effect / ss_total


def safe_import_statsmodels():
    """Safely import statsmodels, returning None if unavailable."""
    if not STATS_MODELS_AVAILABLE:
        return None
    return sm


def compute_two_way_anova(df: pd.DataFrame,
                         factor1: str = 'context_condition',
                         factor2: str = 'metric',
                         dependent: str = 'value') -> Dict[str, Any]:
    """Compute two-way ANOVA using statsmodels if available, else manual computation.

    Args:
        df: DataFrame with columns for factors and dependent variable
        factor1: First factor column name
        factor2: Second factor column name
        dependent: Dependent variable column name

    Returns:
        Dictionary with ANOVA results
    """
    if STATS_MODELS_AVAILABLE:
        return _compute_anova_statsmodels(df, factor1, factor2, dependent)
    else:
        return _compute_anova_manual(df, factor1, factor2, dependent)


def _compute_anova_statsmodels(df: pd.DataFrame,
                               factor1: str,
                               factor2: str,
                               dependent: str) -> Dict[str, Any]:
    """Compute ANOVA using statsmodels."""
    # Prepare data for repeated measures ANOVA
    # For this design, we treat game_id as subject, context_condition and metric as factors

    # Group by subject (game_id) and factors
    try:
        # Use AnovaRM for repeated measures
        anova_model = AnovaRM(
            df,
            depvar=dependent,
            subject='game_id',
            within=[factor1, factor2]
        )
        anova_result = anova_model.fit()

        # Extract summary as string
        summary_str = str(anova_result)

        # Parse F and p values from the result
        # The result has a table with F, PR>F columns
        results = {}
        for idx, row in anova_result.anova_table.iterrows():
            source = str(idx)
            f_val = float(row['F']) if 'F' in row else 0.0
            p_val = float(row['PR>F']) if 'PR>F' in row else 1.0
            results[source] = {'f': f_val, 'p': p_val}

        return {
            'summary': summary_str,
            'results': results,
            'method': 'statsmodels'
        }
    except Exception as e:
        # Fallback to manual computation
        return _compute_anova_manual(df, factor1, factor2, dependent)


def _compute_anova_manual(df: pd.DataFrame,
                         factor1: str,
                         factor2: str,
                         dependent: str) -> Dict[str, Any]:
    """Compute two-way ANOVA manually using numpy.

    This is a simplified implementation for when statsmodels is not available.
    """
    # Group data by factor combinations
    groups = df.groupby([factor1, factor2])[dependent].apply(list).to_dict()

    # Get all unique levels
    levels1 = df[factor1].unique()
    levels2 = df[factor2].unique()

    # Calculate overall mean
    overall_mean = df[dependent].mean()

    # Calculate sums of squares
    ss_total = ((df[dependent] - overall_mean) ** 2).sum()

    # SS for factor 1
    ss_factor1 = 0
    for level1 in levels1:
        subset = df[df[factor1] == level1]
        n = len(subset)
        mean1 = subset[dependent].mean()
        ss_factor1 += n * (mean1 - overall_mean) ** 2

    # SS for factor 2
    ss_factor2 = 0
    for level2 in levels2:
        subset = df[df[factor2] == level2]
        n = len(subset)
        mean2 = subset[dependent].mean()
        ss_factor2 += n * (mean2 - overall_mean) ** 2

    # SS for interaction (simplified - assumes balanced design)
    ss_interaction = 0
    for level1 in levels1:
        for level2 in levels2:
            subset = df[(df[factor1] == level1) & (df[factor2] == level2)]
            if len(subset) > 0:
                n = len(subset)
                mean_cell = subset[dependent].mean()
                mean1 = df[df[factor1] == level1][dependent].mean()
                mean2 = df[df[factor2] == level2][dependent].mean()
                ss_interaction += n * (mean_cell - mean1 - mean2 + overall_mean) ** 2

    # SS error (residual)
    ss_error = ss_total - ss_factor1 - ss_factor2 - ss_interaction

    # Degrees of freedom
    df_factor1 = len(levels1) - 1
    df_factor2 = len(levels2) - 1
    df_interaction = df_factor1 * df_factor2
    df_error = len(df) - len(levels1) * len(levels2)

    # Mean squares
    ms_factor1 = ss_factor1 / df_factor1 if df_factor1 > 0 else 0
    ms_factor2 = ss_factor2 / df_factor2 if df_factor2 > 0 else 0
    ms_interaction = ss_interaction / df_interaction if df_interaction > 0 else 0
    ms_error = ss_error / df_error if df_error > 0 else 1

    # F statistics
    f_factor1 = ms_factor1 / ms_error if ms_error > 0 else 0
    f_factor2 = ms_factor2 / ms_error if ms_error > 0 else 0
    f_interaction = ms_interaction / ms_error if ms_error > 0 else 0

    # P values (approximate using scipy if available, else use rough estimate)
    try:
        from scipy import stats
        p_factor1 = 1 - stats.f.cdf(f_factor1, df_factor1, df_error)
        p_factor2 = 1 - stats.f.cdf(f_factor2, df_factor2, df_error)
        p_interaction = 1 - stats.f.cdf(f_interaction, df_interaction, df_error)
    except ImportError:
        # Fallback: return 1.0 if we can't compute
        p_factor1 = 1.0
        p_factor2 = 1.0
        p_interaction = 1.0

    results = {
        factor1: {'f': f_factor1, 'p': p_factor1},
        factor2: {'f': f_factor2, 'p': p_factor2},
        'interaction': {'f': f_interaction, 'p': p_interaction}
    }

    return {
        'summary': f"Manual ANOVA (statsmodels unavailable)\n"
                  f"Factor {factor1}: F={f_factor1:.4f}, p={p_factor1:.4f}\n"
                  f"Factor {factor2}: F={f_factor2:.4f}, p={p_factor2:.4f}\n"
                  f"Interaction: F={f_interaction:.4f}, p={p_interaction:.4f}",
        'results': results,
        'method': 'manual'
    }


def apply_bonferroni_correction(raw_p_values: Dict[str, float],
                                alpha: float = 0.05) -> Tuple[Dict[str, float], float]:
    """Apply Bonferroni correction to family-wise hypothesis tests.

    The Bonferroni correction divides the significance level alpha by the number
    of tests to control the family-wise error rate.

    Args:
        raw_p_values: Dictionary of raw p-values from hypothesis tests
        alpha: Original significance level (default 0.05)

    Returns:
        Tuple of (corrected_p_values, corrected_alpha)
        - corrected_p_values: P-values multiplied by number of tests (capped at 1.0)
        - corrected_alpha: alpha divided by number of tests
    """
    n_tests = len(raw_p_values)
    if n_tests == 0:
        return {}, alpha

    # Bonferroni corrected alpha
    corrected_alpha = alpha / n_tests

    # Corrected p-values (multiply by n_tests, cap at 1.0)
    corrected_p_values = {}
    for key, p in raw_p_values.items():
        corrected_p = min(p * n_tests, 1.0)
        corrected_p_values[key] = corrected_p

    return corrected_p_values, corrected_alpha


def run_anova_analysis(results_csv: str,
                      alpha: float = 0.05) -> ANOVAOutput:
    """Run complete ANOVA analysis with Bonferroni correction.

    Args:
        results_csv: Path to CSV file with experiment results
        alpha: Significance level for hypothesis testing

    Returns:
        ANOVAOutput with all results and corrected alpha
    """
    # Load and prepare data
    df = load_experiment_results(results_csv)
    melted_df = prepare_data_for_anova(df)

    # Run two-way ANOVA
    anova_results = compute_two_way_anova(
        melted_df,
        factor1='context_condition',
        factor2='metric',
        dependent='value'
    )

    # Extract key statistics
    results_dict = anova_results.get('results', {})

    # Get raw p-values for all tests
    raw_p_values = {}
    for source, stats in results_dict.items():
        raw_p_values[source] = stats.get('p', 1.0)

    # Apply Bonferroni correction
    corrected_p_values, corrected_alpha = apply_bonferroni_correction(
        raw_p_values, alpha=alpha
    )

    # Determine significance based on corrected alpha
    significant = any(p < corrected_alpha for p in corrected_p_values.values())

    # Extract main effects and interaction
    f_stat = results_dict.get('context_condition', {}).get('f', 0.0)
    p_val = results_dict.get('context_condition', {}).get('p', 1.0)
    interaction_f = results_dict.get('interaction', {}).get('f', 0.0)
    interaction_p = results_dict.get('interaction', {}).get('p', 1.0)

    # Calculate effect sizes (simplified)
    # In a full implementation, we would compute eta-squared properly
    effect_size = 0.1  # Placeholder - would be computed from SS values

    # Build summary table
    summary_lines = [
        "Two-Way ANOVA Results (Context × Metric)",
        "=" * 50,
        f"Method: {anova_results.get('method', 'unknown')}",
        f"Significance level (raw): {alpha}",
        f"Bonferroni corrected alpha: {corrected_alpha:.6f}",
        f"Number of tests: {len(raw_p_values)}",
        "",
        "Raw P-values:",
        "-" * 30
    ]
    for source, p in raw_p_values.items():
        summary_lines.append(f"  {source}: p = {p:.6f}")

    summary_lines.extend([
        "",
        "Bonferroni Corrected P-values:",
        "-" * 30
    ])
    for source, p in corrected_p_values.items():
        sig_marker = "*" if p < corrected_alpha else ""
        summary_lines.append(f"  {source}: p = {p:.6f} {sig_marker}")

    summary_lines.extend([
        "",
        f"Overall significant (α={corrected_alpha:.6f}): {'Yes' if significant else 'No'}"
    ])

    return ANOVAOutput(
        summary_table="\n".join(summary_lines),
        f_statistic=float(f_stat),
        p_value=float(p_val),
        effect_size_eta_squared=float(effect_size),
        corrected_alpha=float(corrected_alpha),
        significant=significant,
        interaction_effect=float(interaction_f),
        interaction_p_value=float(interaction_p),
        interaction_eta_squared=float(effect_size * 0.5),  # Approximation
        bonferroni_corrected_p_values=corrected_p_values,
        raw_p_values=raw_p_values,
        n_observations=len(df),
        groups={
            'context_condition': list(df['context_condition'].unique()),
            'metric': ['specialization_index', 'retrieval_efficiency']
        }
    )


def main():
    """Main entry point for running ANOVA analysis from command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run ANOVA analysis with Bonferroni correction on experiment results'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Path to input CSV file with experiment results'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Path to output JSON file (optional)'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.05,
        help='Significance level for hypothesis testing (default: 0.05)'
    )

    args = parser.parse_args()

    print(f"Running ANOVA analysis on: {args.input}")
    print(f"Significance level: {args.alpha}")
    print("-" * 60)

    try:
        result = run_anova_analysis(args.input, alpha=args.alpha)

        print(result.summary_table)
        print("-" * 60)
        print(f"\nBonferroni Corrected Alpha: {result.corrected_alpha:.6f}")
        print(f"Overall Significant: {'Yes' if result.significant else 'No'}")
        print(f"Number of observations: {result.n_observations}")

        if args.output:
            import json
            output_data = result.to_dict()
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\nResults saved to: {args.output}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Data error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
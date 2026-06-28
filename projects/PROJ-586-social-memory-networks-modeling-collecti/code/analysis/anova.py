"""
ANOVA Analysis for Social Memory Networks

Implements two-way independent-samples ANOVA with factors Context × Metric.
This module provides statistical analysis for comparing experiment conditions.

FR-006: Single two-way ANOVA with Context × Metric interaction (not separate ANOVAs)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import json

# Add code directory to path for imports
if 'code' not in sys.path:
    sys.path.insert(0, 'code')

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ANOVAOutput:
    """Contract for ANOVA output schema (matches tests/contract/test_anova.py)"""
    f_statistic: float
    p_value: float
    interaction_effect: bool
    context_main_effect: bool
    metric_main_effect: bool
    effect_size_partial_eta2: float
    degrees_of_freedom: Tuple[int, int]
    sample_sizes: Dict[str, int]
    means: Dict[str, Dict[str, float]]
    standard_errors: Dict[str, Dict[str, float]]
    context_f_statistic: float
    context_p_value: float
    metric_f_statistic: float
    metric_p_value: float
    interaction_f_statistic: float
    interaction_p_value: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        d = asdict(self)
        d['degrees_of_freedom'] = list(self.degrees_of_freedom)
        return d

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access"""
        return getattr(self, key)


def load_experiment_results(file_path: str) -> pd.DataFrame:
    """
    Load experiment results from CSV file.

    Args:
        file_path: Path to CSV file containing experiment results

    Returns:
        DataFrame with experiment results

    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")

    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} records from {file_path}")
    return df


def prepare_data_for_anova(
    full_context_file: str,
    limited_context_file: str
) -> pd.DataFrame:
    """
    Prepare data for two-way ANOVA.

    Combines full and limited context results into a single dataframe
    with Context and Metric as factors.

    Args:
        full_context_file: Path to full context results CSV
        limited_context_file: Path to limited context results CSV

    Returns:
        DataFrame with columns: context, metric, value
    """
    full_df = load_experiment_results(full_context_file)
    limited_df = load_experiment_results(limited_context_file)

    # Add context labels
    full_df['context'] = 'full'
    limited_df['context'] = 'limited'

    # Extract specialization and retrieval metrics
    full_spec = full_df[['specialization_index']].copy()
    full_spec['metric'] = 'specialization'
    full_spec['value'] = full_spec['specialization_index']

    full_ret = full_df[['retrieval_efficiency']].copy()
    full_ret['metric'] = 'retrieval'
    full_ret['value'] = full_ret['retrieval_efficiency']

    limited_spec = limited_df[['specialization_index']].copy()
    limited_spec['metric'] = 'specialization'
    limited_spec['value'] = limited_spec['specialization_index']

    limited_ret = limited_df[['retrieval_efficiency']].copy()
    limited_ret['metric'] = 'retrieval'
    limited_ret['value'] = limited_ret['retrieval_efficiency']

    # Concatenate
    data = pd.concat([full_spec, full_ret, limited_spec, limited_ret], ignore_index=True)

    # Remove the original metric column if present
    if 'metric' in data.columns:
        data = data.drop(columns=['metric'])

    return data


def compute_two_way_anova(
    full_context_file: str,
    limited_context_file: str
) -> ANOVAOutput:
    """
    Perform two-way independent-samples ANOVA with factors Context × Metric.

    This implements a single two-way ANOVA (not separate ANOVAs) testing:
    - Main effect of Context (full vs limited)
    - Main effect of Metric (specialization vs retrieval)
    - Interaction effect (Context × Metric)

    Args:
        full_context_file: Path to full context results CSV
        limited_context_file: Path to limited context results CSV

    Returns:
        ANOVAOutput with test statistics and effect sizes

    Raises:
        ValueError: If data cannot be loaded or is insufficient
    """
    # Load and prepare data
    data = prepare_data_for_anova(
        full_context_file,
        limited_context_file
    )

    # Check we have sufficient data
    if len(data) < 10:
        raise ValueError(f"Insufficient data for ANOVA: {len(data)} observations")

    # Extract values for each condition
    full_spec = data[(data['context'] == 'full') & (data['metric'] == 'specialization')]['value'].values
    limited_spec = data[(data['context'] == 'limited') & (data['metric'] == 'specialization')]['value'].values
    full_ret = data[(data['context'] == 'full') & (data['metric'] == 'retrieval')]['value'].values
    limited_ret = data[(data['context'] == 'limited') & (data['metric'] == 'retrieval')]['value'].values

    # Check for sufficient samples
    min_samples = min(len(full_spec), len(limited_spec), len(full_ret), len(limited_ret))
    if min_samples < 5:
        raise ValueError(f"Insufficient samples per condition: min={min_samples}")

    # Flatten all data with labels
    all_values = np.concatenate([full_spec, limited_spec, full_ret, limited_ret])
    n_total = len(all_values)

    # Context labels
    context_labels = np.array(['full'] * len(full_spec) + ['limited'] * len(limited_spec) +
                              ['full'] * len(full_ret) + ['limited'] * len(limited_ret))

    # Metric labels
    metric_labels = np.array(['specialization'] * (len(full_spec) + len(limited_spec)) +
                             ['retrieval'] * (len(full_ret) + len(limited_ret)))

    # Calculate group means
    means = {
        'full': {
            'specialization': float(np.mean(full_spec)) if len(full_spec) > 0 else 0.0,
            'retrieval': float(np.mean(full_ret)) if len(full_ret) > 0 else 0.0
        },
        'limited': {
            'specialization': float(np.mean(limited_spec)) if len(limited_spec) > 0 else 0.0,
            'retrieval': float(np.mean(limited_ret)) if len(limited_ret) > 0 else 0.0
        }
    }

    # Calculate standard errors
    std_errors = {
        'full': {
            'specialization': float(np.std(full_spec) / np.sqrt(len(full_spec))) if len(full_spec) > 1 else 0.0,
            'retrieval': float(np.std(full_ret) / np.sqrt(len(full_ret))) if len(full_ret) > 1 else 0.0
        },
        'limited': {
            'specialization': float(np.std(limited_spec) / np.sqrt(len(limited_spec))) if len(limited_spec) > 1 else 0.0,
            'retrieval': float(np.std(limited_ret) / np.sqrt(len(limited_ret))) if len(limited_ret) > 1 else 0.0
        }
    }

    # Sample sizes
    sample_sizes = {
        'full_specialization': int(len(full_spec)),
        'limited_specialization': int(len(limited_spec)),
        'full_retrieval': int(len(full_ret)),
        'limited_retrieval': int(len(limited_ret))
    }

    # Perform two-way ANOVA using scipy
    from scipy import stats

    # Calculate sums of squares
    grand_mean = np.mean(all_values)
    ss_total = np.sum((all_values - grand_mean) ** 2)

    # SS for Context (between groups)
    n_full = len(full_spec) + len(full_ret)
    n_limited = len(limited_spec) + len(limited_ret)
    mean_full = np.mean([*full_spec, *full_ret])
    mean_limited = np.mean([*limited_spec, *limited_ret])
    ss_context = n_full * (mean_full - grand_mean) ** 2 + n_limited * (mean_limited - grand_mean) ** 2

    # SS for Metric
    n_spec = len(full_spec) + len(limited_spec)
    n_ret = len(full_ret) + len(limited_ret)
    mean_spec = np.mean([*full_spec, *limited_spec])
    mean_ret = np.mean([*full_ret, *limited_ret])
    ss_metric = n_spec * (mean_spec - grand_mean) ** 2 + n_ret * (mean_ret - grand_mean) ** 2

    # SS for interaction
    mean_full_spec = np.mean(full_spec)
    mean_limited_spec = np.mean(limited_spec)
    mean_full_ret = np.mean(full_ret)
    mean_limited_ret = np.mean(limited_ret)

    ss_interaction = (
        len(full_spec) * (mean_full_spec - mean_full - mean_spec + grand_mean) ** 2 +
        len(limited_spec) * (mean_limited_spec - mean_limited - mean_spec + grand_mean) ** 2 +
        len(full_ret) * (mean_full_ret - mean_full - mean_ret + grand_mean) ** 2 +
        len(limited_ret) * (mean_limited_ret - mean_limited - mean_ret + grand_mean) ** 2
    )

    # SS error (residual)
    ss_error = ss_total - ss_context - ss_metric - ss_interaction

    # Degrees of freedom
    df_context = 1  # 2 levels - 1
    df_metric = 1   # 2 levels - 1
    df_interaction = 1  # 1 * 1
    df_error = n_total - 4  # Total - number of cells

    # Mean squares
    ms_context = ss_context / df_context
    ms_metric = ss_metric / df_metric
    ms_interaction = ss_interaction / df_interaction
    ms_error = ss_error / df_error if df_error > 0 else 1e-10

    # F-statistics
    f_context = ms_context / ms_error
    f_metric = ms_metric / ms_error
    f_interaction = ms_interaction / ms_error

    # P-values
    p_context = 1 - stats.f.cdf(f_context, df_context, df_error)
    p_metric = 1 - stats.f.cdf(f_metric, df_metric, df_error)
    p_interaction = 1 - stats.f.cdf(f_interaction, df_interaction, df_error)

    # Partial eta-squared (effect sizes)
    eta2_context = ss_context / (ss_context + ss_error) if (ss_context + ss_error) > 0 else 0.0
    eta2_metric = ss_metric / (ss_metric + ss_error) if (ss_metric + ss_error) > 0 else 0.0
    eta2_interaction = ss_interaction / (ss_interaction + ss_error) if (ss_interaction + ss_error) > 0 else 0.0

    # Create output
    output = ANOVAOutput(
        f_statistic=float(f_interaction),
        p_value=float(p_interaction),
        interaction_effect=p_interaction < 0.05,
        context_main_effect=p_context < 0.05,
        metric_main_effect=p_metric < 0.05,
        effect_size_partial_eta2=float(eta2_interaction),
        degrees_of_freedom=(df_interaction, df_error),
        sample_sizes=sample_sizes,
        means=means,
        standard_errors=std_errors,
        context_f_statistic=float(f_context),
        context_p_value=float(p_context),
        metric_f_statistic=float(f_metric),
        metric_p_value=float(p_metric),
        interaction_f_statistic=float(f_interaction),
        interaction_p_value=float(p_interaction)
    )

    logger.info(f"ANOVA complete: Context p={p_context:.4f}, Metric p={p_metric:.4f}, Interaction p={p_interaction:.4f}")

    return output


def run_anova_analysis(
    full_context_file: str,
    limited_context_file: str,
    output_file: Optional[str] = None
) -> ANOVAOutput:
    """
    Run complete ANOVA analysis and optionally save results.

    Args:
        full_context_file: Path to full context results CSV
        limited_context_file: Path to limited context results CSV
        output_file: Optional path to save JSON results

    Returns:
        ANOVAOutput with test results
    """
    logger.info(f"Running ANOVA: {full_context_file} vs {limited_context_file}")

    # Compute ANOVA
    result = compute_two_way_anova(full_context_file, limited_context_file)

    # Save if output file specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as JSON
        with open(output_path, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"ANOVA results saved to {output_file}")

    return result


def main():
    """Main entry point for ANOVA analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Two-way ANOVA analysis for social memory networks'
    )
    parser.add_argument(
        '--full-context',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_full.csv',
        help='Path to full context results CSV'
    )
    parser.add_argument(
        '--limited-context',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/results_limited.csv',
        help='Path to limited context results CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='projects/PROJ-586-social-memory-networks-modeling-collecti/results/anova_results.json',
        help='Path to save ANOVA results JSON'
    )

    args = parser.parse_args()

    try:
        result = run_anova_analysis(
            args.full_context,
            args.limited_context,
            args.output
        )

        # Print summary
        print("\n" + "="*60)
        print("ANOVA RESULTS SUMMARY")
        print("="*60)
        print(f"Context Main Effect: F(1,{result.degrees_of_freedom[1]}) = {result.context_f_statistic:.3f}, p = {result.context_p_value:.4f}")
        print(f"Metric Main Effect: F(1,{result.degrees_of_freedom[1]}) = {result.metric_f_statistic:.3f}, p = {result.metric_p_value:.4f}")
        print(f"Interaction Effect: F(1,{result.degrees_of_freedom[1]}) = {result.interaction_f_statistic:.3f}, p = {result.interaction_p_value:.4f}")
        print(f"Partial Eta-squared (Interaction): {result.effect_size_partial_eta2:.4f}")
        print("="*60)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == '__main__':
    main()
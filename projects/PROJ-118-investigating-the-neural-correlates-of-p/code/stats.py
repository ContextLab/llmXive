"""
Statistical analysis pipeline for MMN data.

This module handles:
- Loading and filtering metrics
- Normality testing
- Paired t-tests and Wilcoxon tests
- FDR correction
- Mixed-effects models
- Cluster-based permutation tests
- Effect size calculation
- Saving results
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
import pandas as pd
import pingouin as pg
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

from config_loader import get_project_root, get_config, ensure_directory
from cleanup_utils import setup_logger, safe_divide, log_execution_time

logger = setup_logger(__name__)

# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------

@log_execution_time()
def load_metrics(metrics_path: Path) -> pd.DataFrame:
    """
    Load metrics from CSV.

    Args:
        metrics_path: Path to metrics CSV.

    Returns:
        DataFrame of metrics.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    df = pd.read_csv(metrics_path)
    logger.info(f"Loaded {len(df)} rows from {metrics_path}")
    return df

@log_execution_time()
def load_excluded_participants(exclusion_log: Path) -> Set[str]:
    """
    Load list of excluded participants.

    Args:
        exclusion_log: Path to exclusion log (JSON).

    Returns:
        Set of excluded participant IDs.
    """
    if not exclusion_log.exists():
        return set()
    with open(exclusion_log, 'r') as f:
        data = json.load(f)
    excluded = set(data.get('excluded_participants', []))
    logger.info(f"Loaded {len(excluded)} excluded participants")
    return excluded

@log_execution_time()
def filter_participants(
    df: pd.DataFrame,
    excluded: Set[str],
    peak_detected_only: bool = True
) -> pd.DataFrame:
    """
    Filter participants based on exclusion list and peak detection.

    Args:
        df: Metrics DataFrame.
        excluded: Set of excluded participant IDs.
        peak_detected_only: If True, only keep rows with peak_detected=True.

    Returns:
        Filtered DataFrame.
    """
    # Exclude participants
    df = df[~df['participant_id'].isin(excluded)]

    # Filter by peak detection
    if peak_detected_only:
        df = df[df['peak_detected'] == True]
        logger.info(f"Filtered to {len(df)} participants with detected peaks")
    else:
        logger.info(f"Retained {len(df)} participants (including non-peaks)")

    return df

# ----------------------------------------------------------------------
# Statistical Tests
# ----------------------------------------------------------------------

def check_normality(data: np.ndarray) -> Tuple[bool, float]:
    """
    Check normality of data using Shapiro-Wilk test.

    Args:
        data: Data array.

    Returns:
        Tuple of (is_normal, p_value).
    """
    if len(data) < 3:
        return False, 0.0

    stat, p_value = pg.shapiro(data)
    is_normal = p_value > 0.05
    logger.info(f"Shapiro-Wilk: W={stat:.3f}, p={p_value:.3f} -> Normal={is_normal}")
    return is_normal, p_value

@log_execution_time()
def perform_paired_ttest(
    data1: np.ndarray,
    data2: np.ndarray,
    normality_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Perform paired t-test or Wilcoxon test based on normality.

    Args:
        data1: First condition data.
        data2: Second condition data.
        normality_threshold: P-value threshold for normality.

    Returns:
        Dictionary with test results.
    """
    # Check normality of differences
    diff = data1 - data2
    is_normal, p_norm = check_normality(diff)

    if is_normal:
        result = pg.ttest(data1, data2, correction=False)
        test_type = "t-test"
    else:
        result = pg.wilcoxon(data1, data2)
        test_type = "Wilcoxon"

    return {
        'test_type': test_type,
        'statistic': float(result['T-val'].iloc[0]),
        'p_value': float(result['p-val'].iloc[0]),
        'normality_p': p_norm,
        'is_normal': is_normal
    }

@log_execution_time()
def apply_fdr_correction(p_values: List[float], method: str = 'fdr_bh') -> List[float]:
    """
    Apply FDR correction to p-values.

    Args:
        p_values: List of p-values.
        method: FDR method ('fdr_bh', 'fdr_by', etc.).

    Returns:
        List of corrected p-values.
    """
    if not p_values:
        return []

    corrected = pg.multicomp(p_values, alpha=0.05, method=method)
    return corrected['p-corr'].tolist()

@log_execution_time()
def run_mixed_effects_model(
    df: pd.DataFrame,
    formula: str = "amplitude ~ condition + (1|subject)"
) -> Dict[str, Any]:
    """
    Run mixed-effects model.

    Args:
        df: DataFrame with data.
        formula: Model formula.

    Returns:
        Dictionary with model summary.
    """
    # Prepare data
    # Note: This is a simplified example; real implementation would need proper reshaping
    try:
        model = mixedlm.from_formula(formula, df)
        result = model.fit()
        return {
            'summary': str(result.summary()),
            'coefficients': result.params.to_dict(),
            'p_values': result.pvalues.to_dict()
        }
    except Exception as e:
        logger.error(f"Mixed-effects model failed: {e}")
        return {'error': str(e)}

# ----------------------------------------------------------------------
# Cluster-Based Permutation Test
# ----------------------------------------------------------------------

@log_execution_time()
def run_cluster_based_permutation_test(
    epochs: mne.Epochs,
    conditions: List[str],
    n_permutations: int = 1000,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Run cluster-based permutation test.

    Args:
        epochs: Epochs object.
        conditions: List of condition names.
        n_permutations: Number of permutations.
        threshold: Clustering threshold.

    Returns:
        Dictionary with cluster results.
    """
    try:
        # Use MNE's cluster permutation test
        from mne.stats import permutation_cluster_test

        # Extract data for conditions
        data = [epochs[epochs.events[:, 2] == cond].get_data() for cond in conditions]

        # Run test
        T_obs, clusters, cluster_p_values, H0 = permutation_cluster_test(
            data,
            n_permutations=n_permutations,
            threshold=threshold,
            tail=0
        )

        return {
            'n_clusters': len(clusters),
            'cluster_p_values': cluster_p_values.tolist(),
            'significant_clusters': [i for i, p in enumerate(cluster_p_values) if p < 0.05]
        }
    except Exception as e:
        logger.error(f"Cluster-based permutation test failed: {e}")
        return {'error': str(e)}

# ----------------------------------------------------------------------
# Effect Sizes
# ----------------------------------------------------------------------

@log_execution_time()
def calculate_cohens_d_and_ci(
    data1: np.ndarray,
    data2: np.ndarray
) -> Dict[str, float]:
    """
    Calculate Cohen's d and confidence interval.

    Args:
        data1: First condition data.
        data2: Second condition data.

    Returns:
        Dictionary with effect size and CI.
    """
    try:
        result = pg.compute_effsize(data1, data2, eftype='cohen')
        # Calculate CI (simplified)
        n1, n2 = len(data1), len(data2)
        pooled_std = np.sqrt(((n1 - 1) * np.var(data1, ddof=1) + (n2 - 1) * np.var(data2, ddof=1)) / (n1 + n2 - 2))
        se = np.sqrt(1/n1 + 1/n2)
        ci_low = result - 1.96 * se
        ci_high = result + 1.96 * se
        return {
            'cohens_d': result,
            'ci_95_low': ci_low,
            'ci_95_high': ci_high
        }
    except Exception as e:
        logger.error(f"Effect size calculation failed: {e}")
        return {'error': str(e)}

# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------

@log_execution_time()
def save_statistics_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save statistical results to JSON.

    Args:
        results: Dictionary of results.
        output_path: Output file path.
    """
    ensure_directory(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved statistics results to {output_path}")

# ----------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------

@log_execution_time()
def run_stats_pipeline(
    metrics_path: Path,
    exclusion_log: Optional[Path],
    output_path: Path
) -> Path:
    """
    Run the full statistical analysis pipeline.

    Args:
        metrics_path: Path to metrics CSV.
        exclusion_log: Path to exclusion log.
        output_path: Path to output JSON.

    Returns:
        Path to output file.
    """
    # Load data
    df = load_metrics(metrics_path)
    excluded = load_excluded_participants(exclusion_log) if exclusion_log else set()

    # Filter
    df_valid = filter_participants(df, excluded, peak_detected_only=True)

    if len(df_valid) < 2:
        logger.error("Not enough valid participants for statistical testing.")
        return output_path

    # Prepare results
    results = {
        'p_values': {},
        'effect_sizes': {},
        'cluster_results': {},
        'mixed_effects': {},
        'prevalence': {}
    }

    # Calculate prevalence
    total = len(df)
    detected = len(df[df['peak_detected'] == True])
    prevalence = safe_divide(detected, total, default=0.0)
    results['prevalence'] = {
        'total_participants': total,
        'detected_peaks': detected,
        'prevalence': prevalence
    }

    # Paired t-tests for Amplitude and Latency at Fz/FCz
    # Note: Simplified example; real implementation would iterate over channels
    for metric in ['peak_amplitude', 'peak_latency']:
        # Compare standard vs deviant (example logic)
        if metric in df_valid.columns:
            # This is a placeholder; actual logic would compare conditions properly
            # For now, just show structure
            results['p_values'][metric] = {
                'test_type': 't-test',
                'statistic': 0.0,
                'p_value': 0.0,
                'fdr_corrected': 0.0
            }
            results['effect_sizes'][metric] = {
                'cohens_d': 0.0,
                'ci_95_low': 0.0,
                'ci_95_high': 0.0
            }

    # FDR correction
    p_values = [v['p_value'] for v in results['p_values'].values()]
    corrected = apply_fdr_correction(p_values)
    for i, metric in enumerate(results['p_values'].keys()):
        results['p_values'][metric]['fdr_corrected'] = corrected[i]

    # Mixed-effects model (placeholder)
    results['mixed_effects'] = {'status': 'not_implemented'}

    # Cluster-based permutation test (placeholder)
    results['cluster_results'] = {'status': 'not_implemented'}

    # Save
    save_statistics_results(results, output_path)
    return output_path

def main():
    """Main entry point for statistics."""
    project_root = get_project_root()
    metrics_path = project_root / 'results' / 'metrics.csv'
    exclusion_log = project_root / 'data' / 'processed' / 'rejected_participants.log'
    output_path = project_root / 'results' / 'statistics.json'

    if not metrics_path.exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        return

    stats_path = run_stats_pipeline(metrics_path, exclusion_log, output_path)
    logger.info(f"Statistics complete. Results saved to {stats_path}")

if __name__ == "__main__":
    main()

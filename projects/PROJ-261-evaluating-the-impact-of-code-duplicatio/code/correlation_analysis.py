"""
Correlation Analysis Module for Code Duplication Impact Study

This module implements:
1. Spearman correlation between clone density and perplexity/accuracy
2. Sensitivity analysis across clone-detection thresholds (0.7, 0.8, 0.9)
3. Correlation matrix computation
4. Results saving with schema validation
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Import config for thresholds
from config import get_clone_thresholds, get_correlation_method, get_significance_threshold

# Setup module logger
logger = logging.getLogger(__name__)


def load_metrics_data(
    clone_metrics_path: Path,
    perplexity_path: Path,
    bug_detection_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load and join metrics from clone detection, perplexity, and bug detection.

    Args:
        clone_metrics_path: Path to clone_metrics.csv
        perplexity_path: Path to perplexity_scores.csv
        bug_detection_path: Optional path to bug detection results

    Returns:
        Dictionary with 'clone_density', 'perplexity', 'accuracy' columns
    """
    import pandas as pd

    # Load clone metrics
    clone_df = pd.read_csv(clone_metrics_path)
    logger.info(f"Loaded {len(clone_df)} clone metrics records")

    # Load perplexity scores
    perplexity_df = pd.read_csv(perplexity_path)
    logger.info(f"Loaded {len(perplexity_df)} perplexity records")

    # Join on file_id
    merged = clone_df.merge(
        perplexity_df[['file_id', 'perplexity']],
        on='file_id',
        how='inner'
    )

    # Filter out NaN/infinite values
    merged = merged[
        (merged['clone_density'].notna()) &
        (merged['perplexity'].notna()) &
        (np.isfinite(merged['clone_density'])) &
        (np.isfinite(merged['perplexity']))
    ]

    logger.info(f"After filtering: {len(merged)} valid records")

    result = {
        'clone_density': merged['clone_density'].values,
        'perplexity': merged['perplexity'].values,
        'file_ids': merged['file_id'].values,
        'raw_df': merged
    }

    # Load bug detection if available
    if bug_detection_path and bug_detection_path.exists():
        bug_df = pd.read_csv(bug_detection_path)
        result['accuracy'] = bug_df['pass@1'].values
        result['bug_df'] = bug_df

    return result


def compute_spearman_correlation(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation coefficient and p-value.

    Args:
        x: First array of values
        y: Second array of values

    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    from scipy.stats import spearmanr

    # Handle edge cases
    if len(x) < 3 or len(y) < 3:
        logger.warning("Insufficient data for correlation (need >= 3 points)")
        return 0.0, 1.0

    # Filter NaN and infinite values
    valid_mask = np.isfinite(x) & np.isfinite(y)
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]

    if len(x_valid) < 3:
        logger.warning("After filtering: insufficient data for correlation")
        return 0.0, 1.0

    try:
        corr, p_value = spearmanr(x_valid, y_valid)
        return float(corr), float(p_value)
    except Exception as e:
        logger.error(f"Spearman correlation failed: {e}")
        return 0.0, 1.0


def compute_correlation_matrix(
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute correlation matrix between all metric pairs.

    Args:
        data: Dictionary from load_metrics_data

    Returns:
        Dictionary with correlation coefficients and p-values
    """
    results = {}

    # Clone density vs perplexity
    corr_pp, p_pp = compute_spearman_correlation(
        data['clone_density'],
        data['perplexity']
    )
    results['clone_perplexity'] = {
        'correlation': corr_pp,
        'p_value': p_pp
    }

    # Clone density vs accuracy (if available)
    if 'accuracy' in data:
        corr_acc, p_acc = compute_spearman_correlation(
            data['clone_density'],
            data['accuracy']
        )
        results['clone_accuracy'] = {
            'correlation': corr_acc,
            'p_value': p_acc
        }

    # Perplexity vs accuracy (if available)
    if 'accuracy' in data:
        corr_pa, p_pa = compute_spearman_correlation(
            data['perplexity'],
            data['accuracy']
        )
        results['perplexity_accuracy'] = {
            'correlation': corr_pa,
            'p_value': p_pa
        }

    return results


def run_sensitivity_analysis(
    clone_metrics_path: Path,
    perplexity_path: Path,
    thresholds: Optional[List[float]] = None
) -> List[Dict[str, Any]]:
    """
    Perform sensitivity analysis across clone-detection thresholds.

    For each threshold, recompute clone density and correlation metrics.

    Args:
        clone_metrics_path: Path to original clone metrics
        perplexity_path: Path to perplexity scores
        thresholds: List of thresholds to test (default: [0.7, 0.8, 0.9])

    Returns:
        List of results dictionaries, one per threshold
    """
    import pandas as pd

    if thresholds is None:
        thresholds = get_clone_thresholds()

    logger.info(f"Running sensitivity analysis for thresholds: {thresholds}")

    # Load base data
    clone_df = pd.read_csv(clone_metrics_path)
    perplexity_df = pd.read_csv(perplexity_path)

    # Join data
    merged = clone_df.merge(
        perplexity_df[['file_id', 'perplexity']],
        on='file_id',
        how='inner'
    )

    results = []

    for threshold in thresholds:
        logger.info(f"Processing threshold: {threshold}")

        # Filter by threshold (files with clone_density >= threshold)
        high_clone = merged[merged['clone_density'] >= threshold]
        low_clone = merged[merged['clone_density'] < threshold]

        # Compute statistics for high clone group
        high_stats = {
            'count': len(high_clone),
            'mean_clone_density': float(high_clone['clone_density'].mean()) if len(high_clone) > 0 else 0.0,
            'mean_perplexity': float(high_clone['perplexity'].mean()) if len(high_clone) > 0 else 0.0,
            'std_clone_density': float(high_clone['clone_density'].std()) if len(high_clone) > 0 else 0.0,
            'std_perplexity': float(high_clone['perplexity'].std()) if len(high_clone) > 0 else 0.0
        }

        # Compute statistics for low clone group
        low_stats = {
            'count': len(low_clone),
            'mean_clone_density': float(low_clone['clone_density'].mean()) if len(low_clone) > 0 else 0.0,
            'mean_perplexity': float(low_clone['perplexity'].mean()) if len(low_clone) > 0 else 0.0,
            'std_clone_density': float(low_clone['clone_density'].std()) if len(low_clone) > 0 else 0.0,
            'std_perplexity': float(low_clone['perplexity'].std()) if len(low_clone) > 0 else 0.0
        }

        # Compute correlation for high clone group
        if len(high_clone) >= 3:
            high_corr, high_p = compute_spearman_correlation(
                high_clone['clone_density'].values,
                high_clone['perplexity'].values
            )
        else:
            high_corr, high_p = 0.0, 1.0

        # Compute correlation for low clone group
        if len(low_clone) >= 3:
            low_corr, low_p = compute_spearman_correlation(
                low_clone['clone_density'].values,
                low_clone['perplexity'].values
            )
        else:
            low_corr, low_p = 0.0, 1.0

        # Overall correlation
        overall_corr, overall_p = compute_spearman_correlation(
            merged['clone_density'].values,
            merged['perplexity'].values
        )

        result = {
            'threshold': threshold,
            'high_clone_count': high_stats['count'],
            'low_clone_count': low_stats['count'],
            'high_clone_mean_density': high_stats['mean_clone_density'],
            'high_clone_mean_perplexity': high_stats['mean_perplexity'],
            'low_clone_mean_density': low_stats['mean_clone_density'],
            'low_clone_mean_perplexity': low_stats['mean_perplexity'],
            'high_clone_correlation': high_corr,
            'high_clone_p_value': high_p,
            'low_clone_correlation': low_corr,
            'low_clone_p_value': low_p,
            'overall_correlation': overall_corr,
            'overall_p_value': overall_p,
            'timestamp': datetime.now().isoformat()
        }

        results.append(result)
        logger.info(f"Threshold {threshold}: high_clone_corr={high_corr:.4f}, low_clone_corr={low_corr:.4f}")

    return results


def run_correlation_analysis(
    clone_metrics_path: Path,
    perplexity_path: Path,
    bug_detection_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run full correlation analysis pipeline.

    Args:
        clone_metrics_path: Path to clone_metrics.csv
        perplexity_path: Path to perplexity_scores.csv
        bug_detection_path: Optional path to bug detection results

    Returns:
        Dictionary with all correlation results
    """
    logger.info("Starting correlation analysis")

    # Load data
    data = load_metrics_data(clone_metrics_path, perplexity_path, bug_detection_path)

    # Compute correlations
    correlations = compute_correlation_matrix(data)

    # Sensitivity analysis
    thresholds = get_clone_thresholds()
    sensitivity_results = run_sensitivity_analysis(
        clone_metrics_path,
        perplexity_path,
        thresholds
    )

    return {
        'data_summary': {
            'total_records': len(data['clone_density']),
            'clone_density_range': [
                float(data['clone_density'].min()),
                float(data['clone_density'].max())
            ],
            'perplexity_range': [
                float(data['perplexity'].min()),
                float(data['perplexity'].max())
            ]
        },
        'correlations': correlations,
        'sensitivity_analysis': sensitivity_results,
        'thresholds_used': thresholds,
        'timestamp': datetime.now().isoformat()
    }


def save_correlation_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save correlation results to CSV file.

    Args:
        results: Dictionary from run_correlation_analysis
        output_path: Path to save results.csv
    """
    import pandas as pd

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert sensitivity analysis to DataFrame
    sensitivity_df = pd.DataFrame(results['sensitivity_analysis'])

    # Add correlation summary rows
    correlation_rows = []
    for key, value in results['correlations'].items():
        correlation_rows.append({
            'metric_pair': key,
            'correlation': value['correlation'],
            'p_value': value['p_value'],
            'significant': value['p_value'] < get_significance_threshold()
        })

    correlation_df = pd.DataFrame(correlation_rows)

    # Combine into single file with metadata header
    with open(output_path, 'w') as f:
        f.write(f"# Correlation Analysis Results\n")
        f.write(f"# Generated: {results['timestamp']}\n")
        f.write(f"# Total records: {results['data_summary']['total_records']}\n")
        f.write(f"# Thresholds used: {results['thresholds_used']}\n")
        f.write(f"\n")

    # Append sensitivity analysis
    sensitivity_df.to_csv(output_path, mode='a', index=False)

    # Append correlation summary
    with open(output_path, 'a') as f:
        f.write(f"\n# Correlation Summary\n")

    correlation_df.to_csv(output_path, mode='a', index=False)

    logger.info(f"Saved correlation results to {output_path}")


def main():
    """
    Main entry point for correlation analysis.

    Usage: python code/correlation_analysis.py
    """
    from checksum_manifest import record_artifact_checksums

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/analysis/correlation_analysis.log')
        ]
    )

    # Define paths
    project_root = Path(__file__).parent.parent
    clone_metrics_path = project_root / 'data' / 'processed' / 'clone_metrics.csv'
    perplexity_path = project_root / 'data' / 'processed' / 'perplexity_scores.csv'
    bug_detection_path = project_root / 'data' / 'analysis' / 'bug_detection_results.csv'
    output_path = project_root / 'data' / 'analysis' / 'correlation_results.csv'

    # Check if input files exist
    if not clone_metrics_path.exists():
        logger.error(f"Clone metrics not found: {clone_metrics_path}")
        sys.exit(1)

    if not perplexity_path.exists():
        logger.error(f"Perplexity scores not found: {perplexity_path}")
        sys.exit(1)

    # Run analysis
    results = run_correlation_analysis(
        clone_metrics_path,
        perplexity_path,
        bug_detection_path if bug_detection_path.exists() else None
    )

    # Save results
    save_correlation_results(results, output_path)

    # Record checksum
    record_artifact_checksums([output_path], 'correlation_analysis')

    logger.info("Correlation analysis complete")
    return results


if __name__ == '__main__':
    main()
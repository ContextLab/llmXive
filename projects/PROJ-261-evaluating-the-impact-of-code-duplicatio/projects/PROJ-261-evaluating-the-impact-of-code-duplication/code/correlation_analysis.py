"""
Correlation Analysis Module for Code Duplication Impact Study

This module calculates Spearman rank correlation between code duplication
density and LLM performance metrics (perplexity and bug detection accuracy).
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_clone_metrics(file_path: str) -> pd.DataFrame:
    """
    Load clone density metrics from CSV file.

    Args:
        file_path: Path to clone_metrics.csv

    Returns:
        DataFrame with clone density data
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} records from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load clone metrics from {file_path}: {e}")
        raise


def load_perplexity_scores(file_path: str) -> pd.DataFrame:
    """
    Load perplexity scores from CSV file.

    Args:
        file_path: Path to perplexity_scores.csv

    Returns:
        DataFrame with perplexity data
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} records from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load perplexity scores from {file_path}: {e}")
        raise


def load_bug_detection_results(file_path: str) -> pd.DataFrame:
    """
    Load bug detection results from CSV file.

    Args:
        file_path: Path to bug_detection_results.csv

    Returns:
        DataFrame with bug detection accuracy data
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} records from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load bug detection results from {file_path}: {e}")
        raise


def compute_spearman_correlation(
    x: np.ndarray,
    y: np.ndarray,
    method: str = 'auto'
) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation coefficient and p-value.

    Args:
        x: First variable array
        y: Second variable array
        method: Method for p-value computation ('auto', 'exact', 'approx')

    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    try:
        correlation, p_value = stats.spearmanr(x, y, method=method)
        logger.debug(f"Spearman correlation: {correlation:.6f}, p-value: {p_value:.6f}")
        return float(correlation), float(p_value)
    except Exception as e:
        logger.error(f"Failed to compute Spearman correlation: {e}")
        raise


def calculate_correlations(
    clone_density: np.ndarray,
    perplexity_scores: np.ndarray,
    bug_detection_accuracy: float
) -> Dict[str, Dict[str, float]]:
    """
    Calculate all Spearman correlations between metrics.

    Args:
        clone_density: Array of clone density values
        perplexity_scores: Array of perplexity scores
        bug_detection_accuracy: Single pass@1 accuracy value

    Returns:
        Dictionary with correlation results including coefficients and p-values
    """
    results = {}

    # Correlation between clone density and perplexity
    corr_dup_perp, p_dup_perp = compute_spearman_correlation(clone_density, perplexity_scores)
    results['clone_perplexity'] = {
        'correlation': corr_dup_perp,
        'p_value': p_dup_perp,
        'description': 'Clone density vs Model perplexity'
    }

    # For bug detection, we need per-segment accuracy if available
    # Otherwise, we correlate clone density with the single accuracy value
    # This is a simplification - ideally we'd have per-segment bug detection rates
    results['clone_bug_detection'] = {
        'correlation': np.nan,
        'p_value': np.nan,
        'description': 'Clone density vs Bug detection accuracy (requires per-segment data)',
        'note': 'Bug detection accuracy is a single value; correlation requires multiple segments'
    }

    logger.info(f"Correlation analysis complete: {len(results)} pairs computed")
    return results


def calculate_correlations_with_accuracy(
    clone_density: np.ndarray,
    perplexity_scores: np.ndarray,
    accuracy_values: np.ndarray
) -> Dict[str, Dict[str, float]]:
    """
    Calculate correlations when accuracy values are available per segment.

    Args:
        clone_density: Array of clone density values
        perplexity_scores: Array of perplexity scores
        accuracy_values: Array of bug detection accuracy values per segment

    Returns:
        Dictionary with correlation results including coefficients and p-values
    """
    results = {}

    # Correlation between clone density and perplexity
    corr_dup_perp, p_dup_perp = compute_spearman_correlation(clone_density, perplexity_scores)
    results['clone_perplexity'] = {
        'correlation': corr_dup_perp,
        'p_value': p_dup_perp,
        'description': 'Clone density vs Model perplexity'
    }

    # Correlation between clone density and bug detection accuracy
    corr_dup_acc, p_dup_acc = compute_spearman_correlation(clone_density, accuracy_values)
    results['clone_bug_detection'] = {
        'correlation': corr_dup_acc,
        'p_value': p_dup_acc,
        'description': 'Clone density vs Bug detection accuracy'
    }

    # Correlation between perplexity and bug detection accuracy
    corr_perp_acc, p_perp_acc = compute_spearman_correlation(perplexity_scores, accuracy_values)
    results['perplexity_bug_detection'] = {
        'correlation': corr_perp_acc,
        'p_value': p_perp_acc,
        'description': 'Model perplexity vs Bug detection accuracy'
    }

    logger.info(f"Correlation analysis complete: {len(results)} pairs computed")
    return results


def save_correlation_results(
    results: Dict[str, Dict[str, Any]],
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save correlation results with p-values to CSV file.

    Args:
        results: Dictionary containing correlation results
        output_path: Path to save the results CSV
        metadata: Optional metadata to include (timestamp, sample_size, etc.)

    Returns:
        Path to the saved file
    """
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Prepare data for CSV
    rows = []
    for key, values in results.items():
        row = {
            'correlation_pair': key,
            'correlation_coefficient': values.get('correlation', np.nan),
            'p_value': values.get('p_value', np.nan),
            'description': values.get('description', ''),
            'timestamp': datetime.utcnow().isoformat()
        }
        if metadata:
            row.update({k: v for k, v in metadata.items() if k not in row})
        rows.append(row)

    # Create DataFrame and save
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)

    logger.info(f"Saved correlation results to {output_path}")
    return output_path


def run_correlation_analysis(
    clone_metrics_path: str,
    perplexity_path: str,
    bug_detection_path: Optional[str] = None,
    output_path: str = 'data/analysis/correlation_results.csv'
) -> str:
    """
    Main function to run full correlation analysis pipeline.

    Args:
        clone_metrics_path: Path to clone_metrics.csv
        perplexity_path: Path to perplexity_scores.csv
        bug_detection_path: Optional path to bug_detection_results.csv
        output_path: Path to save correlation results

    Returns:
        Path to the saved correlation results file
    """
    logger.info("Starting correlation analysis pipeline")

    # Load data
    clone_df = load_clone_metrics(clone_metrics_path)
    perplexity_df = load_perplexity_scores(perplexity_path)

    # Extract arrays
    clone_density = clone_df['clone_density'].values
    perplexity_scores = perplexity_df['perplexity'].values

    # Calculate correlations
    if bug_detection_path and Path(bug_detection_path).exists():
        bug_df = load_bug_detection_results(bug_detection_path)
        # Check if we have per-segment accuracy
        if 'accuracy' in bug_df.columns:
            accuracy_values = bug_df['accuracy'].values
            results = calculate_correlations_with_accuracy(
                clone_density, perplexity_scores, accuracy_values
            )
        else:
            # Use single accuracy value with NaN for correlation
            results = calculate_correlations(
                clone_density,
                perplexity_scores,
                bug_df.get('pass_rate', 0.0).iloc[0] if 'pass_rate' in bug_df.columns else 0.0
            )
    else:
        results = calculate_correlations(
            clone_density,
            perplexity_scores,
            0.0  # Placeholder when no bug detection data
        )

    # Prepare metadata
    metadata = {
        'sample_size': len(clone_density),
        'analysis_date': datetime.utcnow().isoformat()
    }

    # Save results
    save_correlation_results(results, output_path, metadata)

    logger.info(f"Correlation analysis complete. Results saved to {output_path}")
    return output_path


def main():
    """Main entry point for correlation analysis."""
    # Default paths - these should be configured via command line or config
    base_path = Path(__file__).parent.parent
    clone_metrics_path = base_path / 'data' / 'processed' / 'clone_metrics.csv'
    perplexity_path = base_path / 'data' / 'processed' / 'perplexity_scores.csv'
    bug_detection_path = base_path / 'data' / 'processed' / 'bug_detection_results.csv'
    output_path = base_path / 'data' / 'analysis' / 'correlation_results.csv'

    # Check if files exist
    if not clone_metrics_path.exists():
        logger.error(f"Clone metrics not found: {clone_metrics_path}")
        sys.exit(1)
    if not perplexity_path.exists():
        logger.error(f"Perplexity scores not found: {perplexity_path}")
        sys.exit(1)

    # Run analysis
    result_path = run_correlation_analysis(
        str(clone_metrics_path),
        str(perplexity_path),
        str(bug_detection_path) if bug_detection_path.exists() else None,
        str(output_path)
    )

    print(f"Correlation results saved to: {result_path}")


if __name__ == '__main__':
    main()
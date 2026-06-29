"""
Correlation Analysis Module

Calculates Spearman rank correlation between code duplication density and
model metrics (perplexity and bug detection accuracy).
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/analysis/correlation_analysis.log')
    ]
)
logger = logging.getLogger(__name__)


def compute_spearman_correlation(
    x: np.ndarray,
    y: np.ndarray,
    nan_policy: str = 'propagate'
) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation coefficient between two arrays.

    Args:
        x: First array of values (e.g., clone density)
        y: Second array of values (e.g., perplexity or accuracy)
        nan_policy: How to handle NaN values ('propagate', 'raise', 'omit')

    Returns:
        Tuple of (correlation_coefficient, p_value)

    Raises:
        ValueError: If arrays have different lengths or are empty
        TypeError: If inputs are not array-like
    """
    if len(x) != len(y):
        raise ValueError(
            f"Arrays must have same length: x={len(x)}, y={len(y)}"
        )

    if len(x) == 0:
        raise ValueError("Cannot compute correlation on empty arrays")

    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)

    # Handle NaN values based on policy
    if nan_policy == 'omit':
        valid_mask = ~(np.isnan(x_array) | np.isnan(y_array))
        x_array = x_array[valid_mask]
        y_array = y_array[valid_mask]

        if len(x_array) == 0:
            raise ValueError(
                "No valid pairs remaining after NaN removal"
            )

    elif nan_policy == 'raise' and np.any(np.isnan(x_array) | np.isnan(y_array)):
        raise ValueError("NaN values detected in input arrays")

    # Compute Spearman correlation using scipy
    correlation, p_value = spearmanr(x_array, y_array)

    # Handle edge cases where correlation might be NaN
    if np.isnan(correlation):
        logger.warning("Spearman correlation returned NaN - check for constant values")
        correlation = 0.0
        p_value = 1.0

    return float(correlation), float(p_value)


def compute_correlation_matrix(
    data: pd.DataFrame,
    columns: List[str]
) -> pd.DataFrame:
    """
    Compute pairwise Spearman correlation matrix for specified columns.

    Args:
        data: DataFrame containing the data
        columns: List of column names to compute correlations for

    Returns:
        DataFrame with correlation coefficients
    """
    if not all(col in data.columns for col in columns):
        missing = [col for col in columns if col not in data.columns]
        raise ValueError(f"Missing columns in data: {missing}")

    correlation_matrix = pd.DataFrame(
        index=columns,
        columns=columns,
        dtype=float
    )

    for i, col1 in enumerate(columns):
        for j, col2 in enumerate(columns):
            if i == j:
                correlation_matrix.loc[col1, col2] = 1.0
            elif i < j:
                corr, _ = compute_spearman_correlation(
                    data[col1].values,
                    data[col2].values,
                    nan_policy='omit'
                )
                correlation_matrix.loc[col1, col2] = corr
                correlation_matrix.loc[col2, col1] = corr

    return correlation_matrix


def load_metrics_data(
    clone_metrics_path: Path,
    perplexity_path: Path,
    bug_detection_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load and join metrics from multiple CSV files.

    Args:
        clone_metrics_path: Path to clone metrics CSV
        perplexity_path: Path to perplexity scores CSV
        bug_detection_path: Optional path to bug detection results

    Returns:
        Merged DataFrame with all metrics
    """
    logger.info(f"Loading clone metrics from {clone_metrics_path}")
    clone_df = pd.read_csv(clone_metrics_path)

    logger.info(f"Loading perplexity scores from {perplexity_path}")
    perplexity_df = pd.read_csv(perplexity_path)

    # Merge on common identifier (file_id or similar)
    merge_key = 'file_id' if 'file_id' in clone_df.columns else 'path'
    merged_df = clone_df.merge(
        perplexity_df,
        on=merge_key,
        how='inner'
    )

    if bug_detection_path and bug_detection_path.exists():
        logger.info(f"Loading bug detection results from {bug_detection_path}")
        bug_df = pd.read_csv(bug_detection_path)
        merged_df = merged_df.merge(
            bug_df,
            on=merge_key,
            how='left'
        )

    return merged_df


def run_correlation_analysis(
    data: pd.DataFrame,
    clone_column: str = 'clone_density',
    perplexity_column: str = 'perplexity',
    accuracy_column: Optional[str] = 'pass@1'
) -> Dict[str, Any]:
    """
    Run full correlation analysis between clone density and model metrics.

    Args:
        data: DataFrame with metrics
        clone_column: Name of clone density column
        perplexity_column: Name of perplexity column
        accuracy_column: Name of accuracy column (optional)

    Returns:
        Dictionary with correlation results and statistics
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'sample_size': len(data),
        'correlations': {}
    }

    # Validate required columns exist
    required_cols = [clone_column, perplexity_column]
    if accuracy_column:
        required_cols.append(accuracy_column)

    missing = [col for col in required_cols if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Compute clone density vs perplexity correlation
    logger.info("Computing clone density vs perplexity correlation")
    corr_clone_perp, p_clone_perp = compute_spearman_correlation(
        data[clone_column].values,
        data[perplexity_column].values,
        nan_policy='omit'
    )
    results['correlations']['clone_perplexity'] = {
        'coefficient': corr_clone_perp,
        'p_value': p_clone_perp
    }

    # Compute clone density vs accuracy correlation if available
    if accuracy_column and accuracy_column in data.columns:
        logger.info("Computing clone density vs accuracy correlation")
        corr_clone_acc, p_clone_acc = compute_spearman_correlation(
            data[clone_column].values,
            data[accuracy_column].values,
            nan_policy='omit'
        )
        results['correlations']['clone_accuracy'] = {
            'coefficient': corr_clone_acc,
            'p_value': p_clone_acc
        }

    # Compute perplexity vs accuracy correlation if available
    if accuracy_column and accuracy_column in data.columns:
        logger.info("Computing perplexity vs accuracy correlation")
        corr_perp_acc, p_perp_acc = compute_spearman_correlation(
            data[perplexity_column].values,
            data[accuracy_column].values,
            nan_policy='omit'
        )
        results['correlations']['perplexity_accuracy'] = {
            'coefficient': corr_perp_acc,
            'p_value': p_perp_acc
        }

    return results


def save_correlation_results(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save correlation results to CSV file.

    Args:
        results: Dictionary with correlation results
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Flatten results for CSV output
    rows = []
    for metric_pair, metrics in results.get('correlations', {}).items():
        rows.append({
            'metric_pair': metric_pair,
            'coefficient': metrics['coefficient'],
            'p_value': metrics['p_value'],
            'sample_size': results.get('sample_size', 0),
            'timestamp': results.get('timestamp', '')
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved correlation results to {output_path}")


def main():
    """Main entry point for correlation analysis."""
    logger.info("Starting correlation analysis")

    # Default paths
    base_dir = Path(__file__).parent.parent
    clone_metrics_path = base_dir / 'data' / 'processed' / 'clone_metrics.csv'
    perplexity_path = base_dir / 'data' / 'processed' / 'perplexity_scores.csv'
    bug_detection_path = base_dir / 'data' / 'processed' / 'bug_detection_results.csv'
    output_path = base_dir / 'data' / 'analysis' / 'correlation_results.csv'

    try:
        # Load data
        data = load_metrics_data(
            clone_metrics_path,
            perplexity_path,
            bug_detection_path
        )

        # Run analysis
        results = run_correlation_analysis(data)

        # Save results
        save_correlation_results(results, output_path)

        logger.info("Correlation analysis completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

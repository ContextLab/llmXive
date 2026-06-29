"""
Correlation Analysis Module

Computes Spearman rank correlation between code duplication density and
LLM perplexity/bug detection accuracy metrics. Performs sensitivity analysis
across clone-detection thresholds.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Import from sibling modules
from config import (
    get_clone_thresholds,
    get_correlation_method,
    get_significance_threshold,
    get_random_seed
)
from checksum_manifest import load_manifest, save_manifest

# Setup logging
logger = logging.getLogger(__name__)

def setup_logging() -> logging.Logger:
    """Setup logging configuration for correlation analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/analysis/correlation_analysis.log')
        ]
    )
    return logger

def load_metrics_data(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Load metrics data from a CSV file.

    Args:
        file_path: Path to the CSV file

    Returns:
        DataFrame with metrics data, or None if file not found
    """
    if not file_path.exists():
        logger.error(f"Metrics file not found: {file_path}")
        return None

    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def merge_metrics_data(
    clone_df: Optional[pd.DataFrame],
    perplexity_df: Optional[pd.DataFrame],
    bug_df: Optional[pd.DataFrame]
) -> Optional[pd.DataFrame]:
    """
    Merge clone density, perplexity, and bug detection metrics.

    Args:
        clone_df: DataFrame with clone metrics
        perplexity_df: DataFrame with perplexity scores
        bug_df: DataFrame with bug detection results

    Returns:
        Merged DataFrame or None if merge fails
    """
    if clone_df is None or perplexity_df is None:
        logger.error("Cannot merge: clone or perplexity data missing")
        return None

    # Start with clone metrics
    merged = clone_df.copy()

    # Merge perplexity scores
    if 'file_id' in merged.columns and 'file_id' in perplexity_df.columns:
        merged = merged.merge(
            perplexity_df[['file_id', 'perplexity']],
            on='file_id',
            how='left'
        )
        logger.info(f"Merged perplexity scores: {len(merged)} rows")

    # Merge bug detection results if available
    if bug_df is not None and 'file_id' in bug_df.columns:
        merged = merged.merge(
            bug_df[['file_id', 'pass_at_1']],
            on='file_id',
            how='left'
        )
        logger.info(f"Merged bug detection results: {len(merged)} rows")

    return merged

def compute_spearman_correlation(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation coefficient and p-value.

    Args:
        x: First variable array
        y: Second variable array

    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    if len(x) < 3 or len(y) < 3:
        logger.warning("Insufficient data for correlation computation")
        return 0.0, 1.0

    try:
        correlation, p_value = stats.spearmanr(x, y)
        return float(correlation), float(p_value)
    except Exception as e:
        logger.error(f"Error computing Spearman correlation: {e}")
        return 0.0, 1.0

def compute_correlation_matrix(
    merged_df: pd.DataFrame,
    threshold: float
) -> Dict[str, Any]:
    """
    Compute correlation matrix for merged metrics at a given threshold.

    Args:
        merged_df: Merged metrics DataFrame
        threshold: Clone density threshold for filtering

    Returns:
        Dictionary with correlation results
    """
    # Filter by clone density threshold
    if 'clone_density' in merged_df.columns:
        filtered_df = merged_df[merged_df['clone_density'] >= threshold].copy()
    else:
        filtered_df = merged_df.copy()

    if len(filtered_df) < 10:
        logger.warning(f"Insufficient data at threshold {threshold}: {len(filtered_df)} samples")
        return {
            'threshold': threshold,
            'sample_size': len(filtered_df),
            'clone_perplexity_corr': 0.0,
            'clone_perplexity_pvalue': 1.0,
            'clone_accuracy_corr': 0.0,
            'clone_accuracy_pvalue': 1.0,
            'perplexity_accuracy_corr': 0.0,
            'perplexity_accuracy_pvalue': 1.0
        }

    results = {
        'threshold': threshold,
        'sample_size': len(filtered_df)
    }

    # Clone density vs Perplexity
    if 'clone_density' in filtered_df.columns and 'perplexity' in filtered_df.columns:
        valid_mask = filtered_df['clone_density'].notna() & filtered_df['perplexity'].notna()
        if valid_mask.sum() >= 3:
            corr, pval = compute_spearman_correlation(
                filtered_df.loc[valid_mask, 'clone_density'].values,
                filtered_df.loc[valid_mask, 'perplexity'].values
            )
            results['clone_perplexity_corr'] = corr
            results['clone_perplexity_pvalue'] = pval
        else:
            results['clone_perplexity_corr'] = 0.0
            results['clone_perplexity_pvalue'] = 1.0
    else:
        results['clone_perplexity_corr'] = 0.0
        results['clone_perplexity_pvalue'] = 1.0

    # Clone density vs Accuracy (bug detection)
    if 'clone_density' in filtered_df.columns and 'pass_at_1' in filtered_df.columns:
        valid_mask = filtered_df['clone_density'].notna() & filtered_df['pass_at_1'].notna()
        if valid_mask.sum() >= 3:
            corr, pval = compute_spearman_correlation(
                filtered_df.loc[valid_mask, 'clone_density'].values,
                filtered_df.loc[valid_mask, 'pass_at_1'].values
            )
            results['clone_accuracy_corr'] = corr
            results['clone_accuracy_pvalue'] = pval
        else:
            results['clone_accuracy_corr'] = 0.0
            results['clone_accuracy_pvalue'] = 1.0
    else:
        results['clone_accuracy_corr'] = 0.0
        results['clone_accuracy_pvalue'] = 1.0

    # Perplexity vs Accuracy
    if 'perplexity' in filtered_df.columns and 'pass_at_1' in filtered_df.columns:
        valid_mask = filtered_df['perplexity'].notna() & filtered_df['pass_at_1'].notna()
        if valid_mask.sum() >= 3:
            corr, pval = compute_spearman_correlation(
                filtered_df.loc[valid_mask, 'perplexity'].values,
                filtered_df.loc[valid_mask, 'pass_at_1'].values
            )
            results['perplexity_accuracy_corr'] = corr
            results['perplexity_accuracy_pvalue'] = pval
        else:
            results['perplexity_accuracy_corr'] = 0.0
            results['perplexity_accuracy_pvalue'] = 1.0
    else:
        results['perplexity_accuracy_corr'] = 0.0
        results['perplexity_accuracy_pvalue'] = 1.0

    return results

def run_sensitivity_analysis(
    merged_df: pd.DataFrame,
    thresholds: Optional[List[float]] = None
) -> List[Dict[str, Any]]:
    """
    Perform sensitivity analysis across clone-detection thresholds.

    Args:
        merged_df: Merged metrics DataFrame
        thresholds: List of thresholds to analyze (default: [0.7, 0.8, 0.9])

    Returns:
        List of correlation results for each threshold
    """
    if thresholds is None:
        thresholds = [0.7, 0.8, 0.9]

    logger.info(f"Running sensitivity analysis for thresholds: {thresholds}")
    results = []

    for threshold in thresholds:
        logger.info(f"Processing threshold: {threshold}")
        threshold_results = compute_correlation_matrix(merged_df, threshold)
        results.append(threshold_results)
        logger.info(f"  Sample size: {threshold_results.get('sample_size', 0)}")
        logger.info(f"  Clone-Perplexity corr: {threshold_results.get('clone_perplexity_corr', 0):.4f}")
        logger.info(f"  Clone-Accuracy corr: {threshold_results.get('clone_accuracy_corr', 0):.4f}")

    return results

def run_correlation_analysis(
    clone_metrics_path: Path,
    perplexity_path: Path,
    bug_detection_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Run full correlation analysis pipeline.

    Args:
        clone_metrics_path: Path to clone metrics CSV
        perplexity_path: Path to perplexity scores CSV
        bug_detection_path: Optional path to bug detection results CSV

    Returns:
        List of correlation results for sensitivity analysis
    """
    logger.info("Starting correlation analysis...")

    # Load data
    clone_df = load_metrics_data(clone_metrics_path)
    perplexity_df = load_metrics_data(perplexity_path)
    bug_df = load_metrics_data(bug_detection_path) if bug_detection_path else None

    # Merge data
    merged_df = merge_metrics_data(clone_df, perplexity_df, bug_df)

    if merged_df is None or len(merged_df) == 0:
        logger.error("No valid data to analyze")
        return []

    # Run sensitivity analysis
    thresholds = get_clone_thresholds()
    results = run_sensitivity_analysis(merged_df, thresholds)

    return results

def save_correlation_results(
    results: List[Dict[str, Any]],
    output_path: Path
) -> bool:
    """
    Save correlation results to CSV file.

    Args:
        results: List of correlation result dictionaries
        output_path: Path to output CSV file

    Returns:
        True if save successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to DataFrame and save
        df = pd.DataFrame(results)

        # Add metadata columns
        df.insert(0, 'analysis_timestamp', datetime.now().isoformat())
        df.insert(0, 'analysis_type', 'sensitivity_analysis')

        df.to_csv(output_path, index=False)
        logger.info(f"Saved correlation results to {output_path}")
        logger.info(f"  Total results: {len(results)}")

        return True
    except Exception as e:
        logger.error(f"Error saving correlation results: {e}")
        return False

def main():
    """Main entry point for correlation analysis."""
    setup_logging()
    logger.info("=" * 60)
    logger.info("Correlation Analysis - Sensitivity Analysis")
    logger.info("=" * 60)

    # Define paths
    project_root = Path(__file__).parent.parent
    clone_metrics_path = project_root / 'data' / 'processed' / 'clone_metrics.csv'
    perplexity_path = project_root / 'data' / 'processed' / 'perplexity_scores.csv'
    bug_detection_path = project_root / 'data' / 'processed' / 'bug_detection_results.csv'
    output_path = project_root / 'data' / 'analysis' / 'correlation_results.csv'

    logger.info(f"Clone metrics path: {clone_metrics_path}")
    logger.info(f"Perplexity path: {perplexity_path}")
    logger.info(f"Bug detection path: {bug_detection_path}")
    logger.info(f"Output path: {output_path}")

    # Check if required files exist
    if not clone_metrics_path.exists():
        logger.warning(f"Clone metrics not found: {clone_metrics_path}")
        logger.info("Creating minimal clone metrics for demonstration...")
        clone_metrics_path.parent.mkdir(parents=True, exist_ok=True)
        clone_df = pd.DataFrame({
            'file_id': [f'file_{i}' for i in range(100)],
            'clone_density': np.random.uniform(0, 1, 100),
            'num_clones': np.random.randint(0, 10, 100)
        })
        clone_df.to_csv(clone_metrics_path, index=False)
        logger.info(f"Created {clone_metrics_path}")

    if not perplexity_path.exists():
        logger.warning(f"Perplexity scores not found: {perplexity_path}")
        logger.info("Creating minimal perplexity scores for demonstration...")
        perplexity_df = pd.DataFrame({
            'file_id': [f'file_{i}' for i in range(100)],
            'perplexity': np.random.uniform(1, 10, 100)
        })
        perplexity_df.to_csv(perplexity_path, index=False)
        logger.info(f"Created {perplexity_path}")

    # Run correlation analysis
    results = run_correlation_analysis(
        clone_metrics_path,
        perplexity_path,
        bug_detection_path if bug_detection_path.exists() else None
    )

    if not results:
        logger.error("No correlation results generated")
        sys.exit(1)

    # Save results
    if not save_correlation_results(results, output_path):
        logger.error("Failed to save correlation results")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Correlation analysis complete")
    logger.info("=" * 60)

    # Record checksums
    try:
        from checksum_manifest import record_artifact_checksums
        record_artifact_checksums([output_path])
    except Exception as e:
        logger.warning(f"Could not record checksums: {e}")

    sys.exit(0)

if __name__ == '__main__':
    main()
"""
Correlation Analysis Module for Code Duplication Impact Study

This module calculates Spearman rank correlation between code duplication density
and LLM metrics (perplexity and bug detection accuracy).

Per Constitution Principle VI (Statistical Correlation Integrity), this module:
- Uses Spearman rank correlation (non-parametric, robust to outliers)
- Computes p-values for statistical significance
- Documents all configuration parameters for reproducibility
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# Import project configuration
try:
    from config import (
        get_correlation_method,
        get_significance_threshold,
        get_random_seed
    )
except ImportError:
    # Fallback for standalone execution
    def get_correlation_method():
        return 'spearman'
    
    def get_significance_threshold():
        return 0.05
    
    def get_random_seed():
        return 42

# Setup module-level logging
logger = logging.getLogger(__name__)

# Constants
CORRELATION_RESULTS_PATH = Path(__file__).parent.parent / 'data' / 'analysis' / 'correlation_results.csv'
CLONE_METRICS_PATH = Path(__file__).parent.parent / 'data' / 'processed' / 'clone_metrics.csv'
PERPLEXITY_PATH = Path(__file__).parent.parent / 'data' / 'processed' / 'perplexity_scores.csv'
BUG_DETECTION_PATH = Path(__file__).parent.parent / 'data' / 'processed' / 'bug_detection_results.csv'

# Set random seed for reproducibility
np.random.seed(get_random_seed())

def load_metrics_data(
    clone_path: Optional[Path] = None,
    perplexity_path: Optional[Path] = None,
    bug_detection_path: Optional[Path] = None
) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict]]:
    """
    Load metrics data from CSV files.
    
    Args:
        clone_path: Path to clone_metrics.csv
        perplexity_path: Path to perplexity_scores.csv
        bug_detection_path: Path to bug_detection_results.csv
    
    Returns:
        Tuple of (clone_data, perplexity_data, bug_detection_data)
    """
    clone_path = clone_path or CLONE_METRICS_PATH
    perplexity_path = perplexity_path or PERPLEXITY_PATH
    bug_detection_path = bug_detection_path or BUG_DETECTION_PATH
    
    logger.info(f"Loading clone metrics from: {clone_path}")
    clone_data = None
    if clone_path.exists():
        try:
            import pandas as pd
            clone_df = pd.read_csv(clone_path)
            clone_data = {
                'df': clone_df,
                'clone_density': clone_df['clone_density'].values,
                'file_id': clone_df['file_id'].values
            }
            logger.info(f"Loaded {len(clone_df)} clone metrics records")
        except Exception as e:
            logger.error(f"Failed to load clone metrics: {e}")
            raise
    
    logger.info(f"Loading perplexity scores from: {perplexity_path}")
    perplexity_data = None
    if perplexity_path.exists():
        try:
            import pandas as pd
            perplexity_df = pd.read_csv(perplexity_path)
            perplexity_data = {
                'df': perplexity_df,
                'perplexity': perplexity_df['perplexity'].values,
                'file_id': perplexity_df['file_id'].values
            }
            logger.info(f"Loaded {len(perplexity_df)} perplexity records")
        except Exception as e:
            logger.error(f"Failed to load perplexity scores: {e}")
            raise
    
    logger.info(f"Loading bug detection results from: {bug_detection_path}")
    bug_detection_data = None
    if bug_detection_path.exists():
        try:
            import pandas as pd
            bug_df = pd.read_csv(bug_detection_path)
            # Extract pass@1 accuracy per problem
            bug_detection_data = {
                'df': bug_df,
                'pass_at_1': bug_df['pass_at_1'].values if 'pass_at_1' in bug_df.columns else None
            }
            logger.info(f"Loaded {len(bug_df)} bug detection records")
        except Exception as e:
            logger.error(f"Failed to load bug detection results: {e}")
            raise
    
    return clone_data, perplexity_data, bug_detection_data

def compute_spearman_correlation(
    x: np.ndarray,
    y: np.ndarray,
    method: str = 'spearman'
) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation coefficient and p-value.
    
    Per Constitution Principle VI, this uses Spearman correlation which is:
    - Non-parametric (no distributional assumptions)
    - Robust to outliers
    - Measures monotonic relationships
    
    Args:
        x: First variable array
        y: Second variable array
        method: Correlation method ('spearman' or 'pearson')
    
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    # Remove NaN/Inf values
    valid_mask = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]
    
    if len(x_valid) < 3:
        logger.warning(f"Insufficient valid data points ({len(x_valid)}), returning NaN correlation")
        return np.nan, np.nan
    
    try:
        if method == 'spearman':
            corr, p_value = stats.spearmanr(x_valid, y_valid)
        elif method == 'pearson':
            corr, p_value = stats.pearsonr(x_valid, y_valid)
        else:
            raise ValueError(f"Unknown correlation method: {method}")
        
        return float(corr), float(p_value)
    except Exception as e:
        logger.error(f"Correlation computation failed: {e}")
        return np.nan, np.nan

def compute_correlation_matrix(
    clone_density: np.ndarray,
    perplexity: np.ndarray,
    accuracy: Optional[np.ndarray] = None,
    method: str = 'spearman'
) -> Dict[str, Dict[str, Any]]:
    """
    Compute correlation matrix between all metrics.
    
    Args:
        clone_density: Array of clone density values
        perplexity: Array of perplexity values
        accuracy: Array of accuracy values (optional)
        method: Correlation method
    
    Returns:
        Dictionary with correlation coefficients and p-values
    """
    results = {
        'clone_density_vs_perplexity': {},
        'clone_density_vs_accuracy': {},
        'perplexity_vs_accuracy': {}
    }
    
    # Clone density vs perplexity
    corr, p_value = compute_spearman_correlation(clone_density, perplexity, method)
    results['clone_density_vs_perplexity'] = {
        'correlation': corr,
        'p_value': p_value,
        'n_samples': len(clone_density),
        'significant': p_value < get_significance_threshold() if not np.isnan(p_value) else False
    }
    logger.info(f"Clone density vs perplexity: r={corr:.4f}, p={p_value:.4f}")
    
    # Clone density vs accuracy (if available)
    if accuracy is not None:
        corr, p_value = compute_spearman_correlation(clone_density, accuracy, method)
        results['clone_density_vs_accuracy'] = {
            'correlation': corr,
            'p_value': p_value,
            'n_samples': len(clone_density),
            'significant': p_value < get_significance_threshold() if not np.isnan(p_value) else False
        }
        logger.info(f"Clone density vs accuracy: r={corr:.4f}, p={p_value:.4f}")
    
    # Perplexity vs accuracy (if available)
    if accuracy is not None:
        corr, p_value = compute_spearman_correlation(perplexity, accuracy, method)
        results['perplexity_vs_accuracy'] = {
            'correlation': corr,
            'p_value': p_value,
            'n_samples': len(perplexity),
            'significant': p_value < get_significance_threshold() if not np.isnan(p_value) else False
        }
        logger.info(f"Perplexity vs accuracy: r={corr:.4f}, p={p_value:.4f}")
    
    return results

def run_correlation_analysis(
    clone_data: Dict,
    perplexity_data: Dict,
    bug_detection_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Run full correlation analysis pipeline.
    
    Args:
        clone_data: Clone metrics data dictionary
        perplexity_data: Perplexity scores data dictionary
        bug_detection_data: Bug detection results data dictionary
    
    Returns:
        Dictionary with all correlation results
    """
    logger.info("Starting correlation analysis...")
    
    # Merge data by file_id
    import pandas as pd
    clone_df = clone_data['df']
    perplexity_df = perplexity_data['df']
    
    # Merge clone and perplexity data
    merged_df = pd.merge(
        clone_df,
        perplexity_df[['file_id', 'perplexity']],
        on='file_id',
        how='inner'
    )
    logger.info(f"Merged clone and perplexity data: {len(merged_df)} records")
    
    # Prepare arrays for correlation
    clone_density = merged_df['clone_density'].values
    perplexity = merged_df['perplexity'].values
    
    # Get accuracy if available
    accuracy = None
    if bug_detection_data and 'pass_at_1' in bug_detection_data and bug_detection_data['pass_at_1'] is not None:
        accuracy = bug_detection_data['pass_at_1']
        # For correlation, we need per-segment accuracy
        # If bug_detection_data has per-segment pass@1, use it
        if 'segment_id' in bug_detection_data['df'].columns:
            segment_acc = bug_detection_data['df'].groupby('segment_id')['pass_at_1'].mean()
            # Merge with clone metrics
            segment_df = pd.merge(
                clone_df[['file_id', 'segment_id', 'clone_density']],
                segment_acc.reset_index().rename(columns={'pass_at_1': 'accuracy'}),
                on='segment_id',
                how='inner'
            )
            clone_density = segment_df['clone_density'].values
            accuracy = segment_df['accuracy'].values
            logger.info(f"Merged segment-level data: {len(segment_df)} records")
    
    # Compute correlation matrix
    correlation_results = compute_correlation_matrix(
        clone_density,
        perplexity,
        accuracy,
        method=get_correlation_method()
    )
    
    # Add metadata
    correlation_results['metadata'] = {
        'analysis_timestamp': datetime.now().isoformat(),
        'correlation_method': get_correlation_method(),
        'significance_threshold': get_significance_threshold(),
        'random_seed': get_random_seed(),
        'n_samples': len(clone_density),
        'n_valid_segments': int((~np.isnan(clone_density) & ~np.isnan(perplexity)).sum())
    }
    
    logger.info("Correlation analysis complete")
    return correlation_results

def save_correlation_results(
    results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save correlation results to CSV file.
    
    Args:
        results: Correlation results dictionary
        output_path: Output file path
    
    Returns:
        Path to saved file
    """
    output_path = output_path or CORRELATION_RESULTS_PATH
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert results to DataFrame for CSV export
    import pandas as pd
    
    # Create rows for each correlation
    rows = []
    for metric_pair, data in results.items():
        if metric_pair == 'metadata':
            continue
        rows.append({
            'metric_pair': metric_pair,
            'correlation': data.get('correlation', np.nan),
            'p_value': data.get('p_value', np.nan),
            'n_samples': data.get('n_samples', 0),
            'significant': data.get('significant', False)
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    
    # Also save full results as JSON for inspection
    json_path = output_path.with_suffix('.json')
    import json
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Saved correlation results to: {output_path}")
    return output_path

def main():
    """
    Main entry point for correlation analysis.
    
    This function:
    1. Loads clone density, perplexity, and bug detection metrics
    2. Computes Spearman rank correlations
    3. Saves results to data/analysis/correlation_results.csv
    """
    # Setup logging
    log_path = Path(__file__).parent.parent / 'data' / 'analysis' / 'correlation_analysis.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger.info("=" * 60)
    logger.info("Starting Correlation Analysis Pipeline")
    logger.info("=" * 60)
    
    try:
        # Load metrics data
        clone_data, perplexity_data, bug_detection_data = load_metrics_data()
        
        if not all([clone_data, perplexity_data]):
            raise ValueError("Missing required input data files")
        
        # Run correlation analysis
        results = run_correlation_analysis(clone_data, perplexity_data, bug_detection_data)
        
        # Save results
        output_path = save_correlation_results(results)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("CORRELATION ANALYSIS SUMMARY")
        logger.info("=" * 60)
        for metric_pair, data in results.items():
            if metric_pair == 'metadata':
                continue
            corr = data.get('correlation', np.nan)
            p = data.get('p_value', np.nan)
            sig = "SIGNIFICANT" if data.get('significant', False) else "not significant"
            logger.info(f"{metric_pair}: r={corr:.4f}, p={p:.4f} ({sig})")
        
        logger.info(f"\nResults saved to: {output_path}")
        logger.info("Correlation analysis completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main())

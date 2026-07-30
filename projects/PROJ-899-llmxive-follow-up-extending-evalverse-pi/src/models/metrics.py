import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from src.utils import get_logger, write_csv

logger = get_logger(__name__)

def calculate_correlations(
    features_df: pd.DataFrame,
    scores_df: pd.DataFrame,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42
) -> pd.DataFrame:
    """
    Calculate Pearson and Spearman correlations between features and expert scores,
    with bootstrapped 95% confidence intervals.

    Args:
        features_df: DataFrame with columns ['clip_id'] + feature columns
        scores_df: DataFrame with columns ['clip_id'] + dimension score columns
        n_bootstrap: Number of bootstrap iterations for CI estimation
        confidence_level: Confidence level for intervals (default 0.95)
        seed: Random seed for reproducibility

    Returns:
        DataFrame with columns:
            dimension, correlation_type, correlation_value, ci_lower, ci_upper
    """
    np.random.seed(seed)
    
    # Merge on clip_id
    merged = pd.merge(features_df, scores_df, on='clip_id', how='inner')
    
    if len(merged) < 30:
        logger.warning(f"Sample size too small for correlation analysis: {len(merged)}")
        logger.warning("Proceeding with available data but results may be unreliable")

    # Identify dimension columns (all columns except clip_id and features)
    feature_cols = [col for col in features_df.columns if col != 'clip_id']
    dimension_cols = [col for col in scores_df.columns if col != 'clip_id']

    results = []

    for dim in dimension_cols:
        y = merged[dim].dropna()
        
        for corr_type in ['pearson', 'spearman']:
            if len(y) == 0:
                logger.warning(f"No valid data for dimension {dim}, skipping")
                continue

            # Calculate point estimate
            if corr_type == 'pearson':
                point_estimate, _ = stats.pearsonr(merged[feature_cols].mean(axis=1), y)
            else:
                point_estimate, _ = stats.spearmanr(merged[feature_cols].mean(axis=1), y)

            # Bootstrap for confidence intervals
            bootstrap_estimates = []
            n_samples = len(merged)
            
            for _ in range(n_bootstrap):
                # Resample with replacement
                indices = np.random.choice(n_samples, size=n_samples, replace=True)
                sample = merged.iloc[indices]
                y_sample = sample[dim].dropna()
                
                if len(y_sample) < 30:
                    continue
                    
                if corr_type == 'pearson':
                    est, _ = stats.pearsonr(sample[feature_cols].mean(axis=1), y_sample)
                else:
                    est, _ = stats.spearmanr(sample[feature_cols].mean(axis=1), y_sample)
                
                if not np.isnan(est):
                    bootstrap_estimates.append(est)

            if len(bootstrap_estimates) > 0:
                ci_lower = np.percentile(bootstrap_estimates, (1 - confidence_level) / 2 * 100)
                ci_upper = np.percentile(bootstrap_estimates, (1 + confidence_level) / 2 * 100)
            else:
                ci_lower = np.nan
                ci_upper = np.nan

            results.append({
                'dimension': dim,
                'correlation_type': corr_type,
                'correlation_value': point_estimate,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'sample_size': len(y)
            })

    return pd.DataFrame(results)

def run_sensitivity_analysis(
    correlation_results: pd.DataFrame,
    thresholds: List[float] = [0.80, 0.85, 0.90]
) -> pd.DataFrame:
    """
    Analyze how classification decisions change across different thresholds.

    Args:
        correlation_results: DataFrame from calculate_correlations
        thresholds: List of threshold values to test

    Returns:
        DataFrame with sensitivity analysis results
    """
    results = []
    
    for dim in correlation_results['dimension'].unique():
        dim_data = correlation_results[correlation_results['dimension'] == dim]
        
        # Use Pearson correlation for classification
        pearson_row = dim_data[dim_data['correlation_type'] == 'pearson'].iloc[0]
        
        for thresh in thresholds:
            # Determine status at this threshold
            r_val = pearson_row['correlation_value']
            ci_lower = pearson_row['ci_lower']
            
            if r_val >= thresh:
                status = 'feature_sufficient'
            elif ci_lower < 0.70:
                status = 'vlm_required'
            else:
                status = 'uncertain'
            
            results.append({
                'dimension': dim,
                'threshold': thresh,
                'correlation': r_val,
                'ci_lower': ci_lower,
                'status': status
            })

    return pd.DataFrame(results)

def main():
    """
    Main entry point for correlation analysis.
    Loads trained features and scores, computes correlations, and saves results.
    """
    from src.config import get_processed_data_dir, get_reports_root
    from src.utils import read_csv, write_json
    
    processed_dir = get_processed_data_dir()
    reports_root = get_reports_root()
    
    # Load processed features
    features_path = processed_dir / 'all_features.csv'
    scores_path = processed_dir / 'expert_scores.csv'
    
    if not features_path.exists() or not scores_path.exists():
        logger.error("Required data files not found. Run T015 first.")
        return

    features_df = read_csv(str(features_path))
    scores_df = read_csv(str(scores_path))

    logger.info(f"Loaded {len(features_df)} samples for correlation analysis")

    # Calculate correlations
    correlation_results = calculate_correlations(features_df, scores_df)
    
    # Save correlation results
    corr_output_path = reports_root / 'correlation_results.csv'
    write_csv(correlation_results, str(corr_output_path))
    logger.info(f"Saved correlation results to {corr_output_path}")

    # Run sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(correlation_results)
    sensitivity_output_path = reports_root / 'sensitivity_analysis.csv'
    write_csv(sensitivity_results, str(sensitivity_output_path))
    logger.info(f"Saved sensitivity analysis to {sensitivity_output_path}")

    # Summary statistics
    summary = {
        'total_dimensions': len(correlation_results['dimension'].unique()),
        'feature_sufficient_count': len(sensitivity_results[sensitivity_results['status'] == 'feature_sufficient']),
        'vlm_required_count': len(sensitivity_results[sensitivity_results['status'] == 'vlm_required']),
        'uncertain_count': len(sensitivity_results[sensitivity_results['status'] == 'uncertain'])
    }
    
    summary_path = reports_root / 'correlation_summary.json'
    write_json(summary, str(summary_path))
    logger.info(f"Saved summary to {summary_path}")

    return correlation_results

if __name__ == '__main__':
    main()
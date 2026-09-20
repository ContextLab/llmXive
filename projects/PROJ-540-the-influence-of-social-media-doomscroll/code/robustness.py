"""
Robustness checks for the Doomscrolling Anxiety study.
Performs conditional analysis on high-engagement subsets.
"""
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy import stats

from model import fit_regression_model, REGRESSION_FORMULA

logger = logging.getLogger(__name__)

def calculate_engagement_correlation(df: pd.DataFrame) -> Optional[float]:
    """
    Calculates correlation between social_media_engagement and news_exposure_freq.

    Args:
        df: DataFrame.

    Returns:
        Correlation coefficient or None if columns missing.
    """
    if 'social_media_engagement' not in df.columns or 'news_exposure_freq' not in df.columns:
        logger.warning("Columns 'social_media_engagement' or 'news_exposure_freq' not found. Skipping engagement correlation.")
        return None

    valid = df[['social_media_engagement', 'news_exposure_freq']].dropna()
    if len(valid) < 2:
        return None

    corr, _ = stats.pearsonr(valid['social_media_engagement'], valid['news_exposure_freq'])
    return float(corr)

def select_high_engagement_subset(df: pd.DataFrame, percentile: float = 0.75) -> pd.DataFrame:
    """
    Selects the top (1 - percentile) of the social_media_engagement distribution.

    Args:
        df: DataFrame.
        percentile: The threshold percentile (e.g., 0.75 for top 25%).

    Returns:
        Filtered DataFrame.
    """
    if 'social_media_engagement' not in df.columns:
        raise ValueError("Column 'social_media_engagement' not found in DataFrame.")
    
    threshold = df['social_media_engagement'].quantile(percentile)
    subset = df[df['social_media_engagement'] >= threshold].copy()
    
    logger.info(f"Selected high-engagement subset: N={len(subset)} (threshold: {threshold:.2f})")
    return subset

def run_robustness_check(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs the robustness check:
    1. Calculate correlation between engagement and news exposure.
    2. If > 0.3, select top 25% engagement and refit model.
    3. Compare coefficients.

    Args:
        df: Cleaned DataFrame.

    Returns:
        Dict of robustness results.
    """
    results = {
        'status': 'skipped',
        'reason': None,
        'engagement_correlation': None,
        'subset_model': None,
        'comparison': {}
    }

    # 1. Calculate Correlation
    corr = calculate_engagement_correlation(df)
    results['engagement_correlation'] = corr

    if corr is None:
        results['reason'] = "Missing engagement data."
        logger.warning("Robustness check skipped: Missing engagement data.")
        return results

    # 2. Condition Check
    if corr <= 0.3:
        results['reason'] = f"Correlation ({corr:.4f}) <= 0.3. Robustness check skipped per Spec FR-006."
        logger.warning(results['reason'])
        return results

    # 3. Select Subset and Refit
    try:
        subset_df = select_high_engagement_subset(df, percentile=0.75)
        if len(subset_df) < 130:
            results['reason'] = f"Subset N ({len(subset_df)}) < 130. Robustness check skipped due to low power."
            logger.warning(results['reason'])
            return results

        subset_results = fit_regression_model(subset_df)
        results['subset_model'] = subset_results
        results['status'] = 'completed'

        # 4. Compare with Full Model
        full_model = fit_regression_model(df)
        
        # Compare coefficients for key predictor
        key_pred = 'news_exposure_freq'
        full_coef = full_model['coefficients'].get(key_pred, 0)
        subset_coef = subset_results['coefficients'].get(key_pred, 0)
        
        results['comparison'] = {
            'key_predictor': key_pred,
            'full_sample_coef': full_coef,
            'high_engagement_coef': subset_coef,
            'coef_diff': subset_coef - full_coef,
            'sign_consistent': (full_coef > 0) == (subset_coef > 0)
        }
        
        logger.info("Robustness check completed.")
    except Exception as e:
        results['status'] = 'error'
        results['reason'] = str(e)
        logger.error(f"Robustness check failed: {e}")

    return results

def main():
    """
    Main entry point for robustness checks.
    """
    from config import load_config, ensure_directories
    from pathlib import Path
    import json
    
    config = load_config()
    ensure_directories()
    
    input_path = Path(config['paths']['processed_data']) / 'analysis_data.csv'
    output_path = Path(config['paths']['outputs']) / 'robustness_results.json'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data not found: {input_path}. Run clean.py first.")
    
    df = pd.read_csv(input_path)
    results = run_robustness_check(df)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Robustness results saved to {output_path}")

if __name__ == '__main__':
    main()

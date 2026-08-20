import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy import stats
from config import load_config
from model import fit_regression_model

logger = logging.getLogger(__name__)

def calculate_engagement_correlation(df: pd.DataFrame) -> float:
    """Calculate correlation between social_media_engagement and news_exposure_freq."""
    if 'social_media_engagement' not in df.columns or 'news_exposure_freq' not in df.columns:
        logger.warning("Columns 'social_media_engagement' or 'news_exposure_freq' not found. Skipping engagement correlation.")
        return 0.0
    
    data = df[['social_media_engagement', 'news_exposure_freq']].dropna()
    if len(data) < 2:
        return 0.0
    
    corr, _ = stats.pearsonr(data['social_media_engagement'], data['news_exposure_freq'])
    logger.info(f"Engagement correlation: {corr:.4f}")
    return corr

def select_high_engagement_subset(df: pd.DataFrame) -> pd.DataFrame:
    """Select the top 25th percentile of social_media_engagement."""
    if 'social_media_engagement' not in df.columns:
        raise ValueError("Column 'social_media_engagement' not found in dataset.")
    
    threshold = df['social_media_engagement'].quantile(0.75)
    subset = df[df['social_media_engagement'] >= threshold].copy()
    logger.info(f"Selected {len(subset)} rows for high-engagement subset (>= {threshold:.2f}).")
    return subset

def run_robustness_check(df: pd.DataFrame) -> Dict[str, Any]:
    """Run the robustness check on the high-engagement subset."""
    logger.info("Starting robustness check...")
    
    # Step 1: Calculate correlation
    corr = calculate_engagement_correlation(df)
    
    results = {
        'engagement_correlation': corr,
        'check_performed': False,
        'subset_results': None,
        'full_results': None
    }
    
    # Step 2: Conditional logic
    if corr > 0.3:
        logger.info("Engagement correlation > 0.3. Performing robustness check.")
        
        # Get full model results first
        try:
            full_results = fit_regression_model(df)
            results['full_results'] = full_results
            results['check_performed'] = True
        except Exception as e:
            logger.error(f"Failed to fit full model: {e}")
            return results
        
        # Select subset
        try:
            subset_df = select_high_engagement_subset(df)
            if len(subset_df) < 30:
                logger.warning(f"Subset size {len(subset_df)} is too small for regression. Skipping subset fit.")
                return results
            
            # Fit model on subset
            subset_results = fit_regression_model(subset_df)
            results['subset_results'] = subset_results
            
            # Compare
            # Compare news_exposure_freq coefficient
            full_coef = full_results['coefficients'].get('news_exposure_freq', 0)
            subset_coef = subset_results['coefficients'].get('news_exposure_freq', 0)
            
            results['comparison'] = {
                'full_coef': full_coef,
                'subset_coef': subset_coef,
                'sign_match': (full_coef > 0) == (subset_coef > 0)
            }
            
        except Exception as e:
            logger.error(f"Robustness check failed: {e}")
    else:
        logger.warning(f"Engagement correlation ({corr:.4f}) <= 0.3. Skipping robustness check.")
    
    return results

def main() -> None:
    """Main entry point for robustness check."""
    config = load_config()
    input_path = Path(config['paths']['processed_data'])
    output_path = Path(config['paths']['robustness_results'])
    
    try:
        df = pd.read_csv(input_path)
        results = run_robustness_check(df)
        
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("Robustness check completed.")
    except Exception as e:
        logger.critical(f"Robustness check failed: {e}")
        raise

if __name__ == "__main__":
    main()

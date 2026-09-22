import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy import stats

from config import load_config, ensure_directories
from model import fit_regression_model

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"ROBUSTNESS: {message}")

def calculate_engagement_correlation(df: pd.DataFrame) -> float:
    """
    Calculate correlation between news_exposure_freq and social_media_engagement.
    """
    _log_step("Calculating engagement correlation")
    if "social_media_engagement" not in df.columns or "news_exposure_freq" not in df.columns:
        logger.warning("Columns for engagement correlation missing. Returning 0.0")
        return 0.0
    
    corr, _ = stats.pearsonr(df["news_exposure_freq"], df["social_media_engagement"])
    return corr

def select_high_engagement_subset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select the top 25th percentile of social_media_engagement.
    Always runs regardless of correlation value (Plan override).
    """
    _log_step("Selecting high engagement subset (top 25%)")
    
    if "social_media_engagement" not in df.columns:
        raise ValueError("Column 'social_media_engagement' not found in dataframe")
    
    # Calculate 75th percentile threshold
    threshold = df["social_media_engagement"].quantile(0.75)
    subset = df[df["social_media_engagement"] >= threshold]
    
    _log_step(f"Subset size: {len(subset)} (threshold: {threshold:.2f})")
    return subset

def run_robustness_check(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run robustness check on high-engagement subset.
    Compares with full model results.
    """
    _log_step("Running robustness check")
    
    # Always run check regardless of correlation value
    logger.info("Always run check regardless of correlation value.")
    
    # Calculate correlation for descriptive purposes
    corr = calculate_engagement_correlation(df)
    logger.info(f"Descriptive: Correlation between engagement and news: {corr:.3f}")
    
    # Select subset
    subset_df = select_high_engagement_subset(df)
    
    # Fit model on full data (assumed to be done previously, but we refit here for comparison)
    # In a real pipeline, we would load the full model results
    # For this task, we assume fit_regression_model is available and works
    try:
        full_results = fit_regression_model(df)
    except Exception as e:
        logger.error(f"Failed to fit full model: {e}")
        full_results = None
    
    # Fit model on subset
    try:
        subset_results = fit_regression_model(subset_df)
    except Exception as e:
        logger.error(f"Failed to fit subset model: {e}")
        subset_results = None
    
    # Compare results
    comparison = {
        "status": "unconditional_run",
        "plan_override": True,
        "full_sample": full_results,
        "high_engagement_subset": subset_results,
        "engagement_correlation": corr
    }
    
    _log_step("Robustness check completed")
    return comparison

def main() -> None:
    """Main entry point for robustness check script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    ensure_directories()
    
    input_path = Path("data/processed/analysis_data.csv")
    output_path = Path("outputs/robustness_results.json")
    
    try:
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        df = pd.read_csv(input_path)
        results = run_robustness_check(df)
        
        # Save results
        import json
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Robustness results saved to {output_path}")
    except Exception as e:
        logger.error(f"Robustness check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()

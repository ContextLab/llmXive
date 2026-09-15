import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy import stats
import json
import sys

# Import from sibling modules as per API surface
from model import fit_regression_model
from config import load_config, ensure_directories, set_seed
from exceptions import PowerLimitationError

logger = logging.getLogger(__name__)

def calculate_engagement_correlation(df: pd.DataFrame) -> float:
    """
    Calculate correlation between social_media_engagement and news_exposure_freq.
    
    Args:
        df: Cleaned dataframe containing both columns.
        
    Returns:
        Pearson correlation coefficient.
    """
    if 'social_media_engagement' not in df.columns or 'news_exposure_freq' not in df.columns:
        logger.warning("Required columns for engagement correlation not found. Returning 0.0.")
        return 0.0
    
    # Drop NaNs for calculation
    valid_data = df[['social_media_engagement', 'news_exposure_freq']].dropna()
    if len(valid_data) < 2:
        logger.warning("Insufficient data for correlation calculation.")
        return 0.0
        
    corr, _ = stats.pearsonr(valid_data['social_media_engagement'], valid_data['news_exposure_freq'])
    return float(corr)

def select_high_engagement_subset(df: pd.DataFrame, percentile: float = 75.0) -> pd.DataFrame:
    """
    Select the top 25th percentile (above 75th percentile) of social_media_engagement.
    
    Args:
        df: Cleaned dataframe.
        percentile: The percentile threshold (default 75.0 for top 25%).
        
    Returns:
        Filtered dataframe.
    """
    if 'social_media_engagement' not in df.columns:
        logger.error("Column 'social_media_engagement' missing from dataframe.")
        raise ValueError("Column 'social_media_engagement' missing.")
    
    threshold = df['social_media_engagement'].quantile(percentile / 100.0)
    subset = df[df['social_media_engagement'] >= threshold].copy()
    logger.info(f"Selected {len(subset)} rows (top 25% engagement) with threshold {threshold:.2f}")
    return subset

def run_robustness_check(config: Dict[str, Any], data_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Re-fit regression on the high-engagement subset and compare with full model.
    
    This implements T026 by:
    1. Loading the processed data.
    2. Checking the engagement correlation (FR-006).
    3. If correlation > 0.3, selecting the high-engagement subset.
    4. Calling fit_regression_model from code/model.py on the subset.
    5. Comparing coefficients and significance with the full model (loaded from outputs/regression_results.json).
    
    Args:
        config: Configuration dictionary.
        data_path: Path to the cleaned data CSV. Defaults to config value.
        
    Returns:
        Dictionary containing full model results, subset model results, and comparison metrics.
    """
    # Set seed for reproducibility
    set_seed(config.get('random_seed', 42))
    
    if data_path is None:
        data_path = Path(config.get('paths', {}).get('processed_data', 'data/processed/analysis_data.csv'))
    
    logger.info(f"Loading processed data from {data_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
        
    df_full = pd.read_csv(data_path)
    logger.info(f"Loaded full dataset: {len(df_full)} rows")
    
    # 1. Calculate correlation
    corr_val = calculate_engagement_correlation(df_full)
    logger.info(f"Correlation between engagement and news exposure: {corr_val:.4f}")
    
    results = {
        "full_model": {},
        "subset_model": {},
        "correlation_engagement_news": corr_val,
        "comparison": {},
        "skipped": False
    }
    
    # 2. Check threshold (FR-006)
    if corr_val <= 0.3:
        logger.warning(f"Correlation {corr_val:.4f} <= 0.3. Skipping robustness check as per FR-006.")
        results["skipped"] = True
        results["comparison"]["reason"] = "Correlation <= 0.3"
        return results
    
    # 3. Select subset
    df_subset = select_high_engagement_subset(df_full)
    if len(df_subset) < 30:
        raise PowerLimitationError(f"Subset size {len(df_subset)} is below power threshold (30). Cannot proceed.")
    
    # 4. Fit regression on subset using the function from model.py
    # The formula is defined in T018: anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender
    formula = "anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender"
    logger.info("Fitting regression model on high-engagement subset...")
    
    try:
        # fit_regression_model expects (df, formula, output_path_optional)
        # We pass None for output_path to avoid overwriting the full model results file
        subset_results = fit_regression_model(df_subset, formula, output_path=None)
        results["subset_model"] = subset_results
    except Exception as e:
        logger.error(f"Failed to fit regression on subset: {e}")
        raise
    
    # 5. Load full model results for comparison
    full_results_path = Path(config.get('paths', {}).get('regression_results', 'outputs/regression_results.json'))
    if not full_results_path.exists():
        logger.warning(f"Full model results not found at {full_results_path}. Skipping comparison.")
        results["comparison"]["reason"] = "Full model results missing"
        return results
        
    with open(full_results_path, 'r') as f:
        full_model_data = json.load(f)
        
    results["full_model"] = full_model_data
    
    # 6. Compare coefficients and significance
    comparison = {}
    
    # Extract coefficients from full model (assuming structure from save_regression_results)
    # Structure expected: {"coefficients": {"variable": {"coef": float, "pvalue": float, ...}}}
    full_coefs = full_model_data.get("coefficients", {})
    subset_coefs = subset_results.get("coefficients", {})
    
    comparison["coefficients_diff"] = {}
    comparison["significance_changes"] = {}
    
    for var in ["news_exposure_freq", "baseline_anxiety", "age", "gender_Male", "gender_Other"]: # Common vars
        if var in full_coefs and var in subset_coefs:
            full_coef = full_coefs[var].get("coef", 0)
            subset_coef = subset_coefs[var].get("coef", 0)
            diff = subset_coef - full_coef
            comparison["coefficients_diff"][var] = {
                "full": full_coef,
                "subset": subset_coef,
                "diff": diff
            }
            
            # Check significance change (p < 0.05)
            full_p = full_coefs[var].get("pvalue", 1.0)
            subset_p = subset_coefs[var].get("pvalue", 1.0)
            
            full_sig = full_p < 0.05
            subset_sig = subset_p < 0.05
            
            if full_sig != subset_sig:
                comparison["significance_changes"][var] = {
                    "full_significant": full_sig,
                    "subset_significant": subset_sig,
                    "full_p": full_p,
                    "subset_p": subset_p
                }
    
    results["comparison"] = comparison
    
    logger.info("Robustness check completed successfully.")
    return results

def main():
    """Entry point for robustness check script."""
    config = load_config()
    ensure_directories(config)
    
    # Setup logging
    from logging_config import setup_logging
    setup_logging(config)
    
    try:
        results = run_robustness_check(config)
        
        # Save results to outputs/robustness_results.json
        output_path = Path(config.get('paths', {}).get('robustness_results', 'outputs/robustness_results.json'))
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Robustness results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Robustness check failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy import stats
from config import load_config, ensure_directories, set_seed
from model import fit_regression_model
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_engagement_correlation(df: pd.DataFrame) -> float:
    """
    Calculate correlation between social_media_engagement and news_exposure_freq.
    Returns 0.0 if either column is missing or data is insufficient.
    """
    if 'social_media_engagement' not in df.columns or 'news_exposure_freq' not in df.columns:
        logger.warning("Required columns for engagement correlation not found.")
        return 0.0
    
    clean_data = df[['social_media_engagement', 'news_exposure_freq']].dropna()
    if len(clean_data) < 3:
        logger.warning("Insufficient data for correlation calculation.")
        return 0.0
    
    corr, _ = stats.pearsonr(clean_data['social_media_engagement'], clean_data['news_exposure_freq'])
    return float(corr)

def select_high_engagement_subset(df: pd.DataFrame, percentile: float = 75.0) -> pd.DataFrame:
    """
    Select the top X percentile of social_media_engagement.
    Default is top 25% (i.e., >= 75th percentile).
    """
    if 'social_media_engagement' not in df.columns:
        raise ValueError("Column 'social_media_engagement' not found in dataset.")
    
    threshold = df['social_media_engagement'].quantile(percentile / 100.0)
    subset = df[df['social_media_engagement'] >= threshold].copy()
    logger.info(f"Selected {len(subset)} rows (top {100 - percentile}% engagement) above threshold {threshold:.2f}")
    return subset

def run_robustness_check(
    full_data_path: str, 
    output_path: str, 
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Re-fit regression on high-engagement subset and compare with full model.
    
    1. Load full data.
    2. Calculate correlation between engagement and news exposure.
    3. If corr > 0.3, select top 25% engagement subset.
    4. Fit regression on subset using fit_regression_model from model.py.
    5. Compare coefficients and significance with full model results (loaded from outputs/regression_results.json).
    6. Save results to output_path.
    """
    config = load_config(config_path)
    set_seed(config.get('random_seed', 42))
    ensure_directories(config)
    
    # Load full data
    df_full = pd.read_csv(full_data_path)
    logger.info(f"Loaded full dataset: {len(df_full)} rows")
    
    # Calculate engagement correlation
    corr_val = calculate_engagement_correlation(df_full)
    logger.info(f"Engagement-Exposure Correlation: {corr_val:.4f}")
    
    results = {
        "engagement_correlation": corr_val,
        "robustness_check_performed": False,
        "full_model": {},
        "subset_model": {},
        "comparison": {}
    }
    
    # Load full model results for comparison
    full_model_file = Path("outputs/regression_results.json")
    if full_model_file.exists():
        with open(full_model_file, 'r') as f:
            results["full_model"] = json.load(f)
    else:
        logger.error(f"Full model results not found at {full_model_file}. Cannot compare.")
        return results
    
    # Conditional check per Spec FR-006
    if corr_val > 0.3:
        logger.info("Correlation > 0.3. Proceeding with robustness check on high-engagement subset.")
        df_subset = select_high_engagement_subset(df_full, percentile=75.0)
        
        if len(df_subset) < 30:
            logger.warning(f"Subset size ({len(df_subset)}) is below power threshold (30). Skipping fit.")
            results["robustness_check_performed"] = False
            results["comparison"]["reason"] = "Subset size below power threshold"
            return results
        
        # Re-fit regression using the shared function from model.py
        logger.info("Re-fitting regression model on high-engagement subset...")
        try:
            subset_model_results = fit_regression_model(df_subset)
            results["robustness_check_performed"] = True
            results["subset_model"] = subset_model_results
            
            # Compare coefficients
            full_coeffs = results["full_model"].get("coefficients", {})
            subset_coeffs = subset_model_results.get("coefficients", {})
            
            comparison = {}
            for var in full_coeffs:
                if var in subset_coeffs:
                    full_coef = full_coeffs[var]
                    subset_coef = subset_coeffs[var]
                    diff = subset_coef - full_coef
                    # Check sign consistency
                    sign_match = (full_coef > 0) == (subset_coef > 0)
                    comparison[var] = {
                        "full_coefficient": full_coef,
                        "subset_coefficient": subset_coef,
                        "difference": diff,
                        "sign_consistent": sign_match
                    }
            
            results["comparison"] = comparison
            logger.info("Robustness check comparison completed.")
            
        except Exception as e:
            logger.error(f"Failed to fit subset model: {e}")
            results["robustness_check_performed"] = False
            results["comparison"]["error"] = str(e)
    else:
        logger.warning(f"Correlation ({corr_val:.4f}) <= 0.3. Skipping robustness check per Spec FR-006.")
        results["robustness_check_performed"] = False
        results["comparison"]["reason"] = "Correlation <= 0.3 threshold"
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Robustness results saved to {output_path}")
    
    return results

def main():
    """Entry point for robustness check script."""
    config = load_config()
    data_path = config.get('processed_data_path', 'data/processed/analysis_data.csv')
    output_path = config.get('robustness_output_path', 'outputs/robustness_results.json')
    
    if not Path(data_path).exists():
        logger.error(f"Input data file not found: {data_path}")
        return
    
    run_robustness_check(data_path, output_path)

if __name__ == "__main__":
    main()
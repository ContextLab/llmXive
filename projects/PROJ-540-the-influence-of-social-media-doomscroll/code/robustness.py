"""
Robustness check module for the Doomscrolling Anxiety Analysis Pipeline.
Implements conditional robustness check per Spec FR-006.
"""
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy import stats
import statsmodels.formula.api as smf
import json

logger = logging.getLogger(__name__)

def calculate_engagement_correlation(df: pd.DataFrame) -> Optional[float]:
    """
    Calculate correlation between social_media_engagement and news_exposure_freq.
    Returns None if variable is missing.
    """
    if 'social_media_engagement' not in df.columns:
        logger.warning("Variable 'social_media_engagement' not found.")
        return None
    
    valid_data = df[['social_media_engagement', 'news_exposure_freq']].dropna()
    
    if len(valid_data) < 2:
        logger.warning("Insufficient data for engagement correlation.")
        return None
    
    try:
        corr, _ = stats.pearsonr(valid_data['social_media_engagement'], valid_data['news_exposure_freq'])
        logger.info(f"Engagement correlation (r): {corr:.4f}")
        return corr
    except Exception as e:
        logger.warning(f"Error calculating engagement correlation: {e}")
        return None

def select_high_engagement_subset(df: pd.DataFrame, percentile: float = 75) -> pd.DataFrame:
    """
    Select top 25th percentile of social_media_engagement.
    """
    if 'social_media_engagement' not in df.columns:
        raise ValueError("Variable 'social_media_engagement' not found.")
    
    threshold = df['social_media_engagement'].quantile(percentile / 100)
    subset = df[df['social_media_engagement'] >= threshold].copy()
    
    logger.info(f"High engagement subset: {len(subset)} rows (threshold: {threshold:.2f})")
    return subset

def run_robustness_check(df: pd.DataFrame, full_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run robustness check per Spec FR-006:
    1. Check for 'social_media_engagement' variable
    2. If r > 0.3: Select top 25th percentile and re-fit model
    3. If r <= 0.3 OR variable missing: SKIP robustness check
    
    Returns results dict with status and comparison.
    """
    logger.info("Running robustness check...")
    
    result = {
        "status": "skipped",
        "reason": None,
        "full_sample": full_results,
        "subset": None,
        "comparison": None
    }
    
    # 1. Check for social_media_engagement variable
    if 'social_media_engagement' not in df.columns:
        result["reason"] = "Variable 'social_media_engagement' not found."
        logger.warning(f"Robustness check skipped: {result['reason']}")
        
        # Save results
        output_path = Path("outputs/robustness_results.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    # 2. Calculate correlation
    r = calculate_engagement_correlation(df)
    
    if r is None:
        result["reason"] = "Could not calculate engagement correlation."
        logger.warning(f"Robustness check skipped: {result['reason']}")
        
        output_path = Path("outputs/robustness_results.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    # 3. Check if r > 0.3
    if r <= 0.3:
        result["reason"] = f"Correlation r ({r:.4f}) <= 0.3"
        logger.warning(f"Robustness check skipped: {result['reason']}")
        
        output_path = Path("outputs/robustness_results.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
    
    # 4. Run robustness check (r > 0.3)
    logger.info(f"Correlation r ({r:.4f}) > 0.3. Running robustness check.")
    
    try:
        # Select high engagement subset
        subset_df = select_high_engagement_subset(df)
        
        if len(subset_df) < 30:
            result["reason"] = f"Subset size ({len(subset_df)}) < 30. Skipping."
            logger.warning(f"Robustness check skipped: {result['reason']}")
            
            output_path = Path("outputs/robustness_results.json")
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            return result
        
        # Re-fit model on subset
        formula = "anxiety_score ~ news_exposure_freq + age + gender"
        # Check if baseline_anxiety should be included
        if 'baseline_anxiety' in df.columns and not full_results.get('validity_checks', {}).get('baseline_anxiety_dropped', False):
            formula = "anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender"
        
        subset_model = smf.ols(formula, data=subset_df).fit()
        
        # Compare coefficients
        full_model_coeffs = full_results.get('regression', {}).get('coefficients', {})
        subset_coeffs = {name: float(param) for name, param in subset_model.params.items()}
        
        comparison = {
            "full_sample_n": len(df),
            "subset_n": len(subset_df),
            "full_sample_coeffs": full_model_coeffs,
            "subset_coeffs": subset_coeffs,
            "coefficient_changes": {}
        }
        
        for key in full_model_coeffs:
            if key in subset_coeffs:
                change = subset_coeffs[key] - full_model_coeffs[key]
                comparison["coefficient_changes"][key] = {
                    "full": full_model_coeffs[key],
                    "subset": subset_coeffs[key],
                    "change": change
                }
        
        result["status"] = "run"
        result["reason"] = f"r = {r:.4f} > 0.3"
        result["subset"] = {
            "n": len(subset_df),
            "model": {
                "rsquared": float(subset_model.rsquared),
                "coefficients": subset_coeffs
            }
        }
        result["comparison"] = comparison
        
        logger.info("Robustness check completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during robustness check: {e}")
        result["status"] = "error"
        result["reason"] = str(e)
    
    # Save results
    output_path = Path("outputs/robustness_results.json")
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result

def main():
    """CLI entry point for robustness check."""
    try:
        input_path = Path("data/processed/analysis_data.csv")
        if not input_path.exists():
            logger.error("No input data found for robustness check.")
            return 1
        
        df = pd.read_csv(input_path)
        
        # Load full results
        full_results_path = Path("outputs/regression_results.json")
        if not full_results_path.exists():
            logger.error("Regression results not found.")
            return 1
        
        with open(full_results_path, 'r') as f:
            full_results = json.load(f)
        
        results = run_robustness_check(df, full_results)
        logger.info(f"Robustness check result: {results['status']}")
        return 0
    except Exception as e:
        logger.error(f"Error during robustness check: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

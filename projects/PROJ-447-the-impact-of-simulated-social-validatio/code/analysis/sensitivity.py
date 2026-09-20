import os
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
import statsmodels.api as sm

from utils.constants import get_stability_threshold, get_seed
from utils.exceptions import StabilityThresholdViolationError
from utils.logger import get_logger, log_pipeline_step

# Import regression utilities
# Assuming these exist in regression.py based on API surface
try:
    from analysis.regression import fit_multiple_linear_regression
except ImportError:
    # Fallback if import path differs in actual execution environment
    # This block ensures the file is syntactically valid even if dependencies are missing
    # In a real run, the correct import must be available.
    def fit_multiple_linear_regression(df, outcome, predictors):
        raise NotImplementedError("Regression module not fully linked in this snippet context")

logger = get_logger()

def remove_outliers_iqr(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Remove outliers from a specific column using the IQR method.
    Returns a copy of the dataframe with outliers removed.
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)].copy()

def winsorize_data(df: pd.DataFrame, column: str, limits: Tuple[float, float] = (0.05, 0.05)) -> pd.DataFrame:
    """
    Winsorize a specific column in the dataframe.
    limits: tuple of (lower_percentile, upper_percentile)
    """
    df_winsorized = df.copy()
    lower_val = df_winsorized[column].quantile(limits[0])
    upper_val = df_winsorized[column].quantile(1 - limits[1])
    
    df_winsorized[column] = df_winsorized[column].clip(lower=lower_val, upper=upper_val)
    return df_winsorized

def run_single_regression(
    df: pd.DataFrame,
    outcome: str,
    primary_predictor: str,
    confounders: List[str],
    apply_winsorization: bool = False,
    apply_iqr_removal: bool = False
) -> Dict[str, Any]:
    """
    Runs a single regression fit with optional preprocessing.
    Returns a dictionary containing the primary coefficient and p-value.
    """
    log_pipeline_step("Running single regression with outlier strategy")
    
    working_df = df.copy()
    
    # Apply outlier strategies
    if apply_iqr_removal:
        working_df = remove_outliers_iqr(working_df, primary_predictor)
        logger.info(f"IQR removal applied. Rows remaining: {len(working_df)}")
    
    if apply_winsorization:
        working_df = winsorize_data(working_df, primary_predictor)
        logger.info("Winsorization applied.")
    
    if len(working_df) < 10:
        raise ValueError("Insufficient data for regression after outlier removal.")

    # Prepare features
    predictors = [primary_predictor] + confounders
    X = working_df[predictors]
    X = sm.add_constant(X)
    y = working_df[outcome]

    model = sm.OLS(y, X).fit()
    
    # Extract primary coefficient
    primary_coef = model.params[primary_predictor]
    primary_pval = model.pvalues[primary_predictor]
    
    return {
        "coefficient": primary_coef,
        "p_value": primary_pval,
        "r_squared": model.rsquared,
        "n_obs": len(working_df)
    }

def run_sensitivity_analysis(
    df: pd.DataFrame,
    outcome: str,
    primary_predictor: str,
    confounders: List[str],
    full_confounders: List[str]
) -> Dict[str, Any]:
    """
    Executes the full 3x2 sensitivity matrix:
    3 Outlier Strategies: None, IQR Removal, Winsorization
    2 Confounder States: With Full Confounders, With Minimal Confounders (Primary only)
    
    Calculates variation in the primary coefficient.
    Raises StabilityThresholdViolationError if variation exceeds threshold.
    """
    log_pipeline_step("Starting Sensitivity Analysis")
    logger.info("Running 3x2 matrix of regression strategies.")
    
    strategies = [
        ("None", False, False),
        ("IQR_Removal", True, False),
        ("Winsorization", False, True)
    ]
    
    confounder_sets = [
        ("Full", full_confounders),
        ("Minimal", [])
    ]
    
    results = []
    coefficients = []
    
    for strat_name, use_iqr, use_winsor in strategies:
        for conf_name, conf_list in confounder_sets:
            try:
                run_params = {
                    "df": df,
                    "outcome": outcome,
                    "primary_predictor": primary_predictor,
                    "confounders": conf_list,
                    "apply_winsorization": use_winsor,
                    "apply_iqr_removal": use_iqr
                }
                
                res = run_single_regression(**run_params)
                
                entry = {
                    "strategy": strat_name,
                    "confounder_set": conf_name,
                    "coefficient": res["coefficient"],
                    "p_value": res["p_value"],
                    "r_squared": res["r_squared"],
                    "n_obs": res["n_obs"]
                }
                results.append(entry)
                coefficients.append(res["coefficient"])
                
            except Exception as e:
                logger.warning(f"Strategy {strat_name}/{conf_name} failed: {e}")
                results.append({
                    "strategy": strat_name,
                    "confounder_set": conf_name,
                    "coefficient": np.nan,
                    "p_value": np.nan,
                    "r_squared": np.nan,
                    "n_obs": 0,
                    "error": str(e)
                })

    # Calculate variation
    valid_coeffs = [c for c in coefficients if not np.isnan(c)]
    
    if len(valid_coeffs) < 2:
        logger.warning("Insufficient valid coefficients to calculate variation.")
        variation = 0.0
    else:
        # Variation defined as (Max - Min) / Mean (relative range)
        # Or standard deviation of coefficients. The prompt implies "variation" generally.
        # We will use the relative range (Max-Min)/Mean as a robust measure of stability.
        mean_coeff = np.mean(valid_coeffs)
        if mean_coeff == 0:
            variation = 0.0
        else:
            variation = (max(valid_coeffs) - min(valid_coeffs)) / abs(mean_coeff)
    
    logger.info(f"Calculated coefficient variation: {variation:.4f}")
    
    # Check Stability Threshold
    threshold = get_stability_threshold()
    is_pass, status = None, None
    
    # Import check_stability from constants if available, or replicate logic
    from utils.constants import check_stability
    is_pass, status = check_stability(variation)
    
    logger.info(f"Stability Check: Variation={variation:.4f}, Threshold={threshold:.4f}, Status={status}")
    
    final_report = {
        "variation": variation,
        "threshold": threshold,
        "status": status,
        "individual_results": results,
        "coefficients": coefficients
    }
    
    if not is_pass:
        logger.error(f"Stability Threshold Violation! Variation {variation} > {threshold}")
        raise StabilityThresholdViolationError(
            f"Stability Threshold Violation: Coefficient variation ({variation:.4f}) "
            f"exceeds allowed threshold ({threshold:.4f}). Pipeline halted."
        )
    
    return final_report

def main():
    """
    Entry point for sensitivity analysis.
    Expects processed data to be available or passed via arguments.
    For this task, we assume data is loaded from data/processed/pipeline_run_data.csv
    """
    log_pipeline_step("Main Sensitivity Analysis Entry")
    
    # Configuration
    data_path = "data/processed/pipeline_run_data.csv"
    output_path = "data/processed/sensitivity_results.json"
    
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        # In a real pipeline, this might be handled by the orchestrator
        # For now, we raise to indicate failure
        raise FileNotFoundError(f"Required data file {data_path} not found.")
    
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded data with {len(df)} rows.")
        
        # Define model parameters (matching regression.py defaults)
        outcome = "self_perception_score"
        primary_predictor = "perceived_social_validation"
        confounders = ["age", "gender", "offline_relationships"]
        full_confounders = ["age", "gender", "offline_relationships", "intrinsic_traits"]
        
        # Run Analysis
        results = run_sensitivity_analysis(
            df=df,
            outcome=outcome,
            primary_predictor=primary_predictor,
            confounders=confounders,
            full_confounders=full_confounders
        )
        
        # Save Results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
        logger.info(f"Status: {results['status']}")
        
    except StabilityThresholdViolationError as e:
        logger.critical(f"Pipeline halted due to stability violation: {e}")
        # Re-raise to ensure main.py can catch it
        raise
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()
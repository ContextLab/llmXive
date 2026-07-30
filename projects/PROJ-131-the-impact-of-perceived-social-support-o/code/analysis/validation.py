import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_analysis_cohort(cohort_path: str) -> pd.DataFrame:
    """
    Load the analysis cohort CSV.
    
    Args:
        cohort_path: Path to the analysis_cohort.csv file.
        
    Returns:
        DataFrame containing the analysis cohort.
        
    Raises:
        FileNotFoundError: If the cohort file does not exist.
        ValueError: If the file is empty or cannot be parsed.
    """
    path = Path(cohort_path)
    if not path.exists():
        raise FileNotFoundError(f"Cohort file not found: {cohort_path}")
    
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("Cohort file is empty.")
    
    logger.info(f"Loaded analysis cohort with {len(df)} rows and {len(df.columns)} columns.")
    return df

def check_harassment_variance(df: pd.DataFrame, col_name: str = 'harassment_severity', 
                              min_sd: float = 0.5, min_n: int = 30) -> Tuple[bool, Dict[str, Any]]:
    """
    Check variance of Harassment Exposure.
    
    Requirement: SD > 0.5 and N > 30.
    
    Args:
        df: The analysis cohort DataFrame.
        col_name: Name of the harassment severity column.
        min_sd: Minimum required standard deviation.
        min_n: Minimum required number of non-null observations.
        
    Returns:
        Tuple of (passed: bool, details: dict)
    """
    if col_name not in df.columns:
        logger.error(f"Column '{col_name}' not found in cohort. Cannot check variance.")
        return False, {"error": f"Column '{col_name}' missing", "sd": None, "n": 0}

    series = df[col_name].dropna()
    n = len(series)
    sd = series.std() if n > 1 else 0.0
    
    passed = (sd > min_sd) and (n > min_n)
    
    details = {
        "column": col_name,
        "n": n,
        "sd": sd,
        "min_sd": min_sd,
        "min_n": min_n,
        "passed": passed
    }
    
    if not passed:
        if sd <= min_sd:
            logger.warning(f"Variance check failed: SD ({sd:.4f}) <= {min_sd} for '{col_name}'.")
        if n <= min_n:
            logger.warning(f"Sample size check failed: N ({n}) <= {min_n} for '{col_name}'.")
    else:
        logger.info(f"Variance check passed for '{col_name}': N={n}, SD={sd:.4f}.")
        
    return passed, details

def check_vif(df: pd.DataFrame, 
              predictors: List[str], 
              max_vif: float = 5.0) -> Tuple[bool, Dict[str, Any]]:
    """
    Compute VIF for the model matrix and ensure VIF < 5.
    
    Args:
        df: The analysis cohort DataFrame.
        predictors: List of predictor column names to check.
        max_vif: Maximum allowed VIF value.
        
    Returns:
        Tuple of (passed: bool, vif_results: dict)
    """
    # Prepare model matrix: drop rows with NaN in predictors
    matrix_cols = predictors
    # Ensure all predictors exist
    missing_cols = [c for c in matrix_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing predictor columns for VIF check: {missing_cols}")
        return False, {"error": f"Missing columns: {missing_cols}", "vifs": {}}

    model_df = df[matrix_cols].dropna()
    
    if model_df.empty:
        logger.error("Model matrix is empty after dropping NaNs. Cannot compute VIF.")
        return False, {"error": "Empty model matrix", "vifs": {}}

    # Add constant for intercept if not present (statsmodels usually requires it for VIF)
    # However, VIF calculation often drops the constant or treats it separately.
    # We will add a constant column named 'const' to the DataFrame for the calculation
    X = model_df.copy()
    X['const'] = 1.0
    
    # Calculate VIF for each feature (excluding the constant)
    vif_data = {}
    max_observed_vif = 0.0
    
    logger.info("Computing Variance Inflation Factors (VIF)...")
    for i, col in enumerate(matrix_cols):
        try:
            # VIF formula: 1 / (1 - R^2) where R^2 is from regressing col against all other cols
            # statsmodels function handles this
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
            if vif > max_observed_vif:
                max_observed_vif = vif
        except Exception as e:
            logger.error(f"Error computing VIF for {col}: {e}")
            vif_data[col] = float('inf')
            max_observed_vif = float('inf')

    passed = max_observed_vif < max_vif
    
    result = {
        "vifs": vif_data,
        "max_vif": max_observed_vif,
        "threshold": max_vif,
        "passed": passed
    }
    
    if not passed:
        logger.warning(f"VIF check failed. Max VIF: {max_observed_vif:.2f} (Threshold: {max_vif}).")
        # Identify which variables are problematic
        problematic = [k for k, v in vif_data.items() if v >= max_vif]
        logger.warning(f"Problematic variables: {problematic}")
    else:
        logger.info(f"VIF check passed. Max VIF: {max_observed_vif:.2f}.")
        
    return passed, result

def validate_analysis_cohort(cohort_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Main validation function for the analysis cohort.
    
    Performs:
    1. Check variance of Harassment Exposure (SD > 0.5, N > 30).
    2. Compute VIF for the model matrix (social_support, harassment_exposure, interaction, covariates).
    
    The pipeline proceeds only if variance criteria are met. VIF warnings are logged but 
    do not halt the pipeline unless specified otherwise (here we return status).
    
    Args:
        cohort_path: Path to analysis_cohort.csv.
        
    Returns:
        Tuple of (is_valid: bool, summary: dict)
    """
    logger.info("Starting analysis cohort validation (T015)...")
    
    # 1. Load Data
    try:
        df = load_analysis_cohort(cohort_path)
    except Exception as e:
        logger.error(f"Failed to load cohort: {e}")
        return False, {"error": str(e)}

    # 2. Check Harassment Variance
    # Note: Task description mentions 'harassment_exposure' in VIF but 'harassment_severity' in variance check.
    # We assume the column name in the dataset is 'harassment_severity' based on T013/T014 context.
    # If the column is named differently, adjust here.
    var_check_col = 'harassment_severity'
    var_passed, var_details = check_harassment_variance(df, col_name=var_check_col)
    
    if not var_passed:
        logger.error("Variance check failed. Pipeline cannot proceed.")
        return False, {
            "valid": False,
            "variance_check": var_details,
            "vif_check": None,
            "reason": "Variance criteria not met"
        }

    # 3. Check VIF
    # Construct the list of predictors as per task description:
    # 'social_support', 'harassment_exposure' (assume 'harassment_severity'), interaction, covariates.
    # Since interaction is derived, VIF is typically checked on the base predictors + interaction if included.
    # However, standard VIF practice often checks the base variables before creating the interaction to avoid 
    # perfect multicollinearity issues if not centered, or checks the full model matrix.
    # We will check the base predictors + interaction term.
    # Assuming interaction column is named 'social_support_x_harassment_severity' or similar.
    # If it doesn't exist, we check the base predictors.
    
    base_predictors = ['social_support', 'harassment_severity']
    # Check if interaction exists, if so add it. If not, we might need to create it or just check base.
    # Task says: "model matrix (social_support, harassment_exposure, interaction, plus covariates)"
    # We will check base predictors first. If interaction column exists, add it.
    interaction_col = None
    # Common naming conventions
    for candidate in ['social_support_x_harassment_severity', 'interaction', 'social_support:harassment_severity']:
        if candidate in df.columns:
            interaction_col = candidate
            break
    
    if interaction_col:
        model_predictors = base_predictors + [interaction_col]
    else:
        model_predictors = base_predictors
        logger.warning("Interaction term not found in cohort. Checking VIF for base predictors only.")

    # Add covariates if they exist in the cohort and are relevant (e.g., age, gender, education, income)
    # We will dynamically add common covariates if they exist to be thorough.
    covariates = ['age', 'gender', 'education', 'income']
    existing_covariates = [c for c in covariates if c in df.columns]
    model_predictors.extend(existing_covariates)
    
    vif_passed, vif_details = check_vif(df, predictors=model_predictors)
    
    # 4. Final Decision
    # Pipeline proceeds only if variance criteria are met (already checked above).
    # VIF < 5 is a recommendation/warning in this context unless specified as a hard stop.
    # The task says: "Log warnings if any check fails; the pipeline proceeds only if variance criteria are met."
    # So VIF failure does not stop the pipeline, but variance failure does.
    
    is_valid = var_passed
    
    summary = {
        "valid": is_valid,
        "variance_check": var_details,
        "vif_check": vif_details,
        "message": "Validation completed."
    }
    
    if not vif_passed:
        summary["message"] += " VIF threshold exceeded, but pipeline proceeds as variance criteria are met."
    
    logger.info(f"Validation complete. Valid: {is_valid}")
    return is_valid, summary

def main():
    """
    Entry point for T015 validation script.
    Expects `data/results/analysis_cohort.csv` to exist.
    """
    cohort_path = "data/results/analysis_cohort.csv"
    
    if not Path(cohort_path).exists():
        logger.error(f"Cohort file {cohort_path} does not exist. Run T014 first.")
        return 1
    
    try:
        is_valid, summary = validate_analysis_cohort(cohort_path)
        
        # Log summary
        logger.info(f"Variance Check: {summary['variance_check']}")
        if summary['vif_check']:
            logger.info(f"VIF Check: {summary['vif_check']}")
        
        if is_valid:
            logger.info("Cohort validation PASSED. Proceeding to save (T016).")
            return 0
        else:
            logger.error("Cohort validation FAILED. Stopping pipeline.")
            return 1
            
    except Exception as e:
        logger.exception(f"Validation failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
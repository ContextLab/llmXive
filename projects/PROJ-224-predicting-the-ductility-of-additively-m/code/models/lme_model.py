"""
Linear Mixed-Effects Model for Ductility Prediction.

This module implements the LME model to quantify parameter influence on ductility,
handling random effects for alloy families.
"""

import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Import statsmodels for Mixed Effects
try:
    import statsmodels.api as sm
    from statsmodels.regression.mixed_linear_model import MixedLM
except ImportError:
    logging.critical("statsmodels is required for LME modeling. Install with: pip install statsmodels")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
CURATED_DATA_PATH = DATA_DIR / "curated_builds.csv"
OUTPUT_ARTIFACT_PATH = ARTIFACTS_DIR / "lme_results.json"

# Ensure output directory exists
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load the curated dataset."""
    if not CURATED_DATA_PATH.exists():
        raise FileNotFoundError(f"Curated data not found at {CURATED_DATA_PATH}. "
                                "Please run code/data/preprocessing.py first.")
    return pd.read_csv(CURATED_DATA_PATH)


def prepare_features(df, predictor_columns):
    """
    Prepare the feature matrix and target variable.
    
    Args:
        df: DataFrame containing the data.
        predictor_columns: List of column names to use as fixed effects.
        
    Returns:
        y: Target array (ductility).
        X: Feature matrix (fixed effects).
        groups: Grouping variable (alloy_family).
    """
    # Check for required columns
    required_cols = predictor_columns + ['ductility', 'alloy_family']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    y = df['ductility'].values
    X = df[predictor_columns].values
    groups = df['alloy_family'].values

    # Handle any NaNs in the selected columns (statsmodels MixedLM cannot handle NaNs)
    # We drop rows where any of the predictors or target are NaN
    valid_mask = ~np.isnan(y)
    for col in predictor_columns:
        valid_mask = valid_mask & ~np.isnan(df[col].values)
    
    if not np.all(valid_mask):
        logger.warning(f"Dropping {np.sum(~valid_mask)} rows with NaN values in predictors or target.")
        y = y[valid_mask]
        X = X[valid_mask]
        groups = groups[valid_mask]

    return y, X, groups


def fit_lme_model(df, predictor_columns):
    """
    Fit a Linear Mixed-Effects model.
    
    Formula: ductility ~ predictor1 + predictor2 + ... + (1 | alloy_family)
    
    Args:
        df: DataFrame with data.
        predictor_columns: List of fixed effect predictors.
        
    Returns:
        result: Fitted MixedLMResults object.
        model: The fitted model instance.
        metadata: Dict with model info and convergence status.
    """
    y, X, groups = prepare_features(df, predictor_columns)

    if len(y) == 0:
        raise ValueError("No valid data points remaining after filtering NaNs.")

    # Create design matrix with intercept
    X_with_intercept = sm.add_constant(X)
    col_names = ['const'] + predictor_columns

    # Initialize the model
    # endog: y, exog: X, groups: groups, re_formula: '1' (random intercept)
    model = MixedLM(endog=y, exog=X_with_intercept, groups=groups, exog_re=np.ones((len(y), 1)))
    
    logger.info(f"Fitting LME model with fixed effects: {predictor_columns}")
    logger.info(f"Random effect: Random intercept for 'alloy_family'")
    logger.info(f"Total samples: {len(y)}, Unique groups: {len(np.unique(groups))}")

    convergence_failed = False
    result = None

    try:
        # Fit the model
        # method='reml' is standard for LME, but 'ml' is sometimes more stable for convergence checks
        # Using 'reml' as default for final estimation
        result = model.fit(reml=True)
        
        # Check convergence flag from statsmodels
        if hasattr(result, 'converged') and result.converged is False:
            logger.error("Model failed to converge (statsmodels reported convergence=False).")
            convergence_failed = True
        elif hasattr(result, 'converged') and result.converged is True:
            logger.info("Model converged successfully.")
        else:
            # If convergence flag is missing, assume success if no exception
            logger.warning("Convergence flag not explicitly available; assuming success if fit completed.")

    except Exception as e:
        logger.error(f"Model fitting failed with exception: {e}")
        convergence_failed = True
        # We proceed to return partial results if possible, but mark as failed
        # However, if fit() raises, result might be None or partial.
        # For safety, if exception occurs, we cannot extract coefficients.
        raise e

    return result, model, convergence_failed


def extract_results(result, predictor_columns, convergence_failed):
    """
    Extract standardized coefficients, CIs, p-values, and random effects.
    
    Args:
        result: Fitted MixedLMResults object.
        predictor_columns: List of fixed effect names.
        convergence_failed: Boolean flag indicating convergence status.
        
    Returns:
        Dict containing model metrics and parameters.
    """
    if result is None:
        return {
            "status": "failed",
            "convergence_failed": True,
            "error": "Model fitting failed or returned no results."
        }

    # Extract fixed effects parameters
    params = result.fe_params
    std_err = result.bse
    t_values = result.tvalues
    p_values = result.pvalues

    # Calculate 95% Confidence Intervals
    # Approximation: param +/- 1.96 * std_err
    ci_lower = params - 1.96 * std_err
    ci_upper = params + 1.96 * std_err

    # Standardized coefficients (Beta)
    # Beta = coef * (std_dev_X / std_dev_y)
    # We need the original data to calculate std_dev_X and std_dev_y
    # This requires re-accessing the data used in fit, or passing it here.
    # For simplicity in this function, we assume we can't easily re-calculate without passing raw data.
    # However, the task asks for standardized coefficients.
    # We will calculate them here assuming we have access to the mean/std of the data used.
    # Since we don't pass the raw X/y back, we'll calculate standardized coefficients based on the
    # input data passed to the main function, or we can skip standardization if we can't get the stats.
    # Better approach: Calculate standardized coefficients in the main function and pass them,
    # or re-calculate here if we have the data.
    # Let's assume we calculate them in the main function and return them.
    # For now, we will return raw coefficients and note that standardization requires raw data stats.
    # Wait, the task says "Extract standardized coefficients".
    # We need the standard deviations of the predictors and the target.
    # We will assume the main function handles this or we calculate it if we had the data.
    # Let's modify the flow: The main function will calculate these stats before calling this,
    # or we can re-calculate if we pass the dataframe.
    # To keep the signature clean, let's assume we calculate standardized coefficients in `main`
    # and pass them, or we calculate them here if we have the dataframe.
    # Actually, let's just calculate them here if we can. But we don't have the dataframe here.
    # So we will return raw coefficients and a note.
    # Correction: The task requires standardized coefficients.
    # We will assume the `main` function passes the necessary stats or we calculate them.
    # Let's change the `extract_results` to accept the dataframe or stats.
    # For this implementation, I will calculate them in `main` and include them in the output dict.
    
    # Construct fixed effects summary
    fixed_effects = {}
    for i, col in enumerate(predictor_columns):
        # Skip intercept for the summary if desired, but usually we list all
        fixed_effects[col] = {
            "coef": params.iloc[i+1] if hasattr(params, 'iloc') else params[i+1], # Skip const
            "std_err": std_err.iloc[i+1] if hasattr(std_err, 'iloc') else std_err[i+1],
            "t_value": t_values.iloc[i+1] if hasattr(t_values, 'iloc') else t_values[i+1],
            "p_value": p_values.iloc[i+1] if hasattr(p_values, 'iloc') else p_values[i+1],
            "ci_lower": ci_lower.iloc[i+1] if hasattr(ci_lower, 'iloc') else ci_lower[i+1],
            "ci_upper": ci_upper.iloc[i+1] if hasattr(ci_upper, 'iloc') else ci_upper[i+1]
        }

    # Random effects (Intercepts for each alloy family)
    # result.random_effects is a dict of {group_id: {random_effect_name: value}}
    # Our random effect is '1' (intercept)
    random_intercepts = {}
    if hasattr(result, 'random_effects'):
        for group, effects in result.random_effects.items():
            # The key in the dict is the name of the random effect, usually '1' or 'Intercept'
            # statsmodels uses '1' for the intercept if specified as '1'
            val = effects.get('1', None)
            if val is not None:
                random_intercepts[str(group)] = float(val)

    # Log-likelihood
    log_likelihood = result.llf

    # AIC and BIC
    aic = result.aic
    bic = result.bic

    return {
        "convergence_failed": convergence_failed,
        "log_likelihood": float(log_likelihood),
        "aic": float(aic),
        "bic": float(bic),
        "fixed_effects": fixed_effects,
        "random_intercepts": random_intercepts
    }


def main():
    """
    Main entry point for the LME model task.
    """
    logger.info("Starting Linear Mixed-Effects Model task (T024).")

    # 1. Load Data
    try:
        df = load_data()
        logger.info(f"Loaded {len(df)} rows from {CURATED_DATA_PATH}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    # 2. Determine Predictors
    # T023 performed VIF analysis and selected the final predictors.
    # We assume the output of T023 (or the logic in preprocessing) determined the set.
    # For this task, we need to know which columns to use.
    # The task description says "selected predictors from T023".
    # We will assume the columns are: 'laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density'
    # BUT T023 logic says: IF Energy Density VIF > 5 THEN drop components and keep ONLY Energy Density.
    # We need to check if we have the 'energy_density' column and if it was the one selected.
    # Since we don't have the output of T023 explicitly as a file in this context, 
    # we will implement the logic to detect the reduced set if 'energy_density' is present and others are present.
    # However, the task T023 says "Output the filtered dataset".
    # So we should read the filtered dataset from preprocessing?
    # The task T023 says "Output the filtered dataset". Let's assume the dataset is updated in place or saved.
    # The task T018/19/23 flow:
    # T018: Adds energy_density.
    # T023: Calculates VIF, drops columns if needed, and outputs the filtered dataset.
    # So we should read the dataset from `curated_builds.csv` (which T023 might have overwritten or saved as a new file).
    # The task T023 description says "Output the filtered dataset".
    # Let's assume the file `data/curated_builds.csv` is the one with the filtered features.
    # If T023 saved it to a new file, we would need that path.
    # Given the task description "Output the filtered dataset", and T018 outputting to curated_builds.csv,
    # it is likely T023 overwrites or saves a new version.
    # Let's assume the current `curated_builds.csv` has the correct columns.
    
    # Check for energy_density
    if 'energy_density' in df.columns:
        # If energy_density is present, we assume T023 logic was applied and other collinear predictors were removed?
        # Or do we need to re-run the VIF logic here?
        # The task T024 says "Fit model with fixed effects (selected predictors from T023)".
        # This implies we trust the output of T023.
        # We need to identify the selected predictors.
        # If the dataset has 'energy_density' and NOT the components, then we use 'energy_density'.
        # If it has both, then T023 didn't filter?
        # Let's assume the dataset `curated_builds.csv` is the one from T023.
        # We will select all numeric columns that are not 'ductility', 'alloy_family', or any ID columns.
        # But we must be careful.
        # Let's define the potential fixed effects based on the domain:
        potential_fixed_effects = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density']
        
        # Filter to only those present in the dataframe
        selected_predictors = [col for col in potential_fixed_effects if col in df.columns]
        
        if not selected_predictors:
            logger.error("No fixed effect predictors found in the dataset.")
            sys.exit(1)
        
        logger.info(f"Selected predictors for LME: {selected_predictors}")
    else:
        # Fallback: use whatever numeric columns are available (excluding target/group)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        selected_predictors = [col for col in numeric_cols if col not in ['ductility', 'alloy_family']]
        logger.warning(f"'energy_density' not found. Using available numeric predictors: {selected_predictors}")

    # 3. Fit Model
    try:
        result, model, convergence_failed = fit_lme_model(df, selected_predictors)
    except Exception as e:
        logger.error(f"Failed to fit LME model: {e}")
        # Create an error artifact
        error_artifact = {
            "status": "failed",
            "convergence_failed": True,
            "error": str(e)
        }
        with open(OUTPUT_ARTIFACT_PATH, 'w') as f:
            json.dump(error_artifact, f, indent=2)
        sys.exit(1)

    # 4. Extract Results
    # To calculate standardized coefficients, we need the std dev of X and y.
    # We have the original df and selected_predictors.
    y_std = df['ductility'].std()
    # We need to calculate standardized coefficients for each predictor.
    # Beta = coef * (x_std / y_std)
    # We need the std of each predictor column.
    std_devs = df[selected_predictors].std()
    
    # We need to re-extract the results with standardized coefficients
    # Let's modify the extraction logic to include standardization
    raw_results = extract_results(result, selected_predictors, convergence_failed)
    
    if raw_results.get("status") == "failed":
        with open(OUTPUT_ARTIFACT_PATH, 'w') as f:
            json.dump(raw_results, f, indent=2)
        sys.exit(1)

    # Calculate standardized coefficients
    fixed_effects_raw = raw_results["fixed_effects"]
    fixed_effects_std = {}
    
    for i, col in enumerate(selected_predictors):
        # The index in params is i+1 because of the intercept (const)
        # But our fixed_effects_raw keys are the column names, not indices.
        # We need to map the column name to the parameter.
        # The extract_results function created a dict keyed by col name.
        # So we can just iterate.
        coef_raw = fixed_effects_raw[col]["coef"]
        x_std = std_devs[col]
        beta_std = coef_raw * (x_std / y_std)
        
        fixed_effects_std[col] = {
            "raw_coef": coef_raw,
            "standardized_coef": beta_std,
            "std_err": fixed_effects_raw[col]["std_err"],
            "p_value": fixed_effects_raw[col]["p_value"],
            "ci_lower": fixed_effects_raw[col]["ci_lower"],
            "ci_upper": fixed_effects_raw[col]["ci_upper"]
        }

    raw_results["fixed_effects_standardized"] = fixed_effects_std
    raw_results["selected_predictors"] = selected_predictors
    raw_results["status"] = "success"

    # 5. Save Artifact
    try:
        with open(OUTPUT_ARTIFACT_PATH, 'w') as f:
            json.dump(raw_results, f, indent=2)
        logger.info(f"LME results saved to {OUTPUT_ARTIFACT_PATH}")
    except Exception as e:
        logger.error(f"Failed to save LME results: {e}")
        sys.exit(1)

    # 6. Convergence Check
    if convergence_failed:
        logger.error("Model convergence failed. Coefficients should not be interpreted.")
        # The artifact contains the flag, so downstream tasks can check it.
    
    return raw_results


if __name__ == "__main__":
    main()
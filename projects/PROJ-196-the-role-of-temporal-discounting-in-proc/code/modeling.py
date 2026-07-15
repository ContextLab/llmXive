"""
Modeling module for temporal discounting analysis.

Implements hyperbolic model fitting, OLS regression with interaction terms,
and diagnostic calculations.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import zscore
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.formula.api import ols
import warnings
from typing import Dict, List, Tuple, Optional, Any

from config import get_random_state, get_project_root, get_config_value


def hyperbolic_function(delay: np.ndarray, k: float) -> np.ndarray:
    """
    Calculate the value of a delayed reward using the hyperbolic discounting model.
    
    V = A / (1 + k*D)
    
    Args:
        delay: Array of delay times (D)
        k: Discount rate parameter
        
    Returns:
        Discounted values
    """
    return 1.0 / (1.0 + k * delay)


def fit_hyperbolic_model(
    delays: np.ndarray,
    values: np.ndarray,
    participant_id: int,
    random_state: Optional[np.random.RandomState] = None
) -> Dict[str, Any]:
    """
    Fit a hyperbolic discounting model to individual participant data.
    
    Uses scipy.optimize.curve_fit to estimate the discount rate (k) for
    a single participant based on their indifference points across different delays.
    
    Args:
        delays: Array of delay times (D) for each trial
        values: Array of normalized subjective values (V) or indifference points
        participant_id: Unique identifier for the participant
        random_state: Random state object for reproducibility (from get_random_state())
        
    Returns:
        Dictionary containing:
            - participant_id: The participant identifier
            - discount_rate_k: The fitted k parameter
            - success: Boolean indicating if fitting was successful
            - r_squared: Coefficient of determination (if successful)
            - message: Status message
    """
    if random_state is None:
        random_state = get_random_state()
    
    # Filter out any invalid data points (NaN or infinite values)
    valid_mask = np.isfinite(delays) & np.isfinite(values)
    delays_clean = delays[valid_mask]
    values_clean = values[valid_mask]
    
    if len(delays_clean) < 2:
        return {
            "participant_id": participant_id,
            "discount_rate_k": np.nan,
            "success": False,
            "r_squared": np.nan,
            "message": "Insufficient valid data points for fitting"
        }
    
    # Initial guess for k (typically small positive number)
    # Use a random initialization within a reasonable range to avoid local minima
    k_init = random_state.uniform(0.001, 0.1)
    
    try:
        # Define bounds for k (must be positive)
        # Lower bound slightly above 0 to avoid division by zero
        popt, pcov = curve_fit(
            hyperbolic_function,
            delays_clean,
            values_clean,
            p0=[k_init],
            bounds=(0, np.inf),
            maxfev=2000
        )
        
        k_fitted = popt[0]
        
        # Calculate R-squared
        residuals = values_clean - hyperbolic_function(delays_clean, k_fitted)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((values_clean - np.mean(values_clean))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Ensure k is reasonable (not extremely large)
        if k_fitted > 1000:
            return {
                "participant_id": participant_id,
                "discount_rate_k": np.nan,
                "success": False,
                "r_squared": np.nan,
                "message": "Fitted k value exceeds reasonable threshold"
            }
        
        return {
            "participant_id": participant_id,
            "discount_rate_k": k_fitted,
            "success": True,
            "r_squared": r_squared,
            "message": "Model fitted successfully"
        }
        
    except RuntimeError as e:
        return {
            "participant_id": participant_id,
            "discount_rate_k": np.nan,
            "success": False,
            "r_squared": np.nan,
            "message": f"Fitting failed: {str(e)}"
        }
    except Exception as e:
        return {
            "participant_id": participant_id,
            "discount_rate_k": np.nan,
            "success": False,
            "r_squared": np.nan,
            "message": f"Unexpected error: {str(e)}"
        }


def load_and_prepare_data(
    filepath: str,
    required_columns: List[str] = None
) -> pd.DataFrame:
    """
    Load and prepare the harmonized dataset for analysis.
    
    Args:
        filepath: Path to the parquet file containing harmonized data
        required_columns: List of columns that must be present
        
    Returns:
        Prepared DataFrame
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    
    df = pd.read_parquet(filepath)
    
    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
    
    # Drop rows with NaN in critical columns for modeling
    critical_cols = ['discount_rate_k', 'procrastination_score', 'wm_accuracy']
    df = df.dropna(subset=critical_cols)
    
    return df


def transform_and_center(
    df: pd.DataFrame,
    log_k: bool = True,
    center: bool = True
) -> pd.DataFrame:
    """
    Transform and center predictors for regression analysis.
    
    Args:
        df: Input DataFrame
        log_k: Whether to apply log transformation to discount_rate_k
        center: Whether to mean-center continuous predictors
        
    Returns:
        Transformed DataFrame with new columns:
            - log_k: log-transformed discount rate (if log_k=True)
            - procrastination_score_centered: centered procrastination score
            - wm_accuracy_centered: centered WM accuracy
            - interaction: interaction term (log_k * wm_accuracy)
    """
    df_transformed = df.copy()
    
    # Log transform discount rate
    if log_k:
        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        df_transformed['log_k'] = np.log(df_transformed['discount_rate_k'] + epsilon)
    else:
        df_transformed['log_k'] = df_transformed['discount_rate_k']
    
    # Mean-center continuous predictors
    if center:
        df_transformed['procrastination_score_centered'] = (
            df_transformed['procrastination_score'] - df_transformed['procrastination_score'].mean()
        )
        df_transformed['wm_accuracy_centered'] = (
            df_transformed['wm_accuracy'] - df_transformed['wm_accuracy'].mean()
        )
    else:
        df_transformed['procrastination_score_centered'] = df_transformed['procrastination_score']
        df_transformed['wm_accuracy_centered'] = df_transformed['wm_accuracy']
    
    # Create interaction term
    df_transformed['interaction'] = (
        df_transformed['log_k'] * df_transformed['wm_accuracy_centered']
    )
    
    return df_transformed


def calculate_vif(df: pd.DataFrame, formula: str) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for predictors in a regression model.
    
    Args:
        df: DataFrame containing the variables
        formula: Statsmodels formula string (e.g., "y ~ x1 + x2")
        
    Returns:
        Dictionary mapping variable names to their VIF values
    """
    # Parse formula to get predictors
    # Simple parsing: split by '+' and clean up
    parts = formula.split('~')
    if len(parts) != 2:
        raise ValueError("Invalid formula format")
    
    predictors = parts[1].strip().split('+')
    predictors = [p.strip() for p in predictors if p.strip()]
    
    # Create design matrix
    from patsy import dmatrix
    y, X = dmatrix(formula, data=df, return_type='dataframe')
    
    # Add intercept column for VIF calculation
    X = X.assign(intercept=1)
    
    vif_dict = {}
    for col in X.columns:
        if col == 'intercept':
            continue
        try:
            vif = variance_inflation_factor(X.values, list(X.columns).index(col))
            vif_dict[col] = vif
        except Exception:
            vif_dict[col] = np.nan
    
    return vif_dict


def run_regression(
    df: pd.DataFrame,
    config_path: str = None
) -> Dict[str, Any]:
    """
    Run OLS regression with interaction term to test primary hypothesis.
    
    Hypothesis: The effect of discount rate on procrastination is moderated by WM capacity.
    Model: procrastination_score ~ log_k * wm_accuracy + covariates
    
    Args:
        df: Prepared DataFrame with transformed variables
        config_path: Path to model_config.json (optional, for reduced model)
        
    Returns:
        Dictionary containing regression results
    """
    # Check for reduced model config
    reduced_model = False
    excluded_covariates = []
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            reduced_model = config.get('reduced_model', False)
            excluded_covariates = config.get('excluded_covariates', [])
    
    # Build formula
    base_predictors = ['log_k', 'wm_accuracy_centered', 'interaction']
    
    # Add covariates if not excluded
    covariates = []
    if not reduced_model:
        # Add age, education if available and not excluded
        if 'age' in df.columns and 'age' not in excluded_covariates:
            covariates.append('age')
        if 'education' in df.columns and 'education' not in excluded_covariates:
            covariates.append('education')
    
    all_predictors = base_predictors + covariates
    formula = f"procrastination_score_centered ~ {' + '.join(all_predictors)}"
    
    # Fit model
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ols(formula, data=df).fit()
    
    # Extract results
    results = {
        "formula": formula,
        "n_obs": model.nobs,
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "aic": model.aic,
        "bic": model.bic,
        "coefficients": {},
        "p_values": {},
        "vif": calculate_vif(df, formula)
    }
    
    # Extract coefficient for interaction term
    for param in model.params.index:
        if param != 'Intercept':
            results["coefficients"][param] = float(model.params[param])
            results["p_values"][param] = float(model.pvalues[param])
    
    # Check for significant interaction
    interaction_p = results["p_values"].get('interaction', 1.0)
    results["interaction_significant"] = interaction_p < 0.05
    results["interaction_p_value"] = interaction_p
    
    return results


def save_regression_results(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save regression results to JSON file.
    
    Args:
        results: Dictionary of regression results
        output_path: Path to output JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


def run_full_analysis(
    data_path: str,
    output_path: str,
    config_path: str = None
) -> Dict[str, Any]:
    """
    Run the full analysis pipeline: load, transform, regress, save.
    
    Args:
        data_path: Path to harmonized dataset
        output_path: Path to save regression results
        config_path: Path to model config (optional)
        
    Returns:
        Regression results dictionary
    """
    # Load data
    df = load_and_prepare_data(data_path)
    
    # Transform and center
    df_transformed = transform_and_center(df)
    
    # Run regression
    results = run_regression(df_transformed, config_path)
    
    # Save results
    save_regression_results(results, output_path)
    
    return results
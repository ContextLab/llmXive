"""
Modeling module for temporal discounting analysis.

Implements hyperbolic model fitting, regression analysis, and data preparation.
"""

import os
import sys
import json
import time
import logging
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import zscore
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.formula.api import ols
from typing import Dict, Any, Tuple, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import config utilities
from config import get_project_root, get_config, get_random_state

def hyperbolic_function(delay: np.ndarray, k: float, V: float = 1.0) -> np.ndarray:
    """
    Calculate the subjective value of a delayed reward using the hyperbolic discounting model.
    
    V(t) = V / (1 + k * t)
    
    Args:
        delay: Array of delay times (t).
        k: Discount rate parameter.
        V: Immediate reward value (default 1.0).
        
    Returns:
        Array of subjective values.
    """
    return V / (1 + k * delay)

def fit_hyperbolic_model(delays: np.ndarray, values: np.ndarray, 
                         participant_id: str) -> Tuple[Optional[float], str]:
    """
    Fit a hyperbolic model to a participant's data.
    
    Args:
        delays: Array of delay times.
        values: Array of observed subjective values or choices.
        participant_id: ID of the participant.
        
    Returns:
        Tuple of (k_value or None, reason_code).
        reason_code can be: "SUCCESS", "NO_SOLUTION", "CONVERGENCE_FAIL", "INVALID_RANGE"
    """
    try:
        # Validate input ranges
        if np.any(delays < 0) or np.any(values < 0):
            return None, "INVALID_RANGE"
        
        if len(delays) < 3:
            return None, "NO_SOLUTION"
        
        # Initial guess for k (discount rate)
        k_guess = 0.05
        
        # Bounds for k (must be positive)
        bounds = (0, np.inf)
        
        try:
            popt, pcov = curve_fit(
                hyperbolic_function, 
                delays, 
                values, 
                p0=[k_guess], 
                bounds=bounds,
                maxfev=10000
            )
            
            k_value = popt[0]
            
            # Check for reasonable k value (not too large or small)
            if not np.isfinite(k_value) or k_value < 0 or k_value > 10:
                return None, "CONVERGENCE_FAIL"
            
            return k_value, "SUCCESS"
            
        except RuntimeError:
            return None, "CONVERGENCE_FAIL"
            
    except Exception as e:
        logger.warning(f"Error fitting model for participant {participant_id}: {e}")
        return None, "NO_SOLUTION"

def load_and_prepare_data() -> Tuple[pd.DataFrame, bool]:
    """
    Load the harmonized dataset and prepare it for analysis.
    
    Returns:
        Tuple of (DataFrame, reduced_model_flag).
        reduced_model_flag indicates if covariates were excluded.
    """
    project_root = get_project_root()
    data_path = os.path.join(project_root, "data", "processed", "harmonized_dataset.parquet")
    config_path = os.path.join(project_root, "data", "processed", "model_config.json")
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_parquet(data_path)
    
    # Load model config to check for excluded covariates
    reduced_model = False
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            reduced_model = config.get('reduced_model', False)
    
    # Filter out excluded participants
    excluded_path = os.path.join(project_root, "data", "processed", "excluded_participants.csv")
    if os.path.exists(excluded_path):
        excluded_df = pd.read_csv(excluded_path)
        excluded_ids = excluded_df['participant_id'].tolist()
        df = df[~df['participant_id'].isin(excluded_ids)]
    
    logger.info(f"Loaded {len(df)} participants for analysis")
    return df, reduced_model

def transform_and_center(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply log transformation to discount rate and mean-center predictors.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with transformed and centered variables.
    """
    df = df.copy()
    
    # Log transform discount rate (add small epsilon to avoid log(0))
    df['log_k'] = np.log(df['discount_rate_k'] + 1e-6)
    
    # Mean-center continuous predictors
    center_vars = ['log_k', 'wm_accuracy', 'wm_rt', 'age', 'procrastination_score']
    for var in center_vars:
        if var in df.columns:
            df[f'{var}_centered'] = zscore(df[var])
    
    # Save centered data
    project_root = get_project_root()
    output_path = os.path.join(project_root, "data", "processed", "centered_data.parquet")
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved centered data to {output_path}")
    
    return df

def calculate_vif(df: pd.DataFrame, formula: str) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors for predictors in a formula.
    
    Args:
        df: DataFrame with data.
        formula: Regression formula string.
        
    Returns:
        Dictionary mapping variable names to VIF scores.
    """
    # Parse formula to get predictor variables
    # Simple parsing for our specific formula structure
    predictors = []
    if '+' in formula:
        parts = formula.split('+')
        for part in parts:
            part = part.strip().split('~')[0].strip() if '~' in part else part
            if part and part != 'Intercept':
                # Handle interaction terms
                if ':' in part:
                    # Split interaction into individual terms
                    for term in part.split(':'):
                        term = term.strip()
                        if term and term not in predictors:
                            predictors.append(term)
                else:
                    if part and part not in predictors:
                        predictors.append(part)
    elif '~' in formula:
        rhs = formula.split('~')[1].strip()
        if '+' in rhs:
            for term in rhs.split('+'):
                term = term.strip()
                if term and term not in predictors:
                    predictors.append(term)
        else:
            if rhs and rhs not in predictors:
                predictors.append(rhs)
    
    # Remove response variable if accidentally included
    response = formula.split('~')[0].strip()
    if response in predictors:
        predictors.remove(response)
    
    vif_data = {}
    X = df[predictors].dropna()
    
    if len(X) == 0:
        return {}
    
    # Add intercept column
    X_with_intercept = sm.add_constant(X)
    
    for col in X_with_intercept.columns:
        try:
            vif = variance_inflation_factor(X_with_intercept.values, X_with_intercept.columns.get_loc(col))
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
    
    return vif_data

def run_regression(df: pd.DataFrame, reduced_model: bool) -> Dict[str, Any]:
    """
    Run the OLS regression with interaction term.
    
    Args:
        df: Prepared DataFrame.
        reduced_model: Flag indicating if covariates were excluded.
        
    Returns:
        Dictionary with regression results.
    """
    import statsmodels.api as sm
    
    # Construct formula based on model config
    base_formula = "procrastination_score ~ log_k_centered + wm_accuracy_centered + log_k_centered:wm_accuracy_centered"
    
    # Add covariates if not excluded
    if not reduced_model:
        base_formula += " + age_centered"
    
    logger.info(f"Running regression with formula: {base_formula}")
    
    # Write formula to log
    project_root = get_project_root()
    formula_log_path = os.path.join(project_root, "data", "processed", "regression_formula.log")
    with open(formula_log_path, 'w') as f:
        f.write(base_formula)
    
    # Prepare data for regression
    X = df[['log_k_centered', 'wm_accuracy_centered', 'age_centered']].copy()
    y = df['procrastination_score']
    
    # Create interaction term manually
    X['interaction'] = X['log_k_centered'] * X['wm_accuracy_centered']
    
    # Drop rows with missing values
    X = X.dropna()
    y = y.loc[X.index]
    
    if len(X) < 10:
        raise ValueError("Insufficient data for regression after dropping missing values")
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit model
    model = ols(base_formula, data=df).fit()
    
    # Calculate VIF
    vif_scores = calculate_vif(df, base_formula)
    
    # Extract results
    results = {
        'r_squared': model.rsquared,
        'adj_r_squared': model.rsquared_adj,
        'aic': model.aic,
        'bic': model.bic,
        'coefficients': model.params.to_dict(),
        'p_values': model.pvalues.to_dict(),
        'vif_scores': vif_scores
    }
    
    # Save VIF report
    vif_path = os.path.join(project_root, "data", "processed", "vif_report.json")
    with open(vif_path, 'w') as f:
        json.dump(vif_scores, f, indent=2)
    
    # Save full results
    results_path = os.path.join(project_root, "data", "processed", "regression_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Regression completed successfully")
    return results

def save_interaction_results(results: Dict[str, Any]) -> None:
    """
    Extract and save interaction term results.
    
    Args:
        results: Full regression results dictionary.
    """
    interaction_coef = results['coefficients'].get('log_k_centered:wm_accuracy_centered', 0)
    interaction_p = results['p_values'].get('log_k_centered:wm_accuracy_centered', 1.0)
    
    interaction_data = {
        'coefficient': interaction_coef,
        'p_value': interaction_p,
        'significant': interaction_p < 0.05
    }
    
    project_root = get_project_root()
    output_path = os.path.join(project_root, "data", "processed", "interaction_results.json")
    with open(output_path, 'w') as f:
        json.dump(interaction_data, f, indent=2)
    
    logger.info(f"Interaction results saved to {output_path}")

def update_halt_log_with_exclusions(excluded_count: int, excluded_file_path: str) -> None:
    """
    Update the halt_log.json with exclusion information.
    
    Args:
        excluded_count: Number of participants excluded.
        excluded_file_path: Path to the excluded participants CSV.
    """
    project_root = get_project_root()
    halt_log_path = os.path.join(project_root, "data", "processed", "halt_log.json")
    
    # Load existing halt log or create new one
    if os.path.exists(halt_log_path):
        with open(halt_log_path, 'r') as f:
            halt_log = json.load(f)
    else:
        halt_log = {}
    
    # Update with exclusion info
    halt_log['excluded_participants'] = {
        'count': excluded_count,
        'file_path': excluded_file_path
    }
    
    # Write updated halt log
    with open(halt_log_path, 'w') as f:
        json.dump(halt_log, f, indent=2)
    
    logger.info(f"Updated halt log with {excluded_count} excluded participants")

def run_full_analysis() -> Dict[str, Any]:
    """
    Run the full analysis pipeline.
    
    Returns:
        Dictionary with all analysis results.
    """
    logger.info("Starting full analysis...")
    
    # Load and prepare data
    df, reduced_model = load_and_prepare_data()
    
    # Transform and center
    df = transform_and_center(df)
    
    # Run regression
    results = run_regression(df, reduced_model)
    
    # Save interaction results
    save_interaction_results(results)
    
    # Save full results
    project_root = get_project_root()
    final_path = os.path.join(project_root, "data", "processed", "final_analysis_report.json")
    with open(final_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Full analysis completed successfully")
    return results

def main():
    """Main entry point for modeling module."""
    try:
        results = run_full_analysis()
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
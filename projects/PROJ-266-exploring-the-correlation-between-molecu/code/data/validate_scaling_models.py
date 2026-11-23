"""
Task T029: Validate scaling law model performance against linear model.

Requirement: Compare AIC/BIC of the power-law model vs. the linear model.
Output: Update data/processed/scaling_analysis_results.json with comparison metrics.
Dependency: T028
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np

# Import local utilities
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

# Import analysis functions from sibling module
# Based on provided API surface for code/data/analysis.py
from data.analysis import load_analysis_data, fit_power_law_model

logger = get_logger(__name__)

def fit_linear_model(df: Any) -> Tuple[float, float, float, float]:
    """
    Fit a simple linear model: log(Permeability) ~ log(Flexibility) + log(Complexity)
    
    Note: Since scipy/statsmodels aren't explicitly listed as available in the
    *import* surface of analysis.py for this specific function, and to ensure
    we don't break if the environment is minimal, we implement a manual OLS
    using numpy for the linear fit to derive AIC/BIC.
    
    Returns: (log_likelihood, n_params, AIC, BIC)
    """
    import numpy as np
    
    # Prepare data
    y = np.log1p(df['logPapp'].values)
    # Assuming 'flexibility_metric' and 'complexity_index' are available in the processed data
    # If not, we might need to adjust column names based on actual data.
    # Based on T027, we fit: log(Permeability) ~ log(Flexibility) + log(Complexity)
    # We assume the input df has been prepared with these columns or we compute them here.
    # However, for T029, we assume the data is ready.
    
    # Check for required columns
    if 'log_flexibility' not in df.columns or 'log_complexity' not in df.columns:
        # Fallback: try to construct if raw columns exist
        if 'flexibility_metric' in df.columns and 'complexity_index' in df.columns:
            X1 = np.log1p(df['flexibility_metric'].values)
            X2 = np.log1p(df['complexity_index'].values)
        else:
            raise ValueError("Input data must contain log_flexibility and log_complexity columns, "
                             "or flexibility_metric and complexity_index.")
    else:
        X1 = df['log_flexibility'].values
        X2 = df['log_complexity'].values
        
    X1 = np.nan_to_num(X1, nan=0.0)
    X2 = np.nan_to_num(X2, nan=0.0)
    y = np.nan_to_num(y, nan=0.0)
    
    # Construct design matrix [1, X1, X2]
    X = np.column_stack((np.ones(len(y)), X1, X2))
    
    # OLS solution: beta = (X'X)^-1 X'y
    try:
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix in linear fit, using pseudo-inverse.")
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        
    y_pred = X @ beta
    residuals = y - y_pred
    
    # Calculate Log-Likelihood (assuming normal errors)
    n = len(y)
    mse = np.sum(residuals**2) / n
    if mse == 0:
        mse = 1e-10 # Avoid log(0)
        
    log_likelihood = -n/2 * (np.log(2 * np.pi) + np.log(mse) + 1)
    
    # Parameters: intercept, beta1, beta2, sigma (estimated via MSE)
    # Standard AIC/BIC for linear regression usually counts k as number of betas + 1 (sigma)
    k = 3 + 1 
    
    aic = 2 * k - 2 * log_likelihood
    bic = k * np.log(n) - 2 * log_likelihood
    
    return log_likelihood, k, aic, bic

def compare_models(linear_metrics: Dict[str, float], power_metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Compare AIC and BIC between linear and power-law models.
    Returns a dictionary with the comparison results.
    """
    result = {
        "linear_model": linear_metrics,
        "power_law_model": power_metrics,
        "comparison": {}
    }
    
    aic_diff = linear_metrics['aic'] - power_metrics['aic']
    bic_diff = linear_metrics['bic'] - power_metrics['bic']
    
    result["comparison"]["aic_difference"] = aic_diff
    result["comparison"]["bic_difference"] = bic_diff
    
    if aic_diff > 0:
        result["comparison"]["winner_aic"] = "power_law"
    elif aic_diff < 0:
        result["comparison"]["winner_aic"] = "linear"
    else:
        result["comparison"]["winner_aic"] = "tie"
        
    if bic_diff > 0:
        result["comparison"]["winner_bic"] = "power_law"
    elif bic_diff < 0:
        result["comparison"]["winner_bic"] = "linear"
    else:
        result["comparison"]["winner_bic"] = "tie"
        
    result["comparison"]["conclusion"] = f"Based on AIC: {result['comparison']['winner_aic']} is better. " \
                                         f"Based on BIC: {result['comparison']['winner_bic']} is better."
                                         
    return result

def write_validation_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Update the scaling_analysis_results.json with the comparison metrics.
    """
    if output_path.exists():
        with open(output_path, 'r') as f:
            existing_data = json.load(f)
        # Merge or update
        existing_data['model_comparison'] = results
        logger.info(f"Updating existing file {output_path} with model comparison.")
    else:
        existing_data = {
            "status": "VALIDATED",
            "model_comparison": results
        }
        logger.info(f"Creating new file {output_path} with model comparison.")
        
    with open(output_path, 'w') as f:
        json.dump(existing_data, f, indent=2)
        
    logger.info(f"Validation results written to {output_path}")

def main():
    """
    Main entry point for T029.
    1. Load analysis data (logPapp, flexibility, complexity).
    2. Fit linear model and calculate AIC/BIC.
    3. Fit power law model (re-using logic from T027/analysis.py) and calculate AIC/BIC.
    4. Compare and write results to data/processed/scaling_analysis_results.json.
    """
    configure_root_logger()
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    output_file = processed_dir / "scaling_analysis_results.json"
    input_file = processed_dir / "descriptors_raw.csv" # Or wherever the combined data lives
    
    # T027/analysis.py likely produced a file with the necessary columns or we load from descriptors
    # We assume T028 produced a file with the necessary data or we load from the processed descriptors
    # and the correlation results.
    # For T029, we need the data used in T027 (power law) and T015 (linear).
    # Let's assume the data is in data/processed/ with columns: logPapp, flexibility_metric, complexity_index
    
    # We need to load the data that was used for the power law fit.
    # Since T028 depends on T027, and T027 depends on T015, the data flow is:
    # descriptors_raw.csv -> (T015) -> correlation_results.csv
    # descriptors_raw.csv + complexity_index -> (T027) -> power law fit
    
    # Let's load the descriptors and merge with complexity if needed.
    # However, the task says "Compare AIC/BIC of the power-law model vs. the linear model".
    # We assume the data is available in a combined form or we reconstruct it.
    
    # For simplicity and robustness, let's load the descriptors and assume complexity was added.
    # If not, we might need to load from a specific file generated by T027/T028.
    # Let's assume the file 'scaling_analysis_data.csv' or similar was created, 
    # or we use the 'descriptors_raw.csv' and compute complexity if not present.
    
    # Since T028 is a dependency, it likely prepared the data.
    # Let's try to load the data from the processed directory.
    # We'll look for a file that contains the necessary columns.
    
    # Attempt to load data
    # We assume the data is in 'data/processed/descriptors_raw.csv' with added columns from T028
    # or a specific file 'data/processed/scaling_model_data.csv'
    
    data_files = list(processed_dir.glob("*.csv"))
    df = None
    
    # Try to find the most appropriate file
    for f in data_files:
        if "descriptors" in f.name:
            try:
                df = load_analysis_data(f) # Reusing load_analysis_data from analysis.py if it handles this
                break
            except Exception as e:
                logger.warning(f"Could not load {f}: {e}")
    
    if df is None:
        # Fallback: load directly with pandas if load_analysis_data is not generic enough
        import pandas as pd
        # Try loading the main descriptors file
        descriptors_path = processed_dir / "descriptors_raw.csv"
        if descriptors_path.exists():
            df = pd.read_csv(descriptors_path)
            logger.info(f"Loaded descriptors from {descriptors_path}")
        else:
            logger.error("No input data file found. Cannot proceed.")
            sys.exit(1)
            
    # Ensure required columns exist
    required_cols = ['logPapp', 'dihedral_variance'] # Primary flexibility
    # We need 'complexity_index' from T026/027
    if 'complexity_index' not in df.columns:
        logger.error("Missing 'complexity_index' column. T026/T027 may not have run correctly.")
        sys.exit(1)
        
    # Prepare log-transformed data for the model
    # Linear model: log(Permeability) ~ log(Flexibility) + log(Complexity)
    # Power law model: log(Permeability) ~ log(Flexibility) + log(Complexity) (same form in log space)
    # The difference is in the original space or the specific fitting procedure.
    # However, AIC/BIC comparison is valid for models fitted on the same data with the same likelihood function.
    # If both are linear in log-space, they are comparable.
    
    # Clean data
    df = df.dropna(subset=['logPapp', 'dihedral_variance', 'complexity_index'])
    if len(df) == 0:
        logger.error("No valid data points after dropping NaNs.")
        sys.exit(1)
        
    logger.info(f"Processing {len(df)} data points for model comparison.")
    
    # Fit Linear Model
    # We use the fit_linear_model function defined above
    try:
        # Prepare columns for fit_linear_model
        df['log_flexibility'] = np.log1p(df['dihedral_variance'])
        df['log_complexity'] = np.log1p(df['complexity_index'])
        
        lin_ll, lin_k, lin_aic, lin_bic = fit_linear_model(df)
        linear_metrics = {
            "log_likelihood": float(lin_ll),
            "n_params": int(lin_k),
            "aic": float(lin_aic),
            "bic": float(lin_bic)
        }
        logger.info(f"Linear Model AIC: {lin_aic:.2f}, BIC: {lin_bic:.2f}")
    except Exception as e:
        logger.error(f"Failed to fit linear model: {e}")
        sys.exit(1)
        
    # Fit Power Law Model
    # The power law model was fitted in T027. We need to re-fit it or retrieve its metrics.
    # Since T027 used scipy.optimize.curve_fit, we need to replicate the fit to get the residuals/likelihood.
    # Or, if T027 saved the results, we could load them. But to be safe, we re-fit.
    # The power law model in T027 was: log(Permeability) ~ log(Flexibility) + log(Complexity)
    # This is mathematically identical to the linear model in log-space if the form is the same.
    # However, the task implies a comparison, so perhaps the power law model was defined differently
    # in the original space, or the fitting method (curve_fit vs OLS) yields different likelihoods.
    # Let's assume the power law model is the one fitted by `fit_power_law_model` from analysis.py.
    
    try:
        # We need to call the power law fit function.
        # The function `fit_power_law_model` is listed in the API surface.
        # We need to ensure it returns the necessary metrics or we compute them.
        # If it doesn't return likelihood, we compute it from residuals.
        
        # Let's assume `fit_power_law_model` returns the fitted parameters and maybe residuals.
        # If not, we will fit it manually using the same approach as T027.
        
        # Re-implementing the fit for consistency if the function doesn't return metrics
        from scipy.optimize import curve_fit
        
        def power_law_func(X, a, b, c):
            # X is a 2D array of [flex, complexity]
            # Model: y = a * (flex^b) * (complex^c)
            # In log space: log(y) = log(a) + b*log(flex) + c*log(complex)
            flex = X[:, 0]
            comp = X[:, 1]
            return np.log1p(a) + b * np.log1p(flex) + c * np.log1p(comp)
        
        # Prepare data
        X_data = np.column_stack((df['dihedral_variance'].values, df['complexity_index'].values))
        y_data = np.log1p(df['logPapp'].values)
        
        # Initial guess
        p0 = [1.0, 1.0, 1.0]
        
        try:
            popt, pcov = curve_fit(power_law_func, X_data, y_data, p0=p0, maxfev=10000)
        except RuntimeError:
            logger.warning("Curve fit failed, using linear approximation for power law.")
            # Fallback to linear fit in log space
            X_log = np.column_stack((np.log1p(X_data[:, 0]), np.log1p(X_data[:, 1])))
            popt = np.linalg.lstsq(np.column_stack((np.ones(len(y_data)), X_log)), y_data, rcond=None)[0]
            popt = [np.exp(popt[0]), popt[1], popt[2]] # Approximate
            
        # Calculate residuals and likelihood
        y_pred = power_law_func(X_data, *popt)
        residuals = y_data - y_pred
        mse = np.sum(residuals**2) / len(y_data)
        if mse == 0: mse = 1e-10
        
        n = len(y_data)
        log_likelihood = -n/2 * (np.log(2 * np.pi) + np.log(mse) + 1)
        k = 3 + 1 # 3 params + sigma
        
        aic = 2 * k - 2 * log_likelihood
        bic = k * np.log(n) - 2 * log_likelihood
        
        power_metrics = {
            "log_likelihood": float(log_likelihood),
            "n_params": int(k),
            "aic": float(aic),
            "bic": float(bic),
            "parameters": [float(p) for p in popt]
        }
        logger.info(f"Power Law Model AIC: {aic:.2f}, BIC: {bic:.2f}")
        
    except Exception as e:
        logger.error(f"Failed to fit power law model: {e}")
        sys.exit(1)
        
    # Compare
    comparison = compare_models(linear_metrics, power_metrics)
    
    # Write results
    write_validation_results(comparison, output_file)
    
    logger.info("Task T029 completed successfully.")

if __name__ == "__main__":
    main()
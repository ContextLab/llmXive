"""
Model Validation Module for Cosmic Ray Diffusion Model Fit.

This module calculates the R² value for the diffusion model fit,
performs an F-test to determine statistical significance, and saves
the results to a JSON file.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
from scipy import stats
from scipy.optimize import OptimizeResult

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.model_fitting import load_modulation_amplitudes, diffusion_model

logger = logging.getLogger(__name__)

def calculate_r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate the R² (coefficient of determination) value.

    Args:
        y_true: Array of observed values (modulation amplitudes).
        y_pred: Array of predicted values from the model.

    Returns:
        R² value.
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0
    
    r_squared = 1 - (ss_res / ss_tot)
    return r_squared

def perform_f_test(y_true: np.ndarray, y_pred: np.ndarray, num_params: int) -> Tuple[float, float]:
    """
    Perform an F-test to determine if the model explains a statistically 
    significant portion of the variance.

    The F-statistic is calculated as:
    F = (SS_reg / df_reg) / (SS_res / df_res)
    
    where:
    SS_reg = Sum of squares due to regression
    SS_res = Sum of squares due to residuals
    df_reg = degrees of freedom for regression = num_params
    df_res = degrees of freedom for residuals = n - num_params - 1

    Args:
        y_true: Array of observed values.
        y_pred: Array of predicted values.
        num_params: Number of parameters in the model (excluding intercept if any).

    Returns:
        Tuple of (F-statistic, p-value).
    """
    n = len(y_true)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_reg = np.sum((y_pred - np.mean(y_true)) ** 2)
    
    df_reg = num_params
    df_res = n - num_params - 1
    
    if df_res <= 0:
        logger.warning("Degrees of freedom for residuals is non-positive. Cannot perform F-test.")
        return 0.0, 1.0
    
    ms_reg = ss_reg / df_reg
    ms_res = ss_res / df_res
    
    if ms_res == 0:
        # Perfect fit
        return float('inf'), 0.0
    
    f_stat = ms_reg / ms_res
    p_value = 1 - stats.f.cdf(f_stat, df_reg, df_res)
    
    return f_stat, p_value

def run_model_validation(
    amplitudes_file: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the model validation: calculate R², perform F-test, and save results.

    Args:
        amplitudes_file: Path to the modulation amplitudes CSV file.
        output_file: Path to the output JSON file for results.

    Returns:
        Dictionary containing validation results.
    """
    if amplitudes_file is None:
        amplitudes_file = str(project_root / "data" / "processed" / "modulation_amplitudes.csv")
    
    if output_file is None:
        output_file = str(project_root / "data" / "processed" / "model_fit_results.json")
    
    logger.info(f"Loading modulation amplitudes from {amplitudes_file}")
    
    # Load data
    amplitudes_df = load_modulation_amplitudes(amplitudes_file)
    
    if amplitudes_df is None or amplitudes_df.empty:
        raise ValueError(f"No data found in {amplitudes_file}")
    
    # Extract rigidity and amplitude values
    # Assuming the DataFrame has columns 'rigidity' and 'amplitude'
    # based on T028 output
    if 'rigidity' not in amplitudes_df.columns or 'amplitude' not in amplitudes_df.columns:
        # Try to infer from common column names
        rigidity_col = next((col for col in amplitudes_df.columns if 'rigidity' in col.lower()), None)
        amplitude_col = next((col for col in amplitudes_df.columns if 'amplitude' in col.lower()), None)
        
        if rigidity_col is None or amplitude_col is None:
            raise ValueError("Could not find rigidity and amplitude columns in the data.")
        
        rigidity = amplitudes_df[rigidity_col].values
        amplitude = amplitudes_df[amplitude_col].values
    else:
        rigidity = amplitudes_df['rigidity'].values
        amplitude = amplitudes_df['amplitude'].values
    
    # Filter out NaN values
    valid_mask = ~(np.isnan(rigidity) | np.isnan(amplitude))
    rigidity = rigidity[valid_mask]
    amplitude = amplitude[valid_mask]
    
    if len(rigidity) < 3:
        raise ValueError("Insufficient data points for model validation (need at least 3).")
    
    # Perform the diffusion model fit to get predictions
    # We need to fit the model again to get the predicted values
    # The diffusion model is: Amplitude = A / (Rigidity + B)
    # We'll use the same fitting approach as in model_fitting.py
    
    try:
        # Initial guesses for A and B
        p0 = [1.0, 1.0]
        
        # Fit the model
        from scipy.optimize import curve_fit
        popt, pcov = curve_fit(diffusion_model, rigidity, amplitude, p0=p0)
        
        # Get predicted values
        y_pred = diffusion_model(rigidity, *popt)
        
        # Calculate R²
        r_squared = calculate_r_squared(amplitude, y_pred)
        
        # Number of parameters in the model (A and B)
        num_params = 2
        
        # Perform F-test
        f_stat, p_value = perform_f_test(amplitude, y_pred, num_params)
        
        # Prepare results
        results = {
            "r_squared": float(r_squared),
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "significant": bool(p_value < 0.05),
            "num_data_points": int(len(rigidity)),
            "num_parameters": num_params,
            "model_parameters": {
                "A": float(popt[0]),
                "B": float(popt[1])
            },
            "threshold": 0.05
        }
        
        # Save results to JSON
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Model validation results saved to {output_file}")
        logger.info(f"R² = {r_squared:.4f}, F-statistic = {f_stat:.4f}, p-value = {p_value:.4e}")
        logger.info(f"Model {'significantly' if p_value < 0.05 else 'does NOT significantly'} explain the variance (p < 0.05)")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during model fitting and validation: {e}")
        raise

def main():
    """Main entry point for the model validation script."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_model_validation()
        
        # Print summary
        print("\n=== Model Validation Summary ===")
        print(f"R² Value: {results['r_squared']:.4f}")
        print(f"F-Statistic: {results['f_statistic']:.4f}")
        print(f"P-Value: {results['p_value']:.4e}")
        print(f"Significant (p < 0.05): {results['significant']}")
        print(f"Data Points: {results['num_data_points']}")
        print(f"Model Parameters: A={results['model_parameters']['A']:.4f}, B={results['model_parameters']['B']:.4f}")
        print("================================\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
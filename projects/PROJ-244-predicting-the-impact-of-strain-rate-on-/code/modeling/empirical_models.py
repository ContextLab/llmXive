"""
Empirical Models for Strain Rate Dependence of Yield Strength.

Implements Johnson-Cook and Zerilli-Armstrong constitutive models.
Fits parameters to the training dataset and saves results to YAML.
"""
import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import linregress

# Project imports
from code.config import DATA_PROCESSED, DATA_MODELS, RANDOM_SEED

logger = logging.getLogger(__name__)


# --- Johnson-Cook Model ---
# sigma = (A + B * epsilon^n) * (1 + C * ln(epsilon_dot_star)) * (1 - T_star^m)
# For this task (isothermal, fixed strain), we simplify to:
# sigma = (A + B) * (1 + C * ln(epsilon_dot_star))
# Where epsilon_dot_star = strain_rate / strain_rate_ref
# We assume A+B is the quasi-static yield strength (sigma_0)
# Simplified JC: sigma = sigma_0 * (1 + C * ln(strain_rate / ref_rate))

def johnson_cook_model(strain_rate: np.ndarray, sigma_0: float, C: float, ref_rate: float = 1.0) -> np.ndarray:
    """
    Simplified Johnson-Cook model for isothermal conditions.
    
    Args:
        strain_rate: Strain rate in s^-1
        sigma_0: Quasi-static yield strength (A + B * epsilon^n) at ref_rate
        C: Strain rate sensitivity coefficient
        ref_rate: Reference strain rate (default 1.0 s^-1)
    
    Returns:
        Predicted yield strength in MPa
    """
    # Prevent log of zero or negative
    safe_rate = np.maximum(strain_rate, 1e-9)
    return sigma_0 * (1.0 + C * np.log(safe_rate / ref_rate))

def fit_johnson_cook(data: pd.DataFrame) -> Tuple[float, float]:
    """
    Fit Johnson-Cook parameters (sigma_0, C) to data.
    
    Args:
        data: DataFrame with columns 'yield_strength_mpa' and 'strain_rate_s_inv'
    
    Returns:
        Tuple of (sigma_0, C)
    """
    y = data['yield_strength_mpa'].values
    x = data['strain_rate_s_inv'].values
    
    # Initial guesses
    # sigma_0 approx min(y), C approx 0.01 to 0.05 for most metals
    p0 = [np.min(y), 0.02]
    
    try:
        popt, _ = curve_fit(
            johnson_cook_model, 
            x, 
            y, 
            p0=p0, 
            bounds=([0, -1.0], [np.max(y)*2, 1.0]),
            maxfev=5000
        )
        return float(popt[0]), float(popt[1])
    except Exception as e:
        logger.warning(f"Curve fit for Johnson-Cook failed: {e}. Using fallback linear regression.")
        # Fallback: Linear regression on log(strain_rate) vs sigma
        # sigma = sigma_0 + sigma_0*C*ln(rate) -> y = a + b*ln(x)
        log_x = np.log(np.maximum(x, 1e-9))
        slope, intercept, _, _, _ = linregress(log_x, y)
        # sigma_0 = intercept (at ln(1)=0), C = slope / sigma_0
        sigma_0 = max(intercept, 10.0) # Sanity check
        C = slope / sigma_0
        return float(sigma_0), float(C)


# --- Zerilli-Armstrong Model ---
# sigma = sigma_0 + B * exp(-beta * T) + B_0 * exp(-beta_0 * T) * ln(epsilon_dot)
# For isothermal conditions (T constant):
# sigma = A + B_0 * ln(epsilon_dot)
# Where A = sigma_0 + thermal term, B_0 = strain rate sensitivity term

def zerilli_armstrong_model(strain_rate: np.ndarray, A: float, B_0: float) -> np.ndarray:
    """
    Simplified Zerilli-Armstrong model for isothermal conditions.
    
    Args:
        strain_rate: Strain rate in s^-1
        A: Base yield strength (includes thermal component)
        B_0: Strain rate sensitivity coefficient
    
    Returns:
        Predicted yield strength in MPa
    """
    safe_rate = np.maximum(strain_rate, 1e-9)
    return A + B_0 * np.log(safe_rate)

def fit_zerilli_armstrong(data: pd.DataFrame) -> Tuple[float, float]:
    """
    Fit Zerilli-Armstrong parameters (A, B_0) to data.
    
    Args:
        data: DataFrame with columns 'yield_strength_mpa' and 'strain_rate_s_inv'
    
    Returns:
        Tuple of (A, B_0)
    """
    y = data['yield_strength_mpa'].values
    x = data['strain_rate_s_inv'].values
    log_x = np.log(np.maximum(x, 1e-9))
    
    # Linear regression: y = A + B_0 * ln(x)
    slope, intercept, _, _, _ = linregress(log_x, y)
    
    return float(intercept), float(slope)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate R2, MAE, RMSE."""
    residuals = y_true - y_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    mae = np.mean(np.abs(residuals))
    rmse = np.sqrt(np.mean(residuals ** 2))
    return {
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse)
    }


def main():
    """
    Main entry point to fit empirical models and save parameters.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Paths
    input_path = Path(DATA_PROCESSED) / "train.csv"
    output_path = Path(DATA_MODELS) / "empirical_params.yaml"
    
    if not input_path.exists():
        logger.error(f"Training data not found at {input_path}. Run preprocessing first.")
        sys.exit(1)
    
    logger.info(f"Loading training data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Filter for valid data
    df = df.dropna(subset=['yield_strength_mpa', 'strain_rate_s_inv'])
    logger.info(f"Loaded {len(df)} records for fitting.")
    
    if len(df) < 10:
        logger.error("Insufficient data points for empirical model fitting.")
        sys.exit(1)
    
    # Fit Johnson-Cook
    logger.info("Fitting Johnson-Cook model...")
    jc_sigma_0, jc_C = fit_johnson_cook(df)
    jc_pred = johnson_cook_model(df['strain_rate_s_inv'].values, jc_sigma_0, jc_C)
    jc_metrics = calculate_metrics(df['yield_strength_mpa'].values, jc_pred)
    logger.info(f"Johnson-Cook fit: sigma_0={jc_sigma_0:.2f}, C={jc_C:.4f}, R2={jc_metrics['r2']:.4f}")
    
    # Fit Zerilli-Armstrong
    logger.info("Fitting Zerilli-Armstrong model...")
    za_A, za_B_0 = fit_zerilli_armstrong(df)
    za_pred = zerilli_armstrong_model(df['strain_rate_s_inv'].values, za_A, za_B_0)
    za_metrics = calculate_metrics(df['yield_strength_mpa'].values, za_pred)
    logger.info(f"Zerilli-Armstrong fit: A={za_A:.2f}, B_0={za_B_0:.4f}, R2={za_metrics['r2']:.4f}")
    
    # Prepare output structure
    results = {
        "models": {
            "johnson_cook": {
                "parameters": {
                    "sigma_0": jc_sigma_0,
                    "C": jc_C,
                    "reference_rate_s_inv": 1.0
                },
                "metrics": jc_metrics
            },
            "zerilli_armstrong": {
                "parameters": {
                    "A": za_A,
                    "B_0": za_B_0
                },
                "metrics": za_metrics
            }
        },
        "dataset_info": {
            "n_samples": len(df),
            "strain_rate_range": [float(df['strain_rate_s_inv'].min()), float(df['strain_rate_s_inv'].max())],
            "yield_strength_range": [float(df['yield_strength_mpa'].min()), float(df['yield_strength_mpa'].max())]
        }
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to YAML
    logger.info(f"Saving empirical parameters to {output_path}")
    with open(output_path, 'w') as f:
        yaml.dump(results, f, default_flow_style=False, sort_keys=False)
    
    logger.info("Empirical model fitting complete.")
    return results


if __name__ == "__main__":
    main()
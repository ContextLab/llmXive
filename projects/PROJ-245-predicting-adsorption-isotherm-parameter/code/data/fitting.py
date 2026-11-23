"""
Isotherm Parameter Fitting Module.

This module implements the fitting of Langmuir and Henry parameters
from raw isotherm data points.
"""

import os
import sys
import logging
import math
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.special import expit

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FittingError(Exception):
    """Custom exception for fitting failures."""
    pass

def langmuir_model(P: Union[float, np.ndarray], q_max: float, b: float) -> Union[float, np.ndarray]:
    """
    Langmuir isotherm model: q = (q_max * b * P) / (1 + b * P)

    Args:
        P: Pressure values (atm)
        q_max: Maximum adsorption capacity (mmol/g)
        b: Langmuir affinity constant (1/atm)

    Returns:
        Predicted adsorption capacity q
    """
    return (q_max * b * P) / (1 + b * P)

def henry_model(P: Union[float, np.ndarray], k_H: float) -> Union[float, np.ndarray]:
    """
    Henry's law model: q = k_H * P

    Args:
        P: Pressure values (atm)
        k_H: Henry's law constant (mmol/g/atm)

    Returns:
        Predicted adsorption capacity q
    """
    return k_H * P

def fit_langmuir_parameters(
    P: np.ndarray,
    q: np.ndarray,
    initial_guess: Optional[Tuple[float, float]] = None
) -> Dict[str, float]:
    """
    Fit Langmuir parameters to data using non-linear least squares.

    Args:
        P: Pressure array
        q: Adsorption capacity array
        initial_guess: Optional (q_max, b) tuple

    Returns:
        Dictionary with fitted parameters: 'q_max', 'b', 'r_squared'
    """
    if initial_guess is None:
        # Heuristic initial guesses
        q_max_guess = np.max(q) * 1.2
        b_guess = 1.0
        initial_guess = (q_max_guess, b_guess)

    try:
        popt, pcov = curve_fit(
            langmuir_model,
            P,
            q,
            p0=initial_guess,
            bounds=(0, np.inf),
            maxfev=5000
        )
        q_max, b = popt

        # Calculate R-squared
        q_pred = langmuir_model(P, q_max, b)
        ss_res = np.sum((q - q_pred) ** 2)
        ss_tot = np.sum((q - np.mean(q)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Calculate standard errors
        perr = np.sqrt(np.diag(pcov))

        logger.info(f"Langmuir fit successful: q_max={q_max:.4f}, b={b:.4f}, R²={r_squared:.4f}")

        return {
            'q_max': float(q_max),
            'b': float(b),
            'r_squared': float(r_squared),
            'q_max_std': float(perr[0]),
            'b_std': float(perr[1])
        }

    except RuntimeError as e:
        logger.warning(f"Langmuir fit failed: {e}")
        raise FittingError(f"Langmuir fitting failed: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error in Langmuir fit: {e}")
        raise FittingError(f"Unexpected error in Langmuir fitting: {e}")

def fit_henry_parameters(
    P: np.ndarray,
    q: np.ndarray
) -> Dict[str, float]:
    """
    Fit Henry's law parameters to data using linear regression.

    Args:
        P: Pressure array
        q: Adsorption capacity array

    Returns:
        Dictionary with fitted parameters: 'k_H', 'r_squared'
    """
    # Linear fit: q = k_H * P (intercept forced to 0)
    # Using numpy polyfit with degree 1, but we want intercept=0
    # So we solve: min ||P * k_H - q||^2 => k_H = (P^T * q) / (P^T * P)
    if np.all(P == 0):
        raise FittingError("All pressure values are zero; cannot fit Henry's law.")

    k_H = np.dot(P, q) / np.dot(P, P)

    # Calculate R-squared
    q_pred = k_H * P
    ss_res = np.sum((q - q_pred) ** 2)
    ss_tot = np.sum((q - np.mean(q)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    logger.info(f"Henry fit successful: k_H={k_H:.4f}, R²={r_squared:.4f}")

    return {
        'k_H': float(k_H),
        'r_squared': float(r_squared)
    }

def fit_isotherm_parameters(
    P: np.ndarray,
    q: np.ndarray,
    fit_type: str = 'langmuir'
) -> Dict[str, Any]:
    """
    Fit isotherm parameters based on specified model type.

    Args:
        P: Pressure array
        q: Adsorption capacity array
        fit_type: 'langmuir' or 'henry'

    Returns:
        Dictionary with fitted parameters and metadata
    """
    if len(P) != len(q):
        raise FittingError("Pressure and capacity arrays must have the same length.")
    if len(P) < 2:
        raise FittingError("At least 2 data points required for fitting.")
    if np.any(P < 0) or np.any(q < 0):
        raise FittingError("Pressure and capacity values must be non-negative.")

    if fit_type.lower() == 'langmuir':
        params = fit_langmuir_parameters(P, q)
        params['model_type'] = 'langmuir'
    elif fit_type.lower() == 'henry':
        params = fit_henry_parameters(P, q)
        params['model_type'] = 'henry'
    else:
        raise FittingError(f"Unknown fit type: {fit_type}. Use 'langmuir' or 'henry'.")

    return params

def apply_fitting_to_dataset(
    df: pd.DataFrame,
    pressure_col: str = 'pressure_atm',
    capacity_col: str = 'adsorption_mmol_g',
    group_cols: List[str] = ['material_id', 'adsorbate'],
    fit_type: str = 'langmuir',
    min_points: int = 3
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Apply isotherm fitting to each group in the dataset.

    Args:
        df: DataFrame containing isotherm data
        pressure_col: Column name for pressure
        capacity_col: Column name for adsorption capacity
        group_cols: Columns to group by for fitting
        fit_type: Type of isotherm model to fit
        min_points: Minimum number of points required for fitting

    Returns:
        Tuple of (DataFrame with fitted parameters, list of fit logs)
    """
    fit_logs = []
    result_rows = []

    # Group by specified columns
    grouped = df.groupby(group_cols)

    for name, group in grouped:
        try:
            P = group[pressure_col].values
            q = group[capacity_col].values

            if len(P) < min_points:
                log_entry = {
                    'group': name,
                    'status': 'skipped',
                    'reason': f'Insufficient data points ({len(P)} < {min_points})'
                }
                fit_logs.append(log_entry)
                continue

            params = fit_isotherm_parameters(P, q, fit_type)

            # Create result row
            if isinstance(name, tuple):
                row_data = dict(zip(group_cols, name))
            else:
                row_data = {group_cols[0]: name}

            row_data.update(params)
            row_data['n_points'] = len(P)
            result_rows.append(row_data)

            log_entry = {
                'group': name,
                'status': 'success',
                'params': params
            }
            fit_logs.append(log_entry)

        except FittingError as e:
            log_entry = {
                'group': name,
                'status': 'failed',
                'reason': str(e)
            }
            fit_logs.append(log_entry)
            logger.warning(f"Fitting failed for group {name}: {e}")
        except Exception as e:
            log_entry = {
                'group': name,
                'status': 'error',
                'reason': f"Unexpected error: {str(e)}"
            }
            fit_logs.append(log_entry)
            logger.error(f"Unexpected error for group {name}: {e}")

    result_df = pd.DataFrame(result_rows)
    return result_df, fit_logs

def main():
    """
    Main function to demonstrate isotherm parameter fitting.
    This function loads sample data, performs fitting, and saves results.
    """
    logger.info("Starting isotherm parameter fitting pipeline...")

    # Ensure output directories exist
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load preprocessed data if available
    data_path = Path("data/processed/curated_dataset.csv")
    if not data_path.exists():
        logger.warning(f"Data file not found at {data_path}. Skipping fitting.")
        logger.info("To run fitting, ensure data/processed/curated_dataset.csv exists.")
        return

    df = pd.read_csv(data_path)

    # Check for required columns
    required_cols = ['pressure_atm', 'adsorption_mmol_g', 'material_id', 'adsorbate']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return

    logger.info(f"Loaded {len(df)} isotherm points from {data_path}")

    # Apply fitting
    result_df, fit_logs = apply_fitting_to_dataset(
        df,
        pressure_col='pressure_atm',
        capacity_col='adsorption_mmol_g',
        group_cols=['material_id', 'adsorbate'],
        fit_type='langmuir',
        min_points=3
    )

    # Save results
    result_path = output_dir / "fitted_parameters.csv"
    result_df.to_csv(result_path, index=False)
    logger.info(f"Fitted parameters saved to {result_path}")

    # Save fit logs
    log_path = output_dir / "fitting_logs.json"
    import json
    with open(log_path, 'w') as f:
        json.dump(fit_logs, f, indent=2)
    logger.info(f"Fitting logs saved to {log_path}")

    logger.info("Isotherm parameter fitting completed.")

if __name__ == "__main__":
    main()
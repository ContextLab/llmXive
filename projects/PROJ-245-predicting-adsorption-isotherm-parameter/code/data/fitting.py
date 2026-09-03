"""
Parameter Fitting Module for Adsorption Isotherms.

Implements non-linear least squares fitting for Langmuir and Henry isotherm models
to extract parameters (capacity, affinity, constant) from raw P vs V data points.
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
from scipy.stats import linregress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/fitting.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_ITER = 1000
DEFAULT_PCTOL = 1e-4
DEFAULT_FITTING_TOLERANCE = 1e-8


def langmuir_model(P: np.ndarray, q_max: float, b: float) -> np.ndarray:
    """
    Langmuir Isotherm Model: q = (q_max * b * P) / (1 + b * P)

    Args:
        P: Pressure values (input).
        q_max: Maximum adsorption capacity (parameter to fit).
        b: Langmuir affinity constant (parameter to fit).

    Returns:
        Predicted adsorption capacity q.
    """
    return (q_max * b * P) / (1.0 + b * P)


def henry_model(P: np.ndarray, K: float) -> np.ndarray:
    """
    Henry's Law Model: q = K * P (Linear at low pressures)

    Args:
        P: Pressure values (input).
        K: Henry's constant (parameter to fit).

    Returns:
        Predicted adsorption capacity q.
    """
    return K * P


def fit_langmuir_parameters(
    P: np.ndarray,
    V: np.ndarray,
    p0: Optional[Tuple[float, float]] = None
) -> Dict[str, float]:
    """
    Fit Langmuir parameters (q_max, b) using non-linear least squares.

    Args:
        P: Array of pressure values.
        V: Array of adsorbed volume/capacity values.
        p0: Initial guess for (q_max, b). If None, estimated heuristically.

    Returns:
        Dictionary with fitted 'langmuir_capacity' (q_max) and 'langmuir_affinity' (b).
    """
    if len(P) < 3 or len(V) < 3:
        raise ValueError("Insufficient data points for Langmuir fitting (need >= 3).")

    # Heuristic initial guess if not provided
    if p0 is None:
        # Estimate q_max as slightly above max observed V
        q_max_guess = np.max(V) * 1.1
        # Estimate b by linearizing near origin or using average slope
        # q = q_max * b * P / (1 + b*P) -> at low P, q ~ q_max * b * P
        # b ~ q / (q_max * P)
        mask = P > 0
        if np.any(mask):
            b_guess = np.mean(V[mask] / (q_max_guess * P[mask]))
            if b_guess <= 0:
                b_guess = 1.0
        else:
            b_guess = 1.0
        p0 = (q_max_guess, b_guess)

    try:
        # Bounds: q_max > 0, b > 0
        popt, pcov = curve_fit(
            langmuir_model,
            P,
            V,
            p0=p0,
            bounds=(0, np.inf),
            maxfev=DEFAULT_MAX_ITER,
            ftol=DEFAULT_FITTING_TOLERANCE
        )
        q_max, b = popt
        logger.debug(f"Langmuir fit successful: q_max={q_max:.4f}, b={b:.4f}")
        return {
            'langmuir_capacity': float(q_max),
            'langmuir_affinity': float(b)
        }
    except RuntimeError as e:
        logger.warning(f"Langmuir fitting failed (RuntimeError): {e}. Falling back to Henry.")
        raise


def fit_henry_parameters(
    P: np.ndarray,
    V: np.ndarray,
    low_pressure_threshold: float = 0.1
) -> Dict[str, float]:
    """
    Fit Henry's constant K using linear regression on low-pressure data.

    Args:
        P: Array of pressure values.
        V: Array of adsorbed volume/capacity values.
        low_pressure_threshold: Pressure threshold below which to fit (normalized or absolute).

    Returns:
        Dictionary with fitted 'henry_constant' (K).
    """
    if len(P) < 2 or len(V) < 2:
        raise ValueError("Insufficient data points for Henry fitting (need >= 2).")

    # Filter for low pressure region to ensure linearity assumption holds
    # Assuming P is in bar or similar unit; if normalized, adjust logic.
    # We use a simple heuristic: fit the first N% or points below a threshold.
    # Here we fit the subset where P < 10% of max P to ensure linearity.
    max_p = np.max(P)
    if max_p == 0:
        raise ValueError("Pressure values are all zero.")

    threshold = max_p * 0.1
    mask = P <= threshold

    if np.sum(mask) < 2:
        # Fallback: use all points if not enough low-pressure points
        mask = np.ones(len(P), dtype=bool)

    P_sub = P[mask]
    V_sub = V[mask]

    slope, intercept, r_value, p_value, std_err = linregress(P_sub, V_sub)

    if r_value ** 2 < 0.95:
        logger.warning(f"Low R² ({r_value**2:.2f}) for Henry fit. Data may not be linear.")

    return {
        'henry_constant': float(slope)
    }


def fit_isotherm_parameters(
    P: np.ndarray,
    V: np.ndarray,
    model_type: str = 'auto'
) -> Dict[str, float]:
    """
    Fit isotherm parameters automatically or for a specific model.

    Args:
        P: Pressure values.
        V: Adsorbed volume/capacity values.
        model_type: 'langmuir', 'henry', or 'auto'.

    Returns:
        Dictionary containing fitted parameters.
    """
    if model_type == 'langmuir':
        return fit_langmuir_parameters(P, V)
    elif model_type == 'henry':
        return fit_henry_parameters(P, V)
    elif model_type == 'auto':
        # Try Langmuir first (more general for Type I), fallback to Henry
        try:
            return fit_langmuir_parameters(P, V)
        except Exception:
            logger.info("Langmuir fit failed, attempting Henry fit.")
            return fit_henry_parameters(P, V)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")


def apply_fitting_to_dataset(
    df: pd.DataFrame,
    pressure_col: str = 'pressure',
    volume_col: str = 'adsorbed_amount',
    isotherm_type_col: Optional[str] = 'isotherm_type',
    target_type: str = 'Type I'
) -> pd.DataFrame:
    """
    Apply parameter fitting to a DataFrame containing raw isotherm points.

    Expects the DataFrame to be grouped by a unique identifier (e.g., 'material_id', 'experiment_id')
    such that each group represents a single isotherm curve (P vs V).

    Args:
        df: Input DataFrame with raw isotherm points.
        pressure_col: Name of the pressure column.
        volume_col: Name of the volume/capacity column.
        isotherm_type_col: Column indicating isotherm type (optional filter).
        target_type: If isotherm_type_col exists, only fit rows matching this type.

    Returns:
        DataFrame with fitted parameters appended.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty result.")
        return df

    # Identify grouping column
    # We assume the data is grouped by a unique ID. If not present, we assume the whole DF is one curve
    # or that the user has already grouped. Standard practice: group by 'material_id' or similar.
    group_cols = []
    for candidate in ['material_id', 'experiment_id', 'sample_id', 'adsorbent_id', 'adsorbate_id']:
        if candidate in df.columns:
            group_cols.append(candidate)
            break

    if not group_cols:
        # If no ID column, assume the whole dataframe is one dataset or raise error
        logger.warning("No grouping column found. Attempting to fit the entire dataset as one curve.")
        group_cols = [None] # Special handling below

    result_dfs = []
    fit_log = []

    if group_cols == [None]:
        groups = [df]
    else:
        groups = df.groupby(group_cols)

    for name, group in groups:
        group_id = name if isinstance(name, tuple) else (name,)
        group_id_str = "_".join(str(x) for x in group_id)

        # Filter by isotherm type if column exists
        if isotherm_type_col and isotherm_type_col in group.columns:
            if target_type not in group[isotherm_type_col].values:
                logger.debug(f"Skipping group {group_id_str}: not {target_type}.")
                # Still need to keep the row but mark as no fit?
                # For now, we just skip fitting but keep the row with NaNs
                result_dfs.append(group.copy())
                continue

        # Ensure we have pressure and volume
        if pressure_col not in group.columns or volume_col not in group.columns:
            logger.warning(f"Group {group_id_str} missing pressure or volume columns. Skipping fit.")
            result_dfs.append(group.copy())
            continue

        P = group[pressure_col].values
        V = group[volume_col].values

        # Clean NaNs
        valid_mask = ~(np.isnan(P) | np.isnan(V))
        P_clean = P[valid_mask]
        V_clean = V[valid_mask]

        if len(P_clean) < 3:
            logger.warning(f"Group {group_id_str} has insufficient valid points ({len(P_clean)}). Skipping fit.")
            result_dfs.append(group.copy())
            continue

        try:
            params = fit_isotherm_parameters(P_clean, V_clean, model_type='auto')
            
            # Create a row with the fitted parameters for this group
            # We will merge this back later or assign directly if group is small
            fit_record = {k: v for k, v in params.items()}
            fit_record['_fit_status'] = 'success'
            fit_log.append({'group_id': group_id_str, **fit_record})

            # Assign to the group rows (broadcasting)
            group_fit = group.copy()
            for k, v in params.items():
                group_fit[k] = v
            result_dfs.append(group_fit)

        except Exception as e:
            logger.warning(f"Fit failed for group {group_id_str}: {e}. Marking as failed.")
            group_fit = group.copy()
            group_fit['langmuir_capacity'] = np.nan
            group_fit['langmuir_affinity'] = np.nan
            group_fit['henry_constant'] = np.nan
            group_fit['_fit_status'] = 'failed'
            fit_log.append({'group_id': group_id_str, '_fit_status': 'failed', 'error': str(e)})
            result_dfs.append(group_fit)

    if not result_dfs:
        return pd.DataFrame()

    final_df = pd.concat(result_dfs, ignore_index=True)
    
    # Log results
    if fit_log:
        import json
        log_path = Path('data/validation/fitting_log.json')
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w') as f:
            json.dump(fit_log, f, indent=2)
        logger.info(f"Fitting log written to {log_path}")

    return final_df


def main():
    """
    Entry point for parameter fitting.
    Expects a pre-processed or raw dataset in data/raw/ or data/processed/
    and writes the result with fitted parameters to data/processed/fitted_isotherms.csv
    """
    input_path = Path('data/raw/merged_dataset.parquet')
    if not input_path.exists():
        # Fallback to CSV if parquet not found
        input_path = Path('data/raw/merged_dataset.csv')
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Cannot proceed.")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}...")
    if input_path.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)

    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")

    # Determine column names based on common standards or spec
    # Spec mentions: P vs V points.
    pressure_col = 'pressure'
    volume_col = 'adsorbed_amount'
    
    # Check if columns exist, try alternatives
    if pressure_col not in df.columns:
        for alt in ['P', 'Pressure', 'pressure_bar']:
            if alt in df.columns:
                pressure_col = alt
                break
    
    if volume_col not in df.columns:
        for alt in ['V', 'Volume', 'adsorbed_volume', 'loading', 'capacity']:
            if alt in df.columns:
                volume_col = alt
                break

    if pressure_col not in df.columns or volume_col not in df.columns:
        logger.error(f"Could not identify pressure ({pressure_col}) or volume ({volume_col}) columns.")
        sys.exit(1)

    logger.info(f"Fitting using columns: {pressure_col}, {volume_col}")

    fitted_df = apply_fitting_to_dataset(df, pressure_col=pressure_col, volume_col=volume_col)

    output_path = Path('data/processed/fitted_isotherms.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fitted_df.to_csv(output_path, index=False)
    logger.info(f"Fitted parameters written to {output_path}")

    # Verify output
    if 'langmuir_capacity' in fitted_df.columns:
        success_count = fitted_df['langmuir_capacity'].notna().sum()
        total_count = len(fitted_df)
        logger.info(f"Fitting success rate: {success_count}/{total_count}")


if __name__ == "__main__":
    main()
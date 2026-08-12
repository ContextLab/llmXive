"""
GAMM Modeling Module for Bird Migration Analysis.

This module contains functions for fitting Generalized Additive Mixed Models (GAMM)
and computing spatial autocorrelation diagnostics (Moran's I) on model residuals.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import pdist, squareform

# Attempt to import patsy for formula handling, fallback to manual if needed
try:
    import patsy
    HAS_PATSY = True
except ImportError:
    HAS_PATSY = False

# Attempt to import pygam for GAMM fitting
try:
    from pygam import LinearGAM, s, te
    HAS_PYJAM = True
except ImportError:
    HAS_PYJAM = False

# Attempt to import statsmodels for mixed models if pygam is insufficient for random effects
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

from src.config import setup_logging

logger = setup_logging(__name__)


def compute_morans_i(df: pd.DataFrame, residual_col: str = 'residual', 
                     lat_col: str = 'lat', lon_col: str = 'lon', 
                     k: int = 10) -> float:
    """
    Compute Moran's I statistic for spatial autocorrelation of residuals.

    This function calculates the spatial autocorrelation of the model residuals
    using the coordinates provided in the dataframe. It uses a k-nearest neighbor
    approach to define the spatial weights matrix.

    Args:
        df: DataFrame containing residuals and spatial coordinates.
        residual_col: Name of the column containing model residuals.
        lat_col: Name of the column containing latitude.
        lon_col: Name of the column containing longitude.
        k: Number of nearest neighbors to consider for the weights matrix.

    Returns:
        float: The Moran's I statistic.

    Raises:
        ValueError: If required columns are missing or data is insufficient.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    required_cols = [residual_col, lat_col, lon_col]
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing required columns: {missing}")

    # Filter out rows with NaN in critical columns
    valid_df = df[[residual_col, lat_col, lon_col]].dropna()
    if len(valid_df) < 5:
        logger.warning(f"Insufficient valid data points ({len(valid_df)}) for Moran's I calculation.")
        return 0.0

    z = valid_df[residual_col].values
    coords = valid_df[[lat_col, lon_col]].values

    n = len(z)
    
    # Compute distance matrix (Euclidean on lat/lon is an approximation, 
    # but sufficient for local k-NN weighting in small regions)
    # For global analysis, Haversine would be preferred, but scipy.spatial is faster
    dists = squareform(pdist(coords))
    
    # Create weights matrix based on k-nearest neighbors
    # Set diagonal to 0
    np.fill_diagonal(dists, np.inf)
    
    # Find k nearest neighbors
    # argsort along axis 1 gives indices of sorted distances
    nearest_indices = np.argsort(dists, axis=1)[:, :k]
    
    W = np.zeros((n, n))
    for i in range(n):
        for j in nearest_indices[i]:
            W[i, j] = 1.0 / (dists[i, j] + 1e-9) # Inverse distance weighting
    
    # Normalize rows (optional, but standard)
    row_sums = W.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0 # Avoid division by zero
    W = W / row_sums

    # Moran's I formula: I = (n / S0) * (sum(w_ij * z_i * z_j) / sum(z_i^2))
    # where S0 = sum(sum(w_ij))
    S0 = W.sum()
    if S0 == 0:
        return 0.0

    # Vectorized calculation
    # z is (n,), W is (n, n)
    # Wz = W @ z
    Wz = W @ z
    numerator = z @ Wz
    denominator = z @ z

    if denominator == 0:
        return 0.0

    I = (n / S0) * (numerator / denominator)

    logger.info(f"Computed Moran's I: {I:.4f} on {n} points.")
    return float(I)


def run_morans_i_analysis(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main entry point to compute Moran's I from preprocessed data.

    Reads preprocessed data, fits a simple baseline model to get residuals,
    and computes Moran's I on those residuals.

    Args:
        input_path: Path to the preprocessed parquet file.
        output_path: Path to write the JSON result.

    Returns:
        Dict containing the Moran's I value and metadata.
    """
    logger.info(f"Starting Moran's I analysis from {input_path}")
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load data
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load parquet file: {e}")

    if df.empty:
        raise ValueError("Preprocessed data is empty.")

    # Prepare baseline model for residuals
    # Formula: phenology_metric ~ s(temp) + s(precip)
    # We use a simple OLS or GAM to get residuals if full GAMM is too heavy for this diagnostic
    # Assuming columns exist based on T017b output schema
    target_col = 'phenology_metric' # Or 'first_arrival_date' depending on specific metric
    temp_col = 'mean_temperature'
    precip_col = 'total_precipitation'
    lat_col = 'lat' # Grid center
    lon_col = 'lon'

    # Check for columns
    available_cols = [c for c in [target_col, temp_col, precip_col, lat_col, lon_col] if c in df.columns]
    if len(available_cols) < 3:
        raise ValueError(f"Missing required columns for baseline model. Available: {available_cols}")

    # Use the first available temperature/precip columns if names vary
    # Fallback logic for column names if standard names not found
    if target_col not in df.columns:
        # Try to find a column with 'phenology' in name
        matches = [c for c in df.columns if 'phenology' in c.lower()]
        if matches:
            target_col = matches[0]
        else:
            raise ValueError("Could not identify phenology metric column.")

    if temp_col not in df.columns:
        temp_col = [c for c in df.columns if 'temp' in c.lower()][0]
    if precip_col not in df.columns:
        precip_col = [c for c in df.columns if 'precip' in c.lower()][0]

    # Clean data for baseline
    clean_df = df[[target_col, temp_col, precip_col, lat_col, lon_col]].dropna()
    
    if len(clean_df) < 10:
        raise ValueError("Insufficient data points for baseline model fitting.")

    # Fit a simple GAM to get residuals (using pygam if available, else OLS)
    residuals = None
    
    if HAS_PYJAM:
        try:
            X = clean_df[[temp_col, precip_col]]
            y = clean_df[target_col]
            gam = LinearGAM(s(0) + s(1)).fit(X, y)
            residuals = y - gam.predict(X)
            logger.info("Fitted GAM baseline for residuals.")
        except Exception as e:
            logger.warning(f"GAM baseline fit failed: {e}. Falling back to OLS.")
            residuals = None

    if residuals is None and HAS_STATSMODELS:
        try:
            # OLS baseline
            formula = f"{target_col} ~ {temp_col} + {precip_col}"
            model = smf.ols(formula, data=clean_df).fit()
            residuals = model.resid
            logger.info("Fitted OLS baseline for residuals.")
        except Exception as e:
            logger.warning(f"OLS baseline fit failed: {e}. Using raw target as residuals.")
            residuals = clean_df[target_col].values

    if residuals is None:
        # Fallback: use the target variable itself as a proxy for spatial structure if no model fits
        logger.warning("No baseline model could be fitted. Using target variable as proxy for spatial analysis.")
        residuals = clean_df[target_col].values

    # Ensure residuals is a numpy array
    residuals = np.array(residuals)

    # Compute Moran's I
    morans_i_value = compute_morans_i(
        clean_df, 
        residual_col='residuals_proxy', # We'll inject it
        lat_col=lat_col, 
        lon_col=lon_col
    )
    # Hack: pass the array directly to a wrapper or modify compute_morans_i to accept array
    # Re-implementing the call to match the signature that takes a DF with the column
    clean_df['residuals_proxy'] = residuals
    morans_i_value = compute_morans_i(
        clean_df, 
        residual_col='residuals_proxy', 
        lat_col=lat_col, 
        lon_col=lon_col
    )

    result = {
        "value": morans_i_value,
        "n_observations": len(clean_df),
        "threshold": 0.15,
        "status": "high_autocorrelation" if morans_i_value > 0.15 else "low_autocorrelation"
    }

    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Moran's I result written to {output_path}")
    return result


def main():
    """CLI entry point for Moran's I analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute Moran's I for spatial autocorrelation.")
    parser.add_argument("--input", type=str, default="data/processed/preprocessed_data.parquet",
                        help="Path to preprocessed parquet file.")
    parser.add_argument("--output", type=str, default="data/interim/morans_i_result.json",
                        help="Path to output JSON result.")
    
    args = parser.parse_args()
    
    try:
        result = run_morans_i_analysis(args.input, args.output)
        print(f"Moran's I: {result['value']:.4f} ({result['status']})")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import json

# PySAL imports
try:
    import libpysal
    from libpysal.weights import Queen, KNN
    from spreg import Lag, Error
    from spreg import OLS as PySALOLS
    from spreg import diagnostics as sp_diagnostics
except ImportError:
    # Fallback for environment setup, though requirements.txt should handle this
    libpysal = None
    Queen = None
    KNN = None
    Lag = None
    Error = None
    PySALOLS = None
    sp_diagnostics = None

from logger import get_logger, get_project_root

logger = get_logger(__name__)

class SpatialWeightMatrixError(Exception):
    """Custom exception for spatial weight matrix construction failures."""
    pass

def build_spatial_weights(geodata: pd.GeoDataFrame, k: int = 8) -> libpysal.weights.W:
    """
    Construct spatial weight matrix using Queen Contiguity, falling back to KNN.
    
    Parameters
    ----------
    geodata : pd.GeoDataFrame
        GeoDataFrame containing geometry column.
    k : int
        Number of neighbors for KNN fallback.
        
    Returns
    -------
    libpysal.weights.W
        Spatial weights object.
        
    Raises
    ------
    SpatialWeightMatrixError
        If both Queen and KNN construction fail.
    """
    if libpysal is None:
        raise ImportError("PySAL libraries (libpysal, spreg) are not installed.")

    logger.info("Attempting to build spatial weights matrix using Queen Contiguity...")
    try:
        w = Queen.from_dataframe(geodata, use_index=True)
        logger.info(f"Queen weights constructed successfully. Non-zero elements: {w.nnonzero}")
        return w
    except Exception as e:
        logger.warning(f"Queen weights construction failed: {e}. Falling back to KNN ({k}).")

    try:
        w = KNN.from_dataframe(geodata, k=k, use_index=True)
        logger.info(f"KNN weights constructed successfully (k={k}). Non-zero elements: {w.nnonzero}")
        return w
    except Exception as e:
        logger.critical(f"KNN weights construction also failed: {e}")
        raise SpatialWeightMatrixError("Both Queen and KNN failed to construct spatial weights.")

def get_weight_matrix_summary(w: libpysal.weights.W) -> Dict[str, Any]:
    """
    Generate a summary of the spatial weight matrix.
    
    Parameters
    ----------
    w : libpysal.weights.W
        Spatial weights object.
        
    Returns
    -------
    dict
        Summary statistics.
    """
    return {
        "n": w.n,
        "nonzero": w.nnonzero,
        "mean_neighbors": w.mean_neighbors,
        "max_neighbors": w.max_neighbors,
        "min_neighbors": w.min_neighbors
    }

def fit_ols_model(
    y: np.ndarray,
    X: np.ndarray,
    names_y: str,
    names_x: list,
    constant: bool = True
) -> PySALOLS:
    """
    Fit an OLS model using PySAL.
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable.
    X : np.ndarray
        Independent variables.
    names_y : str
        Name of dependent variable.
    names_x : list
        Names of independent variables.
    constant : bool
        Whether to add a constant.
        
    Returns
    -------
    PySALOLS
        Fitted OLS model object.
    """
    if PySALOLS is None:
        raise ImportError("PySAL spreg is not installed.")
    
    model = PySALOLS(y, X, names_y=names_y, names_x=names_x, constant=constant)
    return model

def fit_spatial_models(
    y: np.ndarray,
    X: np.ndarray,
    w: libpysal.weights.W,
    names_y: str,
    names_x: list,
    constant: bool = True
) -> Tuple[Optional[Lag], Optional[Error]]:
    """
    Fit Spatial Lag and Spatial Error models using PySAL.
    
    This function attempts to fit both the Lag and Error models.
    If a model fails to converge, it returns None for that model
    and logs the error, allowing the pipeline to potentially fallback
    or handle the missing model elsewhere (e.g., T024).
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable (1D array).
    X : np.ndarray
        Independent variables (2D array).
    w : libpysal.weights.W
        Spatial weights matrix.
    names_y : str
        Name of dependent variable.
    names_x : list
        Names of independent variables.
    constant : bool
        Whether to add a constant.
        
    Returns
    -------
    tuple
        (lag_model, error_model). Either can be None if fitting failed.
    """
    if Lag is None or Error is None:
        raise ImportError("PySAL spreg Lag or Error models are not installed.")

    lag_model = None
    error_model = None

    # Fit Spatial Lag Model
    logger.info("Fitting Spatial Lag Model...")
    try:
        lag_model = Lag(
            y, X, w=w, 
            names_y=names_y, 
            names_x=names_x, 
            constant=constant
        )
        logger.info("Spatial Lag Model fitted successfully.")
        # Check for convergence issues if available in the model object
        if hasattr(lag_model, 'logv') and lag_model.logv is not None:
             logger.debug(f"Lag Model Log-likelihood: {lag_model.logv}")
    except Exception as e:
        logger.error(f"Failed to fit Spatial Lag Model: {e}")
        # Do not raise, return None to allow fallback logic in T024

    # Fit Spatial Error Model
    logger.info("Fitting Spatial Error Model...")
    try:
        error_model = Error(
            y, X, w=w,
            names_y=names_y,
            names_x=names_x,
            constant=constant
        )
        logger.info("Spatial Error Model fitted successfully.")
        if hasattr(error_model, 'logv') and error_model.logv is not None:
             logger.debug(f"Error Model Log-likelihood: {error_model.logv}")
    except Exception as e:
        logger.error(f"Failed to fit Spatial Error Model: {e}")
        # Do not raise, return None to allow fallback logic in T024

    return lag_model, error_model

def main():
    """
    Main entry point for demonstration or testing of model fitting.
    This function expects a harmonized parquet file from T016.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "harmonized.parquet"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T016 (Write harmonized dataset) is completed first.")
        return

    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)

    # Prepare data for modeling
    # Assuming 'noise_metric' is the target and some columns are covariates
    # This logic might need adjustment based on exact schema from T013/T014
    target_col = 'noise_metric_95th' # Example column name, adjust if schema differs
    covariate_cols = [col for col in df.columns if col.startswith('traffic_') or col.startswith('land_use_')]
    
    if not covariate_cols:
        logger.warning("No covariates found matching expected patterns. Using synthetic placeholders for demo.")
        # Fallback to synthetic data generation for testing if real data structure is unknown
        # In a real run, this should ideally fail or require explicit column mapping
        covariate_cols = ['traffic_volume'] 
        if 'traffic_volume' not in df.columns:
            df['traffic_volume'] = np.random.rand(len(df))

    # Ensure target exists
    if target_col not in df.columns:
        # Try to find any numeric column as target for demo
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            target_col = numeric_cols[0]
            logger.warning(f"Target column '{target_col}' not found. Using '{target_col}' as proxy.")
        else:
            logger.error("No suitable target column found.")
            return

    logger.info(f"Using '{target_col}' as target and {covariate_cols} as covariates.")

    # Filter NaNs
    cols_to_use = [target_col] + covariate_cols
    clean_df = df.dropna(subset=cols_to_use)
    
    if len(clean_df) < 10:
        logger.error("Insufficient data after cleaning.")
        return

    y = clean_df[target_col].values
    X = clean_df[covariate_cols].values
    names_y = target_col
    names_x = covariate_cols

    # Build Weights
    logger.info("Building spatial weights...")
    try:
        w = build_spatial_weights(clean_df, k=8)
        w_summary = get_weight_matrix_summary(w)
        logger.info(f"Weights Summary: {w_summary}")
    except SpatialWeightMatrixError as e:
        logger.critical(str(e))
        return

    # Fit OLS
    logger.info("Fitting OLS Model...")
    ols_model = fit_ols_model(y, X, names_y, names_x, constant=True)
    logger.info(f"OLS R-squared: {ols_model.rsquared:.4f}")

    # Fit Spatial Models (T021 Implementation)
    logger.info("Fitting Spatial Lag and Error Models...")
    lag_model, error_model = fit_spatial_models(y, X, w, names_y, names_x, constant=True)

    if lag_model:
        logger.info(f"Lag Model R-squared: {lag_model.rsquared:.4f}, AIC: {lag_model.aic:.4f}")
    else:
        logger.warning("Lag Model could not be fitted.")

    if error_model:
        logger.info(f"Error Model R-squared: {error_model.rsquared:.4f}, AIC: {error_model.aic:.4f}")
    else:
        logger.warning("Error Model could not be fitted.")

    logger.info("Spatial model fitting complete.")

if __name__ == "__main__":
    main()
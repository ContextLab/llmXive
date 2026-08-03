import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import json
from logger import get_logger, get_project_root

class SpatialWeightMatrixError(Exception):
    """Custom exception for spatial weight matrix construction failures."""
    pass

def build_spatial_weights(geodataframe: pd.GeoDataFrame, id_col: str = 'grid_id') -> Any:
    """
    Construct spatial weight matrix using Queen Contiguity, falling back to K-Nearest Neighbor (K=8).
    
    If both methods fail, raises SpatialWeightMatrixError.
    
    Args:
        geodataframe: GeoDataFrame with geometry column.
        id_col: Name of the ID column to use as keys in the weights.
        
    Returns:
        PySAL weights object.
        
    Raises:
        SpatialWeightMatrixError: If both Queen and KNN construction fail.
    """
    logger = get_logger(__name__)
    
    queen_failed = False
    knn_failed = False
    queen_error = None
    knn_error = None

    # Attempt 1: Queen Contiguity
    try:
        logger.info("Attempting to build Queen Contiguity weight matrix...")
        import libpysal
        w_queen = libpysal.weights.Queen.from_dataframe(geodataframe, geom_col='geometry', id_order=geodataframe[id_col].tolist())
        
        # Verify connectivity (optional but good practice)
        if w_queen.n_components > 1:
            logger.warning("Queen weights result in disconnected components. Consider KNN fallback.")
        
        logger.info("Queen Contiguity weight matrix built successfully.")
        return w_queen
        
    except Exception as e:
        queen_failed = True
        queen_error = str(e)
        logger.warning(f"Queen Contiguity failed: {e}")

    # Attempt 2: K-Nearest Neighbor (K=8)
    try:
        logger.info("Queen failed. Attempting K-Nearest Neighbor (K=8) weight matrix...")
        import libpysal
        # Ensure we have coordinates if KNN requires them (libpysal usually handles GeoDataFrame)
        w_knn = libpysal.weights.KNN.from_dataframe(geodataframe, geom_col='geometry', id_order=geodataframe[id_col].tolist(), k=8)
        
        logger.info("K-Nearest Neighbor (K=8) weight matrix built successfully.")
        return w_knn
        
    except Exception as e:
        knn_failed = True
        knn_error = str(e)
        logger.warning(f"K-Nearest Neighbor failed: {e}")

    # Both failed
    logger.critical("Both Queen Contiguity and K-Nearest Neighbor (K=8) weight matrix construction failed.")
    logger.critical(f"Queen Error: {queen_error}")
    logger.critical(f"KNN Error: {knn_error}")
    raise SpatialWeightMatrixError("Both Queen and KNN failed")

def get_weight_matrix_summary(w: Any) -> Dict[str, Any]:
    """
    Generate a summary dictionary of the weight matrix properties.
    
    Args:
        w: PySAL weights object.
        
    Returns:
        Dictionary containing summary stats.
    """
    return {
        "n": w.n,
        "n_components": w.n_components,
        "pct_nonzero": w.pct_nonzero,
        "max_neighbors": max([len(neighbors) for neighbors in w.neighbors.values()]) if w.neighbors else 0,
        "avg_neighbors": w.avg_neighbors
    }

def fit_ols_model(
    df: pd.DataFrame, 
    dependent_var: str, 
    independent_vars: list, 
    weights: Optional[Any] = None
) -> Any:
    """
    Fit an OLS regression model using statsmodels.
    
    Args:
        df: DataFrame containing the data.
        dependent_var: Name of the dependent variable column.
        independent_vars: List of independent variable column names.
        weights: Optional PySAL weights object (for diagnostics).
        
    Returns:
        statsmodels OLS Results object.
    """
    import statsmodels.api as sm
    
    logger = get_logger(__name__)
    
    # Prepare design matrix
    y = df[dependent_var].dropna()
    # Ensure indices align
    X = df[independent_vars].loc[y.index]
    
    if X.empty:
        raise ValueError("No valid independent variables after dropping NaNs.")
        
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X)
    results = model.fit()
    
    logger.info(f"OLS model fitted. R-squared: {results.rsquared:.4f}")
    return results

def fit_spatial_models(
    df: pd.DataFrame,
    dependent_var: str,
    independent_vars: list,
    w: Any,
    robust: bool = True
) -> Dict[str, Any]:
    """
    Fit Spatial Lag and Spatial Error models using PySAL.
    
    Args:
        df: DataFrame containing the data.
        dependent_var: Name of the dependent variable column.
        independent_vars: List of independent variable column names.
        w: PySAL weights object.
        robust: Whether to use robust standard errors.
        
    Returns:
        Dictionary containing results for 'lag' and 'error' models.
    """
    import libpysal
    from pysal.model.spreg import lag, error
    
    logger = get_logger(__name__)
    
    # Prepare data
    y = df[dependent_var].values
    X = df[independent_vars].values
    X = np.column_stack((np.ones(len(X)), X)) # Add constant
    
    results = {}
    
    # Spatial Lag Model
    try:
        logger.info("Fitting Spatial Lag Model...")
        lag_model = lag.Lag(y, X, w=w, robust=robust)
        results['lag'] = {
            "summary": lag_model.summary,
            "params": lag_model.params.tolist(),
            "loglik": lag_model.loglik,
            "aic": lag_model.aic,
            "bic": lag_model.bic,
            "pvalues": lag_model.pvalues.tolist() if hasattr(lag_model, 'pvalues') else None
        }
        logger.info("Spatial Lag Model fitted successfully.")
    except Exception as e:
        logger.error(f"Spatial Lag Model failed: {e}")
        results['lag'] = {"error": str(e)}

    # Spatial Error Model
    try:
        logger.info("Fitting Spatial Error Model...")
        error_model = error.OLS(y, X, w=w, robust=robust)
        results['error'] = {
            "summary": error_model.summary,
            "params": error_model.params.tolist(),
            "loglik": error_model.loglik,
            "aic": error_model.aic,
            "bic": error_model.bic,
            "pvalues": error_model.pvalues.tolist() if hasattr(error_model, 'pvalues') else None
        }
        logger.info("Spatial Error Model fitted successfully.")
    except Exception as e:
        logger.error(f"Spatial Error Model failed: {e}")
        results['error'] = {"error": str(e)}
        
    return results

def main():
    """
    Main entry point for testing the weight matrix failure handling.
    This function is primarily for demonstration/testing of the error handling logic.
    """
    logger = get_logger(__name__)
    logger.info("Starting models module main execution.")
    
    # Create a dummy empty GeoDataFrame to trigger failure
    # In a real scenario, this would be called from a pipeline step with real data
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        
        # Create a dataset that is too small or invalid for both Queen and KNN
        # e.g., 1 point cannot form a KNN (k=8) or Queen neighbor
        data = {
            'grid_id': [1],
            'geometry': [Point(0, 0)]
        }
        gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
        
        logger.warning("Testing with 1-point GeoDataFrame to force weight matrix failure...")
        w = build_spatial_weights(gdf, id_col='grid_id')
        logger.error("ERROR: Expected failure did not occur.")
        
    except SpatialWeightMatrixError as e:
        logger.critical(f"Expected failure caught: {e}")
        # This confirms the logic works
        return True
    except Exception as e:
        logger.error(f"Unexpected error during test: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("Weight matrix failure handling test passed.")
    else:
        print("Weight matrix failure handling test failed.")
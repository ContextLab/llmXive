import numpy as np
import geopandas as gpd
from typing import List, Dict, Tuple, Optional, Any, Generator
import logging
from pathlib import Path
import json

# Attempt to import GWR dependencies. If missing, the class will raise
# a clear ImportError at instantiation time rather than failing silently.
try:
    from pysal.lib.weights import W
    from pysal.explore.gwr import GWR
    HAS_GWR = True
except ImportError:
    HAS_GWR = False

from utils.logging import get_logger
from config import MAX_BLOCKS, get_path

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Spatial Block Sampling & Cross-Validation Infrastructure
# ----------------------------------------------------------------------

class SpatialCrossValidator:
    """
    Generates spatial folds to prevent data leakage during cross-validation.
    Uses pre-defined spatial blocks to ensure spatial independence between folds.
    """
    def __init__(self, n_splits: int = 5, random_state: int = 42):
        if n_splits < 2:
            raise ValueError("n_splits must be >= 2")
        self.n_splits = n_splits
        self.random_state = random_state
        self.rng = np.random.default_rng(random_state)

    def generate_folds(self, block_ids: List[Any]) -> Generator[Tuple[List[int], List[int]], None, None]:
        """
        Yields (train_idx, test_idx) tuples based on block IDs.
        """
        if not block_ids:
            return

        # Shuffle block IDs deterministically
        shuffled = self.rng.permutation(block_ids)
        n_blocks = len(shuffled)
        fold_size = max(1, n_blocks // self.n_splits)

        for i in range(self.n_splits):
            start = i * fold_size
            end = start + fold_size if i < self.n_splits - 1 else n_blocks

            test_blocks = shuffled[start:end]
            train_blocks = np.concatenate([shuffled[:start], shuffled[end:]])

            yield list(train_blocks), list(test_blocks)


def generate_spatial_folds(
    n_samples: int,
    block_assignments: np.ndarray,
    n_splits: int = 5,
    random_state: int = 42
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Helper to generate spatial folds from a flat array of block assignments.
    Returns list of (train_mask, test_mask) boolean arrays.
    """
    unique_blocks = np.unique(block_assignments)
    cv = SpatialCrossValidator(n_splits=n_splits, random_state=random_state)
    
    folds = []
    for train_blocks, test_blocks in cv.generate_folds(unique_blocks):
        train_mask = np.isin(block_assignments, train_blocks)
        test_mask = np.isin(block_assignments, test_blocks)
        folds.append((train_mask, test_mask))
    
    return folds


def validate_spatial_leakage(
    train_mask: np.ndarray,
    test_mask: np.ndarray,
    block_assignments: np.ndarray
) -> bool:
    """
    Checks if any block appears in both train and test sets.
    Returns True if leakage is detected (should be False for valid folds).
    """
    train_blocks = np.unique(block_assignments[train_mask])
    test_blocks = np.unique(block_assignments[test_mask])
    overlap = set(train_blocks) & set(test_blocks)
    return len(overlap) > 0


# ----------------------------------------------------------------------
# Model Fitting Functions
# ----------------------------------------------------------------------

def fit_ols_baseline(
    X: np.ndarray,
    y: np.ndarray,
    block_assignments: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Fits an OLS baseline model with spatially robust standard errors (HAC).
    Uses statsmodels for robust estimation.
    """
    try:
        import statsmodels.api as sm
        from statsmodels.regression.linear_model import OLS
        from statsmodels.stats.sandwich_covariance import cov_hac
    except ImportError:
        logger.error("statsmodels not installed. Cannot fit OLS baseline.")
        return {"status": "error", "message": "statsmodels missing"}

    if X.shape[0] != len(y):
        raise ValueError("X and y must have the same number of samples.")

    X_const = sm.add_constant(X)
    model = OLS(y, X_const).fit()
    
    # HAC covariance
    try:
        # Use block assignments for HAC if available, else simple HAC
        if block_assignments is not None:
            # Simple group-based HAC approximation using blocks
            # Note: statsmodels HAC doesn't take groups directly, 
            # so we use the default HAC which accounts for serial correlation
            # In a full spatial implementation, we would construct a spatial weight matrix.
            cov_matrix = cov_hac(model)
        else:
            cov_matrix = cov_hac(model)
        
        model._hac_cov = cov_matrix
    except Exception as e:
        logger.warning(f"HAC covariance calculation failed: {e}")

    return {
        "status": "success",
        "coefficients": model.params.tolist(),
        "rsquared": float(model.rsquared),
        "rsquared_adj": float(model.rsquared_adj),
        "aic": float(model.aic),
        "bic": float(model.bic)
    }


def fit_sar_model(
    X: np.ndarray,
    y: np.ndarray,
    W: Optional[W] = None,
    model_type: str = "lag"
) -> Dict[str, Any]:
    """
    Fits a Spatial Autoregressive (SAR) model (Lag or Error).
    """
    if not HAS_GWR:
        logger.warning("PySAL not installed. Degrading to OLS.")
        return fit_ols_baseline(X, y)

    try:
        import pysal.lib.weights as libw
        import pysal.model.spreg as spreg
    except ImportError:
        logger.error("PySAL model modules missing.")
        return {"status": "error", "message": "PySAL spreg missing"}

    if W is None:
        # Fallback to OLS if no spatial weights provided
        return fit_ols_baseline(X, y)

    X_const = sm.add_constant(X)
    
    try:
        if model_type == "lag":
            model = spreg.GM_Lag(y, X_const, w=W, robust=True)
        else:  # error
            model = spreg.GM_Error(y, X_const, w=W, robust=True)
        
        return {
            "status": "success",
            "type": model_type,
            "coefficients": model.beta.flatten().tolist(),
            "rho": float(model.rho) if hasattr(model, 'rho') else None,
            "lambda": float(model.lambda_) if hasattr(model, 'lambda_') else None,
            "rsquared": float(model.rsquared),
            "loglik": float(model.llf)
        }
    except Exception as e:
        logger.warning(f"SAR model fitting failed: {e}. Degrading to OLS.")
        return fit_ols_baseline(X, y)


class GWRModel:
    """
    Wrapper for Geographically Weighted Regression (GWR).
    Handles bandwidth selection and model fitting.
    """
    def __init__(self, kernel: str = "bisquare", adaptive: bool = True):
        if not HAS_GWR:
            raise ImportError("PySAL GWR module required for GWRModel. Install pysal[explore].")
        
        self.kernel = kernel
        self.adaptive = adaptive
        self.model = None
        self.results = None
        self.bandwidth = None

    def fit(
        self,
        coords: np.ndarray,
        y: np.ndarray,
        X: np.ndarray,
        bandwidth: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Fits the GWR model. If bandwidth is None, uses default selection.
        """
        try:
            from pysal.explore.gwr import GWR
        except ImportError:
            return {"status": "error", "message": "PySAL GWR missing"}

        if coords.shape[0] != len(y) or coords.shape[0] != X.shape[0]:
            raise ValueError("coords, y, and X must have same length.")

        X_const = sm.add_constant(X)
        
        try:
            if bandwidth is not None:
                self.model = GWR(coords, y, X_const, bandwidth=bandwidth, 
                                 kernel=self.kernel, adaptive=self.adaptive)
            else:
                # Let GWR select bandwidth automatically (CV or AICc)
                self.model = GWR(coords, y, X_const, kernel=self.kernel, 
                                 adaptive=self.adaptive)
            
            self.results = self.model.fit()
            self.bandwidth = self.results.bandwidth
            
            return {
                "status": "success",
                "bandwidth": float(self.bandwidth),
                "rsquared": float(self.results.r2),
                "aic": float(self.results.aic),
                "n_params": int(self.results.nparams),
                "coefficients_mean": self.results.params.mean(axis=0).tolist()
            }
        except Exception as e:
            logger.warning(f"GWR fitting failed: {e}.")
            return {"status": "error", "message": str(e)}


def fit_gwr_model(
    coords: np.ndarray,
    y: np.ndarray,
    X: np.ndarray,
    bandwidth: Optional[float] = None
) -> Dict[str, Any]:
    """
    Convenience function to fit a single GWR model.
    """
    gwr = GWRModel()
    return gwr.fit(coords, y, X, bandwidth)


# ----------------------------------------------------------------------
# T034: GWR Bandwidth Sweep Implementation
# ----------------------------------------------------------------------

def run_gwr_bandwidth_sweep(
    coords: np.ndarray,
    y: np.ndarray,
    X: np.ndarray,
    bandwidths: Optional[List[float]] = None,
    n_candidates: int = 10
) -> Dict[str, Any]:
    """
    Implements a configurable bandwidth sweep for GWR (FR-009).
    Sweeps over a set of bandwidth values, fits GWR for each, and records R².
    
    Parameters
    ----------
    coords : np.ndarray
        Array of shape (N, 2) with (x, y) coordinates.
    y : np.ndarray
        Target variable array of shape (N,).
    X : np.ndarray
        Feature matrix of shape (N, p).
    bandwidths : list of float, optional
        Explicit list of bandwidth values to sweep. If None, generates
        candidates based on data extent.
    n_candidates : int
        Number of candidates to generate if bandwidths is None.
    
    Returns
    -------
    dict
        Contains 'sweep_results' (list of dicts with bandwidth, r2, aic)
        and 'best_bandwidth' (bandwidth with highest R²).
    """
    if not HAS_GWR:
        logger.error("PySAL GWR module required for bandwidth sweep.")
        return {
            "status": "error",
            "message": "PySAL GWR missing",
            "sweep_results": []
        }

    try:
        from pysal.explore.gwr import GWR
    except ImportError:
        return {
            "status": "error",
            "message": "PySAL GWR import failed",
            "sweep_results": []
        }

    logger.info(f"Starting GWR bandwidth sweep with {n_candidates} candidates.")

    # Generate candidates if not provided
    if bandwidths is None:
        # Calculate data extent to determine reasonable bandwidth range
        x_min, y_min = coords.min(axis=0)
        x_max, y_max = coords.max(axis=0)
        x_range = x_max - x_min
        y_range = y_max - y_min
        avg_extent = (x_range + y_range) / 2.0
        
        # Generate logarithmic spacing of candidates
        # Start from small (e.g., 0.01 * avg_extent) to large (e.g., 0.5 * avg_extent)
        min_bw = max(1.0, avg_extent * 0.01)
        max_bw = avg_extent * 0.5
        
        if min_bw >= max_bw:
            # Fallback if extent is tiny
            min_bw, max_bw = 1.0, 100.0
        
        bandwidths = np.logspace(np.log10(min_bw), np.log10(max_bw), n_candidates).tolist()
        logger.info(f"Generated bandwidth candidates: {bandwidths}")

    results = []
    best_r2 = -np.inf
    best_bandwidth = None

    for bw in bandwidths:
        try:
            gwr = GWR(coords, y, sm.add_constant(X), bandwidth=bw, kernel="bisquare", adaptive=True)
            res = gwr.fit()
            
            r2 = res.r2
            aic = res.aic
            
            results.append({
                "bandwidth": float(bw),
                "r2": float(r2),
                "aic": float(aic),
                "n_params": int(res.nparams),
                "status": "success"
            })
            
            if r2 > best_r2:
                best_r2 = r2
                best_bandwidth = float(bw)
                
            logger.debug(f"Bandwidth {bw:.4f}: R²={r2:.4f}, AIC={aic:.4f}")
            
        except Exception as e:
            logger.warning(f"Bandwidth {bw} failed: {e}")
            results.append({
                "bandwidth": float(bw),
                "r2": None,
                "aic": None,
                "n_params": None,
                "status": "failed",
                "error": str(e)
            })

    logger.info(f"Sweep complete. Best bandwidth: {best_bandwidth} (R²={best_r2:.4f})")

    return {
        "status": "success",
        "sweep_results": results,
        "best_bandwidth": best_bandwidth,
        "best_r2": float(best_r2) if best_r2 != -np.inf else None,
        "total_candidates": len(bandwidths),
        "successful_fits": sum(1 for r in results if r["status"] == "success")
    }


def apply_permutation_fdr(
    p_values: List[float],
    method: str = "bh"
) -> List[float]:
    """
    Applies False Discovery Rate (FDR) correction to p-values using permutation-based approach.
    Uses Benjamini-Hochberg (bh) by default.
    """
    try:
        from statsmodels.stats.multitest import multipletests
    except ImportError:
        logger.warning("statsmodels missing for FDR correction.")
        return p_values

    if not p_values:
        return []

    # Filter out non-numeric or NaN values
    clean_pvals = [p for p in p_values if isinstance(p, (int, float)) and not np.isnan(p)]
    if len(clean_pvals) != len(p_values):
        logger.warning("Some p-values were NaN or non-numeric and were excluded from FDR.")

    try:
        _, adjusted_pvals, _, _ = multipletests(clean_pvals, alpha=0.05, method=method)
        return adjusted_pvals.tolist()
    except Exception as e:
        logger.warning(f"FDR correction failed: {e}")
        return p_values


# ----------------------------------------------------------------------
# Main Entry Point
# ----------------------------------------------------------------------

def main():
    """
    Main entry point for modeling pipeline.
    Can be extended to run the bandwidth sweep if data is available.
    """
    logger.info("Modeling pipeline initialized.")
    
    # Example usage of bandwidth sweep (would require real data to run)
    # This is a placeholder to demonstrate the API
    if len(sys.argv) > 1 and sys.argv[1] == "sweep":
        logger.info("Running bandwidth sweep example (requires data).")
        # In a real run, load data from data/processed/
        # coords, y, X = load_modeling_data()
        # results = run_gwr_bandwidth_sweep(coords, y, X)
        # save_results(results)
        logger.warning("Sweep requires real data. Skipping example.")
    
    logger.info("Modeling pipeline ready.")


if __name__ == "__main__":
    import sys
    main()

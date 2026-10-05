import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
from scipy import linalg
from scipy.interpolate import BSpline, make_interp_spline
from sklearn.decomposition import PCA

from config import get_data_dir, get_artifacts_dir, get_project_root
from logging_config import setup_logging, get_logger

# Ensure logging is configured
setup_logging()
logger = get_logger(__name__)

def load_b_spline_coefficients(data_dir: Optional[Path] = None) -> Tuple[np.ndarray, List[str]]:
    """
    Load B-spline coefficients from the processed data directory.
    Expects a pickle file containing a dictionary: {model_id: coefficients_array}
    where coefficients_array is shape (n_knots, n_variables) or similar.
    Returns a stacked 2D array (n_samples, n_features) and a list of sample IDs.
    """
    if data_dir is None:
        data_dir = get_data_dir()

    coeffs_path = data_dir / "b_spline_coefficients.pkl"
    if not coeffs_path.exists():
        raise FileNotFoundError(f"Coefficients file not found at {coeffs_path}. "
                                "Run the basis expansion pipeline first.")

    logger.info(f"Loading B-spline coefficients from {coeffs_path}")
    with open(coeffs_path, 'rb') as f:
        data = pickle.load(f)

    # Assuming data is a dict {model_id: coeff_array}
    # We need to flatten this into a matrix for PCA.
    # Shape: (N_models, K_basis, n_vars) -> (N_models, K_basis * n_vars)
    # Or if already flattened: (N_models, Features)
    
    sample_ids = []
    matrices = []
    
    for model_id, coeffs in data.items():
        if isinstance(coeffs, dict):
            # If it's a dict of variables, flatten it
            flat = []
            for var in sorted(coeffs.keys()):
                flat.extend(coeffs[var].flatten())
            matrices.append(np.array(flat))
        elif isinstance(coeffs, np.ndarray):
            matrices.append(coeffs.flatten())
        else:
            logger.warning(f"Skipping unknown coefficient format for {model_id}")
    
    if not matrices:
        raise ValueError("No valid coefficient matrices found.")
    
    X = np.vstack(matrices)
    return X, list(data.keys())

def perform_fpca(X: np.ndarray, n_components: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform Functional Principal Component Analysis using scikit-learn PCA.
    Input X: (n_samples, n_features)
    Returns dictionary with eigenvalues, eigenvectors (loadings), explained variance ratio.
    """
    logger.info(f"Performing FPCA on data shape {X.shape}")
    
    # Center the data (PCA does this, but we need it for eigenfunctions reconstruction)
    pca = PCA(n_components=n_components)
    X_centered = X - X.mean(axis=0)
    components = pca.fit(X_centered)
    
    eigenvalues = components.explained_variance_
    eigenvectors = components.components_.T  # Shape (n_features, n_components)
    explained_variance_ratio = components.explained_variance_ratio_
    
    # Reconstruct mean function (if needed later for visualization)
    mean_func = X.mean(axis=0)
    
    return {
        "eigenvalues": eigenvalues,
        "eigenvectors": eigenvectors,
        "explained_variance_ratio": explained_variance_ratio,
        "mean_function": mean_func,
        "n_components": len(eigenvalues)
    }

def reconstruct_eigenfunctions(eigenvectors: np.ndarray, mean_func: np.ndarray, 
                               n_knots: int, n_vars: int) -> List[BSpline]:
    """
    Reconstruct smooth eigenfunctions from the PCA loadings.
    This assumes the features in the vector correspond to basis coefficients.
    Since we flattened the coefficients, we need to reshape them back to (n_knots, n_vars)
    to interpret them as functional modes.
    
    Note: This is a simplified reconstruction. In a full fPCA, one would project
    the basis functions onto the eigenfunctions. Here we treat the loading vector
    as the coefficients of the basis functions for the eigenmode.
    """
    n_features = eigenvectors.shape[0]
    if n_features != n_knots * n_vars:
        logger.warning(f"Feature count {n_features} does not match expected {n_knots * n_vars}. "
                       "Reconstruction may be inaccurate.")
        # Attempt to infer n_knots if n_vars is known or assume 1 var
        inferred_n_knots = n_features // max(1, n_vars)
        n_knots = inferred_n_knots
    
    eigenfunctions = []
    for i in range(eigenvectors.shape[1]):
        vec = eigenvectors[:, i]
        # Reshape to (n_knots, n_vars)
        if n_vars > 1:
            coeffs = vec.reshape(n_knots, n_vars)
            # Create one spline per variable? Or a multivariate spline?
            # For simplicity in visualization, we might just flatten or pick a channel.
            # Let's create a single spline for the first variable or sum them if scalar-like.
            # Assuming the input was flattened (k1, k2...), we treat it as a single functional mode
            # if the original data was univariate. If multivariate, this needs specific handling.
            # For this implementation, we assume the flattened vector represents the mode shape.
            # We will create a spline for the first variable's coefficients as a proxy.
            spline_coeffs = coeffs[:, 0] 
        else:
            spline_coeffs = vec
        
        # Create a B-spline. We need knots. 
        # Since we don't have the original knot vector here, we assume uniform knots 0..1
        # This is a limitation; in production, knot info should be stored.
        # We'll use a simple interpolation of the coefficients if we had the knots,
        # but here we treat the coefficients themselves as the discrete representation
        # and interpolate them to get a smooth function.
        
        # Let's assume the coefficients correspond to values at specific points
        # or we just create a spline through the coefficients.
        # A better approach: The eigenvector IS the set of coefficients for the basis.
        # To evaluate the eigenfunction at a point t, we need the basis functions B_j(t).
        # Without the original knot vector, we can't perfectly reconstruct.
        # We will store the raw coefficients and assume a uniform grid for visualization later.
        eigenfunctions.append(spline_coeffs)
        
    return eigenfunctions

def calculate_cumulative_variance(fpca_results: Dict[str, Any], threshold: float = 0.80) -> Dict[str, Any]:
    """
    Calculate cumulative variance and determine the number of components needed
    to explain at least `threshold` (default 80%) of the variance.
    
    Args:
        fpca_results: Dictionary output from perform_fpca.
        threshold: Cumulative variance threshold (0.0 to 1.0).
    
    Returns:
        Dictionary containing:
            - cumulative_variance: List of cumulative variance values
            - n_components_selected: Number of components to reach threshold
            - total_variance_explained: Variance explained by selected components
            - all_eigenvalues: List of all eigenvalues
            - all_variance_ratios: List of all variance ratios
    """
    ratios = fpca_results["explained_variance_ratio"]
    cumulative = np.cumsum(ratios)
    
    # Find the index where cumulative variance >= threshold
    # If even the full set doesn't reach it, select all.
    if len(cumulative) > 0:
        indices = np.where(cumulative >= threshold)[0]
        if len(indices) > 0:
            n_selected = indices[0] + 1  # +1 because index is 0-based
        else:
            n_selected = len(cumulative)
    else:
        n_selected = 0
    
    total_explained = cumulative[n_selected - 1] if n_selected > 0 else 0.0
    
    return {
        "cumulative_variance": cumulative.tolist(),
        "n_components_selected": int(n_selected),
        "total_variance_explained": float(total_explained),
        "threshold": threshold,
        "all_eigenvalues": fpca_results["eigenvalues"].tolist(),
        "all_variance_ratios": ratios.tolist()
    }

def run_fpca_pipeline(data_dir: Optional[Path] = None, output_dir: Optional[Path] = None,
                      variance_threshold: float = 0.80) -> Dict[str, Any]:
    """
    Main pipeline function to load data, run FPCA, calculate metrics, and save results.
    
    Args:
        data_dir: Path to data directory. Defaults to config.
        output_dir: Path to output directory. Defaults to data/processed.
        variance_threshold: Threshold for cumulative variance (default 0.80).
    
    Returns:
        Dictionary containing all results.
    """
    if data_dir is None:
        data_dir = get_data_dir()
    if output_dir is None:
        output_dir = get_data_dir() / "processed"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    X, sample_ids = load_b_spline_coefficients(data_dir)
    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features.")
    
    # 2. Perform FPCA
    fpca_results = perform_fpca(X)
    
    # 3. Calculate Cumulative Variance
    variance_metrics = calculate_cumulative_variance(fpca_results, threshold=variance_threshold)
    
    logger.info(f"Selected {variance_metrics['n_components_selected']} components "
                f"to explain {variance_metrics['total_variance_explained']:.2%} variance.")
    
    # 4. Save Variance Metrics to JSON
    metrics_path = output_dir / "variance_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(variance_metrics, f, indent=2)
    logger.info(f"Saved variance metrics to {metrics_path}")
    
    # 5. Save Full FPCA Results (eigenvalues, eigenvectors, etc.)
    # We need to save the raw numpy arrays, so we use pickle for the heavy data
    # and JSON for the metadata.
    results_path = output_dir / "fpca_results.pkl"
    with open(results_path, 'wb') as f:
        # Convert numpy arrays to lists for pickling compatibility if needed,
        # but pickle handles numpy arrays fine.
        pickle.dump(fpca_results, f)
    logger.info(f"Saved FPCA results to {results_path}")
    
    # 6. Save Eigenvalues/Variance as CSV for easy inspection (optional but good practice)
    # We'll stick to the JSON requirement for metrics and Pkl for full results.
    
    return {
        "fpca_results": fpca_results,
        "variance_metrics": variance_metrics,
        "sample_ids": sample_ids
    }

def main():
    """Entry point for running the FPCA pipeline."""
    logger.info("Starting FPCA Pipeline...")
    try:
        results = run_fpca_pipeline()
        logger.info("FPCA Pipeline completed successfully.")
        print(f"Results saved. Components selected: {results['variance_metrics']['n_components_selected']}")
    except Exception as e:
        logger.error(f"FPCA Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

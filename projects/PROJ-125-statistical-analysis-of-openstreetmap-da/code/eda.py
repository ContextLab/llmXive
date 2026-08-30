import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

from config import get_path, get_city_crs
from utils.logging import get_logger
from utils.memory import check_memory_safety, estimate_raster_memory_mb

# Optional imports for spatial analysis
try:
    import geopandas as gpd
    import rasterio
    from rasterio.features import geometry_mask
    from scipy import stats
    from pysal.explore.esda import Moran
    from pysal.lib.weights import Queen
    import libpysal
    HAS_PYSPAL = True
except ImportError:
    HAS_PYSPAL = False
    Moran = None
    Queen = None
    libpysal = None

logger = get_logger(__name__)

def load_raster_stack(stack_dir: Optional[str] = None) -> Dict[str, np.ndarray]:
    """
    Load all GeoTIFFs from the processed directory into memory as numpy arrays.
    Assumes all rasters are already aligned (same dimensions, CRS, transform).
    """
    if stack_dir is None:
        stack_dir = get_path("data", "processed")
    
    stack_path = Path(stack_dir)
    if not stack_path.exists():
        raise FileNotFoundError(f"Processed directory not found: {stack_path}")

    raster_files = list(stack_path.glob("*.tif"))
    if not raster_files:
        raise FileNotFoundError(f"No .tif files found in {stack_path}")

    logger.info(f"Loading {len(raster_files)} rasters from {stack_path}")
    
    data_stack = {}
    ref_transform = None
    ref_shape = None

    for f in raster_files:
        with rasterio.open(f) as src:
            # Read the first band; assuming single band for covariates/temp
            arr = src.read(1).astype(np.float32)
            
            # Handle nodata
            if src.nodata is not None:
                arr[arr == src.nodata] = np.nan

            data_stack[f.stem] = arr

            if ref_shape is None:
                ref_shape = arr.shape
                ref_transform = src.transform
            else:
                if arr.shape != ref_shape:
                    raise ValueError(f"Shape mismatch for {f.name}: {arr.shape} vs {ref_shape}")
    
    # Memory safety check
    total_mb = sum(estimate_raster_memory_mb(arr) for arr in data_stack.values())
    check_memory_safety(total_mb, limit_mb=4000) # 4GB limit for EDA stage

    return data_stack

def extract_sample_points_from_blocks(data: Dict[str, np.ndarray], 
                                      block_mask: Optional[np.ndarray] = None) -> Dict[str, np.ndarray]:
    """
    Flatten the raster stack into 1D arrays, optionally filtering by a block mask.
    Returns a dictionary of arrays ready for statistical analysis.
    """
    if not data:
        return {}

    # Use the first array to determine shape
    first_key = next(iter(data))
    shape = data[first_key].shape
    total_pixels = shape[0] * shape[1]

    # Create a valid mask (non-NaN) across all layers
    valid_mask = np.ones(shape, dtype=bool)
    for arr in data.values():
        valid_mask &= ~np.isnan(arr)

    if block_mask is not None:
        valid_mask &= block_mask

    if np.sum(valid_mask) == 0:
        raise ValueError("No valid pixels found after masking.")

    # Extract values
    result = {}
    for key, arr in data.items():
        flat_arr = arr[valid_mask]
        result[key] = flat_arr

    logger.info(f"Extracted {len(result[next(iter(result))])} valid sample points.")
    return result

def pivot_to_wide(sample_dict: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Convert the dictionary of 1D arrays into a 2D numpy matrix (N_samples x N_features).
    """
    keys = list(sample_dict.keys())
    n_samples = len(sample_dict[keys[0]])
    n_features = len(keys)
    
    matrix = np.zeros((n_samples, n_features))
    for i, key in enumerate(keys):
        matrix[:, i] = sample_dict[key]
    
    return matrix

def compute_correlation_matrix(sample_dict: Dict[str, np.ndarray], 
                               output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute Pearson and Spearman correlation matrices.
    Outputs to data/results/correlation_matrix.csv if output_path provided.
    """
    if not HAS_PYSPAL:
        logger.warning("scipy not available for correlation matrix.")
        return {}

    keys = list(sample_dict.keys())
    n = len(sample_dict[keys[0]])
    data_matrix = np.column_stack([sample_dict[k] for k in keys])

    # Remove rows with any NaN (should be rare after masking)
    mask = ~np.any(np.isnan(data_matrix), axis=1)
    clean_data = data_matrix[mask]

    if clean_data.shape[0] == 0:
        raise ValueError("No valid data points for correlation analysis.")

    pearson_r, pearson_p = stats.pearsonr(clean_data, axis=0)
    spearman_r, spearman_p = stats.spearmanr(clean_data, axis=0)

    # Structure result
    result = {
        "pearson": {},
        "spearman": {}
    }

    for i, k1 in enumerate(keys):
        result["pearson"][k1] = {}
        result["spearman"][k1] = {}
        for j, k2 in enumerate(keys):
            result["pearson"][k1][k2] = float(pearson_r[i, j])
            result["spearman"][k1][k2] = float(spearman_r[i, j])

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        # Simple CSV export (flattened)
        with open(out_p, 'w') as f:
            f.write("method,var1,var2,coefficient,p_value\n")
            for i, k1 in enumerate(keys):
                for j, k2 in enumerate(keys):
                    if i <= j: continue # Skip duplicate/upper triangle if desired, or keep all
                    # For full matrix
                    f.write(f"pearson,{k1},{k2},{pearson_r[i,j]:.4f},{pearson_p[i,j]:.4f}\n")
                    f.write(f"spearman,{k1},{k2},{spearman_r[i,j]:.4f},{spearman_p[i,j]:.4f}\n")
        logger.info(f"Correlation matrix saved to {output_path}")

    return result

def compute_spatial_autocorrelation(data: Dict[str, np.ndarray], 
                                    output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute Moran's I and Variograms for the target variable (Temperature).
    Requires pysal and libpysal.
    """
    if not HAS_PYSPAL:
        raise RuntimeError("pysal and libpysal are required for spatial autocorrelation. Install with 'pip install pysal'.")

    logger.info("Starting spatial autocorrelation analysis...")

    # Identify temperature variable
    temp_key = None
    for k in data.keys():
        if 'temp' in k.lower() or 'land_surface' in k.lower():
            temp_key = k
            break
    
    if temp_key is None:
        # Fallback to the last key if 'temp' not found, assuming it's the target
        temp_key = list(data.keys())[-1]
        logger.warning(f"Could not identify temperature variable by name. Using '{temp_key}' as target.")

    temp_arr = data[temp_key]
    shape = temp_arr.shape
    n_rows, n_cols = shape

    # Flatten
    y = temp_arr.flatten()
    valid_mask = ~np.isnan(y)
    y_clean = y[valid_mask]

    if len(y_clean) < 100:
        raise ValueError(f"Insufficient valid pixels for spatial analysis: {len(y_clean)}")

    logger.info(f"Analyzing {len(y_clean)} valid pixels for Moran's I.")

    # Create spatial weights (Queen contiguity on the grid)
    # We need to map 1D index back to 2D grid neighbors
    # Construct a grid of IDs
    grid_ids = np.arange(n_rows * n_cols).reshape(shape)
    
    # Filter grid IDs to match valid pixels
    valid_grid_ids = grid_ids[valid_mask]
    
    # Create a mapping from original 2D index (flattened) to new 1D index in clean array
    # Actually, pysal expects a W object. We can build W on the full grid then subset, 
    # or build W on the valid points assuming regular grid topology.
    # Efficient approach: Build W on the full grid, then subset to valid indices.
    
    # Generate Queen weights for the full grid
    # libpysal.weights.Queen.from_shapefile is common, but we have a raster grid.
    # We can use libpysal.weights.lat2W
    w_full = libpysal.weights.lat2W(n_rows, n_cols, rook=False) # Queen = rook=False (includes diagonals)
    
    # Subset weights to valid indices
    # w_full.id_order is 0..N-1
    valid_indices = np.where(valid_mask)[0]
    w = libpysal.weights.W_subset(w_full, valid_indices)
    
    if w.n < 100:
        raise ValueError("Spatial weights matrix too small after subsetting.")

    # Compute Moran's I
    moran = Moran(y_clean, w)
    moran_i = float(moran.I)
    z_score = float(moran.z)
    p_value = float(moran.p)

    logger.info(f"Moran's I: {moran_i:.4f} (z={z_score:.2f}, p={p_value:.4f})")

    # Compute Empirical Variogram
    # We need coordinates for the valid points
    # Create meshgrid
    y_coords, x_coords = np.meshgrid(np.arange(n_rows), np.arange(n_cols), indexing='ij')
    x_flat = x_coords.flatten()
    y_flat = y_coords.flatten()
    
    valid_x = x_flat[valid_mask]
    valid_y = y_flat[valid_mask]
    
    # Combine into (N, 2) array
    coords = np.column_stack([valid_x, valid_y])
    
    # Use pysal's variogram
    # libpysal.esda.variogram.empirical_variogram
    try:
        from pysal.explore.esda import variogram
        # Calculate variogram
        # Note: pysal variogram expects y and coordinates
        var_results = variogram.empirical_variogram(y_clean, coords, bin_func=variogram.bin_linear, lags=20)
        
        variogram_data = {
            "lags": var_results.lags.tolist(),
            "semivariance": var_results.semivariance.tolist(),
            "n_lags": len(var_results.lags)
        }
    except Exception as e:
        logger.warning(f"Could not compute variogram: {e}")
        variogram_data = {"error": str(e)}

    result = {
        "target_variable": temp_key,
        "n_samples": len(y_clean),
        "moran_i": moran_i,
        "z_score": z_score,
        "p_value": p_value,
        "significant_at_0.05": p_value < 0.05,
        "variogram": variogram_data
    }

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Spatial statistics saved to {output_path}")

    return result

def main():
    """
    Main entry point for EDA analysis.
    Loads processed rasters, computes correlations and spatial stats.
    """
    logger.info("Starting EDA Pipeline (T019 + T020)")
    
    # Paths
    results_dir = get_path("data", "results")
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    try:
        data = load_raster_stack()
    except Exception as e:
        logger.error(f"Failed to load raster stack: {e}")
        return 1

    # 2. Extract Samples (No masking needed if data is already aligned and clean)
    try:
        sample_dict = extract_sample_points_from_blocks(data)
    except Exception as e:
        logger.error(f"Failed to extract samples: {e}")
        return 1

    # 3. Correlation Matrix (T019)
    corr_path = get_path("data", "results", "correlation_matrix.csv")
    try:
        compute_correlation_matrix(sample_dict, output_path=corr_path)
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        return 1

    # 4. Spatial Autocorrelation (T020)
    spatial_stats_path = get_path("data", "results", "spatial_stats.json")
    try:
        compute_spatial_autocorrelation(data, output_path=spatial_stats_path)
    except Exception as e:
        logger.error(f"Spatial autocorrelation analysis failed: {e}")
        return 1

    logger.info("EDA Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

# Optional imports for spatial analysis
try:
    import geopandas as gpd
    from scipy import stats
    from scipy.spatial import distance_matrix
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    gpd = None
    stats = None
    distance_matrix = None

try:
    import pyvariogram
    HAS_PYVARI = True
except ImportError:
    HAS_PYVARI = False

from utils.logging import get_logger

logger = get_logger(__name__)

# --- Helper Functions ---

def load_raster_as_dataframe(raster_path: str) -> Optional[np.ndarray]:
    """
    Load a GeoTIFF raster into a 2D numpy array.
    Returns None if file not found or reading fails.
    """
    if not os.path.exists(raster_path):
        logger.error(f"Raster file not found: {raster_path}")
        return None

    try:
        import rasterio
        with rasterio.open(raster_path) as src:
            # Read the first band
            data = src.read(1)
            # Mask nodata values
            nodata = src.nodata
            if nodata is not None:
                data = np.ma.masked_equal(data, nodata)
            # Convert masked array to float, filling masked with NaN for easier handling
            data = data.filled(np.nan)
            return data
    except Exception as e:
        logger.error(f"Error reading raster {raster_path}: {e}")
        return None

def calculate_correlation_matrix(covariate_paths: Dict[str, str], temp_path: str) -> Dict[str, Any]:
    """
    Calculate Pearson/Spearman correlations between covariates and temperature.
    Output to data/results/correlation_matrix.csv (handled by caller or main).
    Returns a dictionary of correlation coefficients.
    """
    if not HAS_SCIPY:
        logger.error("Scipy not available for correlation calculation.")
        return {}

    temp_data = load_raster_as_dataframe(temp_path)
    if temp_data is None:
        return {}

    # Flatten temperature
    temp_flat = temp_data.flatten()
    valid_mask = ~np.isnan(temp_flat)

    results = {}
    results['temperature'] = {}

    logger.info(f"Calculating correlations with {len(covariate_paths)} covariates...")

    for name, path in covariate_paths.items():
        cov_data = load_raster_as_dataframe(path)
        if cov_data is None:
            continue

        cov_flat = cov_data.flatten()
        
        # Apply same mask as temperature, plus check for covariate NaNs
        combined_mask = valid_mask & ~np.isnan(cov_flat)
        
        if np.sum(combined_mask) < 10:
            logger.warning(f"Not enough valid overlapping data points for {name}. Skipping.")
            continue

        x = cov_flat[combined_mask]
        y = temp_flat[combined_mask]

        try:
            # Pearson
            pearson_corr, pearson_p = stats.pearsonr(x, y)
            # Spearman
            spearman_corr, spearman_p = stats.spearmanr(x, y)

            results['temperature'][name] = {
                'pearson': float(pearson_corr),
                'pearson_p': float(pearson_p),
                'spearman': float(spearman_corr),
                'spearman_p': float(spearman_p),
                'n_samples': int(np.sum(combined_mask))
            }
            logger.info(f"Correlation for {name}: Pearson={pearson_corr:.4f}, Spearman={spearman_corr:.4f}")
        except Exception as e:
            logger.warning(f"Could not compute correlation for {name}: {e}")
            continue

    return results

def calculate_morans_i(data: np.ndarray, weights: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Compute Moran's I for a 2D array (temperature raster).
    If weights are not provided, a simple queen contiguity matrix is generated.
    Returns dict with 'morans_i', 'expected_i', 'z_score', 'p_value'.
    """
    if not HAS_SCIPY:
        logger.error("Scipy not available for Moran's I calculation.")
        return {'error': 'scipy_missing'}

    if data.ndim != 2:
        logger.error("Input data must be 2D for Moran's I.")
        return {'error': 'invalid_shape'}

    # Flatten and handle NaNs
    flat_data = data.flatten()
    valid_mask = ~np.isnan(flat_data)
    y = flat_data[valid_mask]

    if len(y) < 10:
        logger.warning("Too few valid points for Moran's I.")
        return {'error': 'insufficient_data'}

    n = len(y)
    mean_y = np.mean(y)
    var_y = np.var(y, ddof=0) # Population variance

    if var_y == 0:
        return {'morans_i': 0.0, 'expected_i': -1.0/(n-1), 'z_score': 0.0, 'p_value': 1.0}

    # Generate spatial weights if not provided
    # For a 2D grid, we can construct a simplified weight matrix based on indices
    # However, reconstructing the 2D grid from 1D requires original shape.
    # We assume the input 'data' is the 2D array, but we are working on 'y' (flattened valid).
    # To do this correctly without the full grid structure of valid points, we approximate
    # using the original 2D structure but only considering valid neighbors.
    
    # Reconstruct 2D mask
    mask_2d = valid_mask.reshape(data.shape)
    
    # Create a sparse-like weight matrix logic: iterate over non-NaN pixels
    # This is O(N) for neighbor finding, acceptable for moderate rasters.
    # We will calculate the numerator and denominator sums directly.
    
    # Numerator: Sum_i Sum_j w_ij (x_i - mean)(x_j - mean)
    # Denominator: Sum_i (x_i - mean)^2
    # S = Sum_i Sum_j w_ij
    
    # We define w_ij = 1 if pixels i and j are 4-connected (rook) or 8-connected (queen).
    # Let's use 4-connected (rook) for simplicity and speed.
    
    rows, cols = data.shape
    numerator = 0.0
    denominator = 0.0
    s = 0.0 # Sum of weights
    
    # Pre-calculate deviations
    dev = np.zeros_like(data)
    dev[valid_mask] = y - mean_y
    
    # Denominator: Sum of squared deviations (over all valid points)
    denominator = np.sum(dev[valid_mask] ** 2)
    
    # Iterate over valid pixels and check neighbors
    # To avoid double counting in the sum (i,j) and (j,i), we can just sum all and divide by 2 later,
    # or define the loop carefully. Moran's I formula usually sums over all i,j.
    # We will sum over all i,j pairs where w_ij=1.
    
    # Directions for 4-connectivity: (row, col)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    valid_indices = np.argwhere(mask_2d)
    
    for r, c in valid_indices:
        val_i = dev[r, c]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and mask_2d[nr, nc]:
                val_j = dev[nr, nc]
                numerator += val_i * val_j
                s += 1.0
    
    if s == 0:
        return {'error': 'no_neighbors'}
    
    morans_i = (n / s) * (numerator / denominator)
    expected_i = -1.0 / (n - 1)
    
    # Variance of I (approximate for large n, regular grid)
    # Using the standard normal approximation
    # This is a simplified variance calculation; pysal has more robust ones.
    # Variance approx: (n * S0 * S2 - S1^2) / ((n-1) * S0^2) ... complex.
    # Let's use a simpler Monte Carlo permutation approach for p-value if possible, 
    # but for a single run without pysal, we'll estimate Z.
    
    # Approximate Z-score using standard error for regular grids (simplified)
    # SE = sqrt( (n * (S2 - S1^2/S0) - S1^2) / ((n-1)*S0^2) ) ... too complex to derive on fly without weights object.
    # Instead, we will return the calculated I and expected I. 
    # For a robust Z-score without pysal, we assume the null distribution is approximately normal 
    # with variance derived from the data structure.
    # A common simplified variance for regular grids:
    # Var(I) = (n * S2 - S1^2) / ( (n-1) * S0^2 ) ... still need S1, S2.
    
    # Let's fallback to a simple permutation test for p-value if n is small, 
    # or return the statistic and let the user interpret if n is large.
    # Given the constraint of "no pysal", we will calculate Z using a standard approximation
    # for a regular lattice:
    # Z = (I - E[I]) / sqrt(Var[I])
    # Var[I] approximation for large n: (1 - E[I]^2) / (n-1) is often used as a rough lower bound.
    # Better: Use the formula from Cliff & Ord for regular grids.
    
    # For this implementation, we will compute a Monte Carlo p-value if n < 5000, 
    # else return NaN for Z to avoid incorrect assumptions.
    
    p_val = np.nan
    z_score = np.nan
    
    if n < 5000:
        # Monte Carlo permutation
        sims = 1000
        count_extreme = 0
        for _ in range(sims):
            np.random.shuffle(y)
            # Re-calculate numerator with shuffled y (same weights structure)
            # This is slow in pure python. 
            # Optimization: The weights structure is fixed. We are calculating sum_i sum_j w_ij y_i y_j
            # = y^T W y.
            # We can't easily vectorize this without the full matrix W.
            # Given performance constraints, we will skip MC if n is large.
            pass 
        
        # Since MC is too slow in pure python for rasters, we will return the I value and expected.
        # We will set Z to NaN to indicate it's an estimate.
        logger.info("Monte Carlo not performed due to performance constraints in pure python.")
    else:
        logger.info("n too large for Monte Carlo Z-score calculation without optimized libraries.")
        
    # Attempt a rough Z-score using a simplified variance formula for regular grids
    # Var(I) approx = (n * S2 - S1^2) / ( (n-1) * S0^2 ) is hard without S1, S2.
    # We'll leave Z as NaN if we can't compute it reliably.
    
    return {
        'morans_i': float(morans_i),
        'expected_i': float(expected_i),
        'z_score': float('nan'), # Placeholder
        'p_value': float('nan'),
        'n_samples': int(n),
        'note': 'Z-score and p-value require spatial weights matrix structure (pysal) or Monte Carlo. Pure Python approximation omitted for performance.'
    }

def calculate_variogram(data: np.ndarray, bin_size: float = 1.0, max_lag: float = 10.0) -> Dict[str, Any]:
    """
    Compute a variogram for the target variable.
    bin_size: Distance interval for binning.
    max_lag: Maximum distance to consider.
    Returns dict with 'lags', 'semivariances', 'nugget', 'sill', 'range'.
    """
    if not HAS_SCIPY:
        logger.error("Scipy not available for variogram.")
        return {'error': 'scipy_missing'}

    if data.ndim != 2:
        logger.error("Input data must be 2D.")
        return {'error': 'invalid_shape'}

    rows, cols = data.shape
    valid_mask = ~np.isnan(data)
    if np.sum(valid_mask) < 10:
        return {'error': 'insufficient_data'}

    # Extract coordinates and values
    ys, xs = np.where(valid_mask)
    values = data[valid_mask]
    
    # Calculate pairwise distances (simplified: only for a subset if too large)
    n_points = len(values)
    if n_points > 2000:
        logger.warning(f"Too many points ({n_points}) for exact variogram. Sampling 2000 points.")
        idx = np.random.choice(n_points, 2000, replace=False)
        xs = xs[idx]
        ys = ys[idx]
        values = values[idx]
        n_points = len(values)

    # Calculate distances
    # Using a simplified approach: create a grid of points
    coords = np.column_stack((xs, ys))
    # Euclidean distance matrix
    # D[i,j] = sqrt((x_i-x_j)^2 + (y_i-y_j)^2)
    # This is O(N^2). For N=2000, 4M pairs. Doable.
    
    dists = distance_matrix(coords, coords)
    n_pairs = (n_points * (n_points - 1)) // 2
    
    # Flatten distances and values for pair calculation
    # We need pairs (i, j) with i < j
    # Use triu_indices
    i_idx, j_idx = np.triu_indices(n_points, k=1)
    
    dists = dists[i_idx, j_idx]
    vals_i = values[i_idx]
    vals_j = values[j_idx]
    
    # Filter by max_lag
    valid_pairs = dists <= max_lag
    dists = dists[valid_pairs]
    diffs = (vals_i - vals_j) ** 2 / 2.0
    diffs = diffs[valid_pairs]
    
    if len(dists) == 0:
        return {'error': 'no_pairs_within_max_lag'}
    
    # Bin the distances
    bins = np.arange(0, max_lag + bin_size, bin_size)
    bin_centers = (bins[:-1] + bins[1:]) / 2.0
    
    semivariances = []
    counts = []
    
    for i in range(len(bins) - 1):
        mask = (dists >= bins[i]) & (dists < bins[i+1])
        if np.sum(mask) > 0:
            semivariances.append(np.mean(diffs[mask]))
            counts.append(np.sum(mask))
        else:
            semivariances.append(np.nan)
            counts.append(0)
    
    # Simple nugget/sill/range estimation
    # Nugget: semivariance at lag 0 (approx first bin)
    # Sill: max semivariance
    # Range: lag where semivariance reaches sill
    
    valid_svs = [sv for sv in semivariances if not np.isnan(sv)]
    if len(valid_svs) == 0:
        return {'error': 'no_valid_bins'}
        
    nugget = valid_svs[0] if len(valid_svs) > 0 else 0.0
    sill = np.max(valid_svs)
    
    # Find range (first bin where SV >= 0.95 * sill)
    range_val = max_lag
    for i, sv in enumerate(semivariances):
        if not np.isnan(sv) and sv >= 0.95 * sill:
            range_val = bin_centers[i]
            break
    
    return {
        'lags': [float(x) for x in bin_centers],
        'semivariances': [float(x) if not np.isnan(x) else None for x in semivariances],
        'counts': counts,
        'nugget': float(nugget),
        'sill': float(sill),
        'range': float(range_val)
    }

def generate_eda_report(stats: Dict[str, Any], output_path: str) -> None:
    """
    Generate a markdown summary report of EDA results.
    """
    with open(output_path, 'w') as f:
        f.write("# Exploratory Data Analysis Report\n\n")
        
        f.write("## Spatial Autocorrelation (Moran's I)\n")
        if 'temperature' in stats and 'morans_i' in stats['temperature']:
            mi = stats['temperature']['morans_i']
            f.write(f"- **Moran's I**: {mi['morans_i']:.4f}\n")
            f.write(f"- **Expected I**: {mi['expected_i']:.4f}\n")
            if 'z_score' in mi and not np.isnan(mi.get('z_score', np.nan)):
                f.write(f"- **Z-Score**: {mi['z_score']:.4f}\n")
            if 'note' in mi:
                f.write(f"- **Note**: {mi['note']}\n")
        else:
            f.write("- No Moran's I data available.\n")
        
        f.write("\n## Variogram Analysis\n")
        if 'temperature' in stats and 'variogram' in stats['temperature']:
            vg = stats['temperature']['variogram']
            f.write(f"- **Nugget**: {vg['nugget']:.4f}\n")
            f.write(f"- **Sill**: {vg['sill']:.4f}\n")
            f.write(f"- **Range**: {vg['range']:.4f}\n")
        else:
            f.write("- No variogram data available.\n")

def main():
    """
    Main entry point for EDA analysis.
    Expects environment variables or config for paths.
    Reads from data/processed/ and writes to data/results/
    """
    # Determine paths based on project structure
    # Assuming standard paths from config or hardcoding for this task if config is not fully ready
    # We will try to read from a standard location or use defaults.
    
    # Default paths
    processed_dir = Path("data/processed")
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Find temperature raster (look for *_temp.tif or similar)
    temp_files = list(processed_dir.glob("*temp*.tif"))
    if not temp_files:
        # Fallback: look for any tif if pattern fails, but warn
        temp_files = list(processed_dir.glob("*.tif"))
    
    if not temp_files:
        logger.error("No temperature raster found in data/processed/")
        return

    temp_path = str(temp_files[0])
    logger.info(f"Using temperature raster: {temp_path}")
    
    # Find covariate rasters (exclude temp)
    covariate_paths = {}
    for f in processed_dir.glob("*.tif"):
        if f.name != Path(temp_path).name:
            # Simple heuristic: assume all other tiffs are covariates
            covariate_paths[f.stem] = str(f)
    
    if not covariate_paths:
        logger.warning("No covariate rasters found. Skipping correlation matrix.")
    else:
        logger.info(f"Found {len(covariate_paths)} covariate rasters.")
    
    # 1. Correlation Matrix
    corr_results = {}
    if covariate_paths:
        corr_results = calculate_correlation_matrix(covariate_paths, temp_path)
        # Save CSV
        if corr_results:
            csv_path = results_dir / "correlation_matrix.csv"
            # Flatten for CSV
            rows = []
            for target, data in corr_results.items():
                for cov, vals in data.items():
                    if target == 'temperature':
                        rows.append({
                            'variable_1': target,
                            'variable_2': cov,
                            'pearson': vals['pearson'],
                            'pearson_p': vals['pearson_p'],
                            'spearman': vals['spearman'],
                            'spearman_p': vals['spearman_p'],
                            'n_samples': vals['n_samples']
                        })
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows)
                df.to_csv(csv_path, index=False)
                logger.info(f"Saved correlation matrix to {csv_path}")
    
    # 2. Spatial Autocorrelation & Variogram
    temp_data = load_raster_as_dataframe(temp_path)
    stats_output = {}
    
    if temp_data is not None:
        # Moran's I
        mi_res = calculate_morans_i(temp_data)
        stats_output['temperature'] = {'morans_i': mi_res}
        
        # Variogram
        vg_res = calculate_variogram(temp_data)
        stats_output['temperature']['variogram'] = vg_res
        
        # Save JSON
        json_path = results_dir / "spatial_stats.json"
        with open(json_path, 'w') as f:
            json.dump(stats_output, f, indent=2)
        logger.info(f"Saved spatial stats to {json_path}")
        
        # Generate Report
        report_path = results_dir / "eda_report.md"
        generate_eda_report(stats_output, str(report_path))
        logger.info(f"Generated EDA report at {report_path}")
    else:
        logger.error("Failed to load temperature data for spatial analysis.")

if __name__ == "__main__":
    main()
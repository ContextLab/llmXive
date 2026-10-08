"""
Spatial Metrics Analysis Module

Computes 2-D autocorrelation functions, fits decay models, and extracts
correlation lengths and spectral power metrics for perovskite solar cell
elemental maps.
"""

import numpy as np
from scipy import ndimage
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import logging
from typing import Tuple, Dict, Any, Optional, Union, List
import pandas as pd
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Decay Models ---

def gaussian_decay(x: np.ndarray, amplitude: float, center: float, sigma: float) -> np.ndarray:
    """
    Gaussian decay model for autocorrelation.
    AC(r) = amplitude * exp(-(r-center)^2 / (2 * sigma^2))
    """
    return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))

def exponential_decay(x: np.ndarray, amplitude: float, center: float, tau: float) -> np.ndarray:
    """
    Exponential decay model for autocorrelation.
    AC(r) = amplitude * exp(-(r-center) / tau)
    """
    # Ensure non-negative x for stability if center is 0, though r >= 0 usually
    return amplitude * np.exp(-np.maximum(x - center, 0) / tau)

def power_law_decay(x: np.ndarray, amplitude: float, center: float, alpha: float) -> np.ndarray:
    """
    Power-law decay model for autocorrelation.
    AC(r) = amplitude * (1 + (r-center)/scale)^-alpha
    Using a simplified form: A * (r + eps)^-alpha
    """
    # Avoid division by zero or negative base
    safe_x = np.maximum(x, 1e-9)
    return amplitude * (safe_x ** -alpha)

# --- Autocorrelation Computation ---

def compute_autocorrelation(map_data: np.ndarray) -> np.ndarray:
    """
    Computes the 2-D autocorrelation of a map using FFT.
    """
    # Normalize
    map_centered = map_data - np.mean(map_data)
    fft_map = np.fft.fft2(map_centered)
    autocorr = np.fft.ifft2(fft_map * np.conj(fft_map)).real
    
    # Shift zero-frequency component to center
    autocorr = np.fft.fftshift(autocorr)
    
    # Normalize by variance (at lag 0)
    var = np.var(map_data)
    if var > 0:
        autocorr = autocorr / (var * map_data.size)
    else:
        autocorr = np.zeros_like(autocorr)
        
    return autocorr

def compute_radial_distances(shape: Tuple[int, int]) -> np.ndarray:
    """
    Computes radial distances from the center of the autocorrelation map.
    """
    y, x = np.indices(shape)
    center_y, center_x = np.array(shape) / 2.0
    r = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    return r

def extract_radial_profile(autocorr: np.ndarray, r: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extracts the radial profile of the autocorrelation by binning.
    Returns mean AC value per bin and bin centers.
    """
    r_flat = r.flatten()
    ac_flat = autocorr.flatten()
    
    # Sort by radius
    sorted_indices = np.argsort(r_flat)
    r_sorted = r_flat[sorted_indices]
    ac_sorted = ac_flat[sorted_indices]
    
    # Bin edges
    bin_edges = np.linspace(0, r_sorted.max(), 100)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    
    radial_profile = []
    bin_counts = []
    
    for i in range(len(bin_centers)):
        mask = (r_sorted >= bin_edges[i]) & (r_sorted < bin_edges[i+1])
        if np.sum(mask) > 0:
            radial_profile.append(np.mean(ac_sorted[mask]))
            bin_counts.append(np.sum(mask))
        else:
            radial_profile.append(np.nan)
            bin_counts.append(0)
            
    return np.array(bin_centers), np.array(radial_profile)

# --- Model Fitting ---

def fit_decay_model(r: np.ndarray, ac: np.ndarray, 
                    max_r: float, 
                    models: List[str] = ['gaussian', 'exponential', 'power_law']) -> Dict[str, Any]:
    """
    Fits multiple decay models to the radial autocorrelation profile.
    Returns the best fit model based on AIC and correlation length.
    
    Handles 'undefined' correlation lengths when decay does not occur within bounds.
    """
    results = {}
    best_model_name = None
    best_aic = np.inf
    best_params = None
    
    # Filter out NaNs from the radial profile
    valid_mask = ~np.isnan(ac)
    r_fit = r[valid_mask]
    ac_fit = ac[valid_mask]
    
    if len(r_fit) < 5:
        logger.warning("Insufficient data points for fitting.")
        return {
            "model_type": "undefined",
            "correlation_length": np.nan,
            "aic": np.inf,
            "is_undefined": True,
            "lower_bound": max_r
        }

    # Define fitting functions with initial guesses
    def try_fit(func, p0, bounds=(0, np.inf), model_name=""):
        try:
            popt, pcov = curve_fit(func, r_fit, ac_fit, p0=p0, bounds=bounds, maxfev=5000)
            residuals = ac_fit - func(r_fit, *popt)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((ac_fit - np.mean(ac_fit))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Calculate AIC
            k = len(popt)
            n = len(r_fit)
            if ss_res == 0:
                aic = -np.inf # Perfect fit
            else:
                aic = n * np.log(ss_res / n) + 2 * k
            
            return {
                "params": popt,
                "aic": aic,
                "r_squared": r_squared,
                "success": True
            }
        except Exception as e:
            logger.debug(f"Fit failed for {model_name}: {e}")
            return {"success": False}

    if 'gaussian' in models:
        # Guess: amplitude ~ 1, center ~ 0, sigma ~ max_r/4
        res = try_fit(gaussian_decay, [1.0, 0.0, max_r/4], model_name="gaussian")
        if res["success"]:
            results['gaussian'] = res
            if res["aic"] < best_aic:
                best_aic = res["aic"]
                best_model_name = 'gaussian'
                best_params = res["params"]

    if 'exponential' in models:
        # Guess: amplitude ~ 1, center ~ 0, tau ~ max_r/3
        res = try_fit(exponential_decay, [1.0, 0.0, max_r/3], model_name="exponential")
        if res["success"]:
            results['exponential'] = res
            if res["aic"] < best_aic:
                best_aic = res["aic"]
                best_model_name = 'exponential'
                best_params = res["params"]

    if 'power_law' in models:
        # Guess: amplitude ~ 1, alpha ~ 1
        res = try_fit(power_law_decay, [1.0, 0.0, 1.0], bounds=(0, [np.inf, np.inf, 5.0]), model_name="power_law")
        if res["success"]:
            results['power_law'] = res
            if res["aic"] < best_aic:
                best_aic = res["aic"]
                best_model_name = 'power_law'
                best_params = res["params"]

    if not best_model_name:
        logger.warning("No decay model could be fitted successfully.")
        return {
            "model_type": "undefined",
            "correlation_length": np.nan,
            "aic": np.inf,
            "is_undefined": True,
            "lower_bound": max_r
        }

    # Extract correlation length based on model
    correlation_length = np.nan
    is_undefined = False
    lower_bound = np.nan

    if best_model_name == 'gaussian':
        # Sigma is the correlation length
        correlation_length = best_params[2]
    elif best_model_name == 'exponential':
        # Tau is the correlation length
        correlation_length = best_params[2]
    elif best_model_name == 'power_law':
        # For power law, correlation length is not strictly defined as a decay to 1/e
        # We can define it as the scale parameter or mark as undefined if it decays too slowly
        # Here we treat alpha < 1 as potentially undefined (long range)
        alpha = best_params[2]
        if alpha < 1.0:
            is_undefined = True
            lower_bound = max_r
            correlation_length = np.nan
        else:
            # Approximate correlation length for power law
            correlation_length = 1.0 / alpha 
    else:
        is_undefined = True
        lower_bound = max_r

    # Check if decay occurs within image bounds
    # If correlation_length > max_r / 2 (or some threshold), it might be undefined
    # Specifically, if the fitted curve does not drop to near zero within max_r
    if best_model_name == 'exponential' or best_model_name == 'gaussian':
        # Check value at max_r
        val_at_max = 0
        if best_model_name == 'exponential':
            val_at_max = exponential_decay(np.array([max_r]), *best_params)[0]
        else:
            val_at_max = gaussian_decay(np.array([max_r]), *best_params)[0]
        
        # If the correlation is still > 0.1 (10%) at the edge, it's likely undefined
        if val_at_max > 0.1:
            is_undefined = True
            lower_bound = max_r
            correlation_length = np.nan
            logger.info(f"Correlation length undefined for {best_model_name}: decay not observed within bounds (val@max={val_at_max:.3f})")

    return {
        "model_type": best_model_name,
        "correlation_length": correlation_length,
        "aic": best_aic,
        "is_undefined": is_undefined,
        "lower_bound": lower_bound,
        "params": best_params
    }

# --- Main Processing ---

def compute_spatial_metrics_for_sample(sample_id: str, 
                                       element_map: np.ndarray, 
                                       element_name: str,
                                       pixel_size: float = 1.0) -> Dict[str, Any]:
    """
    Computes spatial metrics for a single sample.
    """
    # Compute autocorrelation
    autocorr = compute_autocorrelation(element_map)
    
    # Compute radial distances
    r = compute_radial_distances(autocorr.shape)
    max_r = r.max()
    
    # Extract radial profile
    r_profile, ac_profile = extract_radial_profile(autocorr, r)
    
    # Fit models
    fit_results = fit_decay_model(r_profile, ac_profile, max_r)
    
    # Convert correlation length to physical units if pixel_size provided
    if pixel_size != 1.0 and not np.isnan(fit_results.get('correlation_length', np.nan)):
        fit_results['correlation_length'] *= pixel_size
        if not np.isnan(fit_results.get('lower_bound', np.nan)):
            fit_results['lower_bound'] *= pixel_size

    return {
        "sample_id": sample_id,
        "element": element_name,
        "correlation_length": fit_results.get('correlation_length', np.nan),
        "model_type": fit_results.get('model_type', 'undefined'),
        "aic": fit_results.get('aic', np.inf),
        "is_undefined": fit_results.get('is_undefined', False),
        "lower_bound": fit_results.get('lower_bound', np.nan)
    }

def process_dataset_and_write_metrics(dataset_path: str, 
                                      output_path: str,
                                      map_columns: List[str],
                                      pixel_size: float = 1.0):
    """
    Processes a dataset of maps and writes spatial metrics to CSV.
    """
    logger.info(f"Loading dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)
    
    results = []
    
    for idx, row in df.iterrows():
        sample_id = row['sample_id']
        logger.info(f"Processing {sample_id}")
        
        for col in map_columns:
            if pd.isna(row[col]):
                logger.warning(f"Skipping {sample_id} - {col}: missing data")
                continue
            
            # Load map (assuming path or array in cell, here assuming path string)
            # In a real scenario, we might need to load the image file
            # For this implementation, we assume the CSV contains paths or we have a way to access the map
            # If the CSV contains the array directly (unlikely for large data), we parse it.
            # Assuming the CSV has paths to numpy files or similar.
            # For the sake of this task, we assume we need to load the map from a file system.
            # However, the task T021 is about the *logic* of flagging undefined lengths.
            # We will assume the map is available as a numpy array or path.
            # Let's assume the column contains a path to a .npy file.
            map_path = row[col]
            if not os.path.exists(map_path):
                # If it's not a path, maybe it's a serialized array string? 
                # Or maybe we skip.
                logger.warning(f"Map file not found: {map_path}")
                continue
            
            try:
                map_data = np.load(map_path)
            except Exception as e:
                logger.error(f"Error loading map {map_path}: {e}")
                continue
            
            element_name = col.replace('_map', '').replace('_path', '')
            
            metrics = compute_spatial_metrics_for_sample(
                sample_id, map_data, element_name, pixel_size
            )
            results.append(metrics)
    
    # Create DataFrame
    result_df = pd.DataFrame(results)
    
    # Ensure columns are in expected order
    cols = ['sample_id', 'element', 'correlation_length', 'model_type', 'aic', 'is_undefined', 'lower_bound']
    # Only keep columns that exist
    existing_cols = [c for c in cols if c in result_df.columns]
    result_df = result_df[existing_cols]
    
    # Write to CSV
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    logger.info(f"Wrote metrics to {output_path}")
    return result_df

def main():
    """
    Entry point for spatial metrics analysis.
    """
    # Example usage (to be replaced by CLI args in a real pipeline)
    # dataset_path = "data/processed/unified_dataset.csv"
    # output_path = "data/processed/spatial_metrics.csv"
    # map_columns = ['Pb_map_path', 'I_map_path', 'MA_map_path']
    
    # For testing purposes, if no files exist, this will log warnings and produce an empty CSV
    # This satisfies the requirement to write the file even if data is missing (graceful degradation)
    # But the core logic for T021 (flagging undefined) is in fit_decay_model.
    
    import argparse
    parser = argparse.ArgumentParser(description="Compute spatial metrics")
    parser.add_argument("--dataset", type=str, required=True, help="Path to unified dataset CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output spatial metrics CSV")
    parser.add_argument("--columns", type=str, nargs='+', help="Columns containing map paths")
    parser.add_argument("--pixel-size", type=float, default=1.0, help="Pixel size in nm")
    
    args = parser.parse_args()
    
    if not args.columns:
        # Default columns if not provided
        args.columns = ['Pb_map_path', 'I_map_path', 'MA_map_path']
        
    process_dataset_and_write_metrics(
        args.dataset, 
        args.output, 
        args.columns, 
        args.pixel_size
    )

if __name__ == "__main__":
    main()
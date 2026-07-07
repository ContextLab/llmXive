import numpy as np
from scipy import ndimage
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import logging
from typing import Tuple, Dict, Any, Optional, Union, List
import os
import pandas as pd
from pathlib import Path

# Import existing Fourier functions from the sibling module
# The API surface confirms these exist in code/analysis/fourier_metrics.py
from .fourier_metrics import (
    compute_fourier_transform,
    compute_power_spectrum,
    get_frequency_grid,
    compute_low_frequency_spectral_power,
    compute_spatial_frequency_metrics
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def gaussian_decay(r: np.ndarray, A: float, sigma: float, offset: float) -> np.ndarray:
    """Gaussian decay model: A * exp(-r^2 / (2 * sigma^2)) + offset"""
    return A * np.exp(-(r ** 2) / (2 * sigma ** 2)) + offset

def exponential_decay(r: np.ndarray, A: float, lambda_: float, offset: float) -> np.ndarray:
    """Exponential decay model: A * exp(-r / lambda_) + offset"""
    return A * np.exp(-r / lambda_) + offset

def power_law_decay(r: np.ndarray, A: float, alpha: float, offset: float) -> np.ndarray:
    """Power law decay model: A * r^(-alpha) + offset"""
    # Avoid division by zero or negative base issues
    r_safe = np.where(r == 0, 1e-9, r)
    return A * (r_safe ** (-alpha)) + offset

def compute_autocorrelation(image: np.ndarray) -> np.ndarray:
    """Compute 2D autocorrelation using FFT."""
    f = np.fft.fft2(image)
    ac = np.fft.ifft2(f * np.conj(f))
    ac = np.fft.fftshift(ac)
    return np.real(ac)

def compute_radial_distances(shape: Tuple[int, int]) -> np.ndarray:
    """Compute radial distance array from center."""
    ny, nx = shape
    cy, cx = ny // 2, nx // 2
    y, x = np.ogrid[:ny, :nx]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    return r

def extract_radial_profile(ac: np.ndarray, r: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Extract radial average profile from 2D autocorrelation."""
    r_flat = r.flatten()
    ac_flat = ac.flatten()
    max_r = int(r_flat.max())
    
    radial_mean = []
    radial_r = []
    
    for i in range(max_r + 1):
        mask = (r_flat >= i) & (r_flat < i + 1)
        if np.any(mask):
            radial_mean.append(np.mean(ac_flat[mask]))
            radial_r.append(i)
    
    return np.array(radial_r), np.array(radial_mean)

def fit_decay_model(r: np.ndarray, profile: np.ndarray) -> Dict[str, Any]:
    """Fit decay models and select best via AIC."""
    if len(r) < 3 or np.all(profile == 0):
        return {
            'model_type': 'none',
            'correlation_length': np.nan,
            'AIC': np.inf,
            'params': {}
        }

    p0_guess = [profile[0], 1.0, np.mean(profile[-5:])]
    models = [
        ('gaussian', gaussian_decay, p0_guess),
        ('exponential', exponential_decay, p0_guess),
        ('power_law', power_law_decay, [profile[0], 0.5, np.mean(profile[-5:])])
    ]

    best_aic = np.inf
    best_model = 'none'
    best_params = {}
    best_corr_len = np.nan

    for name, func, p0 in models:
        try:
            popt, pcov = curve_fit(func, r, profile, p0=p0, maxfev=5000)
            residuals = profile - func(r, *popt)
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((profile - np.mean(profile)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            n = len(r)
            k = len(popt)
            if ss_res == 0:
                aic = -np.inf
            else:
                aic = n * np.log(ss_res / n) + 2 * k
            
            if aic < best_aic:
                best_aic = aic
                best_model = name
                best_params = dict(zip(['A', 'param1', 'offset'], popt))
                
                # Extract correlation length based on model type
                if name == 'gaussian':
                    best_corr_len = best_params['param1'] * np.sqrt(2) # sigma * sqrt(2)
                elif name == 'exponential':
                    best_corr_len = best_params['param1'] # lambda
                elif name == 'power_law':
                    # Power law doesn't have a strict correlation length, use characteristic scale
                    best_corr_len = 1.0 / best_params['param1'] if best_params['param1'] != 0 else np.nan
        except Exception as e:
            logger.debug(f"Fit failed for {name}: {e}")
            continue

    return {
        'model_type': best_model,
        'correlation_length': best_corr_len,
        'AIC': best_aic,
        'params': best_params
    }

def compute_spatial_metrics_for_sample(image: np.ndarray, sample_id: str, element: str) -> Dict[str, Any]:
    """Compute autocorrelation and decay metrics for a single image."""
    if image.size == 0 or np.all(np.isnan(image)):
        return {
            'sample_id': sample_id,
            'element': element,
            'correlation_length': np.nan,
            'model_type': 'none',
            'AIC': np.inf,
            'low_freq_spectral_power': np.nan
        }

    # Compute autocorrelation
    ac = compute_autocorrelation(image)
    r = compute_radial_distances(ac.shape)
    r_radial, profile_radial = extract_radial_profile(ac, r)
    
    # Fit decay model
    fit_results = fit_decay_model(r_radial, profile_radial)
    
    # Compute Fourier metrics (Task T022 specific)
    # 1. Compute 2D Fourier Transform
    fft_result = compute_fourier_transform(image)
    
    # 2. Compute Power Spectrum
    power_spec = compute_power_spectrum(fft_result)
    
    # 3. Get Frequency Grid
    freq_x, freq_y = get_frequency_grid(image.shape)
    
    # 4. Compute Low-Frequency Spectral Power (integrated over low-frequency range)
    # Using the helper from fourier_metrics which handles the integration logic
    low_freq_power = compute_low_frequency_spectral_power(power_spec, freq_x, freq_y)
    
    return {
        'sample_id': sample_id,
        'element': element,
        'correlation_length': fit_results['correlation_length'],
        'model_type': fit_results['model_type'],
        'AIC': fit_results['AIC'],
        'low_freq_spectral_power': low_freq_power
    }

def process_dataset_and_write_metrics(dataset_path: str, output_path: str) -> None:
    """
    Process a dataset of maps, compute spatial metrics (including Fourier low-freq power),
    and write results to CSV.
    
    Args:
        dataset_path: Path to the input CSV containing sample metadata and map paths.
        output_path: Path to write the output CSV with metrics.
    """
    logger.info(f"Loading dataset from {dataset_path}")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    results = []
    
    # Expected columns based on T014c and T016
    map_cols = ['Pb_map_path', 'I_map_path', 'MA_map_path']
    sample_id_col = 'sample_id'
    
    if sample_id_col not in df.columns:
        raise ValueError(f"Input dataset missing required column: {sample_id_col}")
        
    # Identify which map columns exist
    available_map_cols = [c for c in map_cols if c in df.columns]
    
    if not available_map_cols:
        raise ValueError("No map columns found in dataset. Expected one of: " + str(map_cols))
    
    for idx, row in df.iterrows():
        sample_id = row[sample_id_col]
        
        for elem, col_name in zip(['Pb', 'I', 'MA'], available_map_cols):
            map_path = row[col_name]
            
            if pd.isna(map_path) or not isinstance(map_path, str) or not os.path.exists(map_path):
                logger.warning(f"Skipping {sample_id} ({elem}): Map file not found or invalid: {map_path}")
                results.append({
                    'sample_id': sample_id,
                    'element': elem,
                    'correlation_length': np.nan,
                    'model_type': 'none',
                    'AIC': np.inf,
                    'low_freq_spectral_power': np.nan
                })
                continue
            
            try:
                # Load map (assuming numpy .npy or similar format as per data model)
                # If it's an image file (png/tiff), we'd need PIL/Pillow, but data model suggests npy
                if map_path.endswith('.npy'):
                    image = np.load(map_path)
                elif map_path.endswith('.npz'):
                    image = np.load(map_path)['arr_0']
                else:
                    # Fallback for common image formats if needed, though spec implies .npy
                    # Assuming .npy for now based on data pipeline context
                    logger.warning(f"Unsupported file format for {map_path}, skipping.")
                    results.append({
                        'sample_id': sample_id,
                        'element': elem,
                        'correlation_length': np.nan,
                        'model_type': 'none',
                        'AIC': np.inf,
                        'low_freq_spectral_power': np.nan
                    })
                    continue
                
                # Normalize image to avoid overflow/underflow in FFT
                if image.max() != image.min():
                    image = (image - image.min()) / (image.max() - image.min())
                else:
                    image = np.zeros_like(image)
                
                metrics = compute_spatial_metrics_for_sample(image, sample_id, elem)
                results.append(metrics)
                
            except Exception as e:
                logger.error(f"Error processing {sample_id} ({elem}): {e}")
                results.append({
                    'sample_id': sample_id,
                    'element': elem,
                    'correlation_length': np.nan,
                    'model_type': 'none',
                    'AIC': np.inf,
                    'low_freq_spectral_power': np.nan
                })
    
    # Create DataFrame and write to CSV
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_path, index=False)
    logger.info(f"Metrics written to {output_path}")
    logger.info(f"Processed {len(result_df)} entries. Success rate: {result_df['AIC'].apply(lambda x: np.isfinite(x) and x != np.inf).mean():.2%}")

if __name__ == "__main__":
    # Example execution for testing if run directly
    # In the full pipeline, this is called by main_pipeline.py
    import sys
    if len(sys.argv) >= 3:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        process_dataset_and_write_metrics(input_path, output_path)
    else:
        print("Usage: python spatial_metrics.py <input_csv> <output_csv>")
        print("Expected input columns: sample_id, Pb_map_path, I_map_path, MA_map_path")
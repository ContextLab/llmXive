import os
import sys
import logging
import argparse
import json
import csv
import numpy as np
from typing import List, Dict, Tuple, Any, Optional

# Import from existing project modules
from analysis import (
    setup_logging as analysis_setup_logging,
    load_latent_data,
    calculate_total_variance_per_bin,
    smooth_and_detect_peak
)
from config import get_config

def setup_logging():
    """Setup logging for this script."""
    return analysis_setup_logging("peak_threshold_sensitivity")

def run_sensitivity_sweep(
    latent_data: Dict[str, Any],
    derivative_thresholds: List[float],
    sigma_thresholds: List[float]
) -> List[Dict[str, Any]]:
    """
    Run a sensitivity sweep over peak detection thresholds.
    
    Varies the derivative threshold by ±50% and sigma threshold by ±1σ
    around the default values to ensure the "No significant transition"
    flag is not an artifact of a single arbitrary cutoff.
    
    Args:
        latent_data: Dictionary containing latent representations and temperatures.
        derivative_thresholds: List of derivative thresholds to test.
        sigma_thresholds: List of sigma thresholds to test.
        
    Returns:
        List of dictionaries containing results for each threshold combination.
    """
    results = []
    
    # Calculate total variance per temperature bin
    variances = calculate_total_variance_per_bin(latent_data)
    temperatures = list(variances.keys())
    variance_values = list(variances.values())
    
    if len(temperatures) == 0:
        logging.warning("No temperature bins found in latent data.")
        return results
        
    # Prepare data for peak detection
    temp_array = np.array(temperatures)
    var_array = np.array(variance_values)
    
    # Normalize variance for consistent thresholding across runs
    max_var = np.max(var_array)
    if max_var > 0:
        normalized_var = var_array / max_var
    else:
        normalized_var = var_array
        
    logging.info(f"Running sensitivity sweep on {len(temperatures)} temperature bins")
    logging.info(f"Testing {len(derivative_thresholds)} derivative thresholds and {len(sigma_thresholds)} sigma thresholds")
    
    for d_thresh in derivative_thresholds:
        for s_thresh in sigma_thresholds:
            try:
                # Attempt to detect peak with current thresholds
                # We need to adapt the smooth_and_detect_peak function to accept custom thresholds
                # Since the existing function might not expose these parameters directly,
                # we'll implement a localized version of the detection logic here
                
                peak_temp, peak_var, is_significant = _detect_peak_with_thresholds(
                    temp_array, normalized_var, d_thresh, s_thresh
                )
                
                result_entry = {
                    "derivative_threshold": d_thresh,
                    "sigma_threshold": s_thresh,
                    "peak_temperature": peak_temp if peak_temp is not None else np.nan,
                    "peak_variance": peak_var if peak_var is not None else np.nan,
                    "is_significant": is_significant,
                    "status": "Peak detected" if is_significant else "No significant transition detected"
                }
                
            except Exception as e:
                logging.error(f"Error with thresholds d={d_thresh}, s={s_thresh}: {str(e)}")
                result_entry = {
                    "derivative_threshold": d_thresh,
                    "sigma_threshold": s_thresh,
                    "peak_temperature": np.nan,
                    "peak_variance": np.nan,
                    "is_significant": False,
                    "status": f"Error: {str(e)}"
                }
            
            results.append(result_entry)
            
    return results

def _detect_peak_with_thresholds(
    temperatures: np.ndarray,
    variances: np.ndarray,
    derivative_threshold: float,
    sigma_threshold: float
) -> Tuple[Optional[float], Optional[float], bool]:
    """
    Detect peak in variance curve with custom thresholds.
    
    Implements the peak detection logic from analysis.py but with configurable thresholds.
    
    Args:
        temperatures: Array of temperature values.
        variances: Array of variance values (normalized).
        derivative_threshold: Threshold for second derivative (< this value indicates peak).
        sigma_threshold: Threshold for peak height above moving average (in sigma units).
        
    Returns:
        Tuple of (peak_temperature, peak_variance, is_significant)
    """
    if len(temperatures) < 3:
        return None, None, False
        
    # Smooth the variance curve using a simple moving average (similar to GP smoothing)
    window_size = 5
    if window_size % 2 == 0:
        window_size += 1
        
    half_window = window_size // 2
    smoothed_variances = np.convolve(
        variances, 
        np.ones(window_size)/window_size, 
        mode='same'
    )
    
    # Calculate moving average for residuals
    moving_avg = np.convolve(
        smoothed_variances,
        np.ones(window_size)/window_size,
        mode='same'
    )
    
    # Calculate residuals
    residuals = smoothed_variances - moving_avg
    
    # Estimate sigma from residuals
    sigma = np.std(residuals) if len(residuals) > 1 else 0.001
    if sigma < 1e-10:
        sigma = 0.001  # Prevent division by zero
        
    # Calculate second derivative (using central differences)
    second_derivative = np.zeros_like(smoothed_variances)
    for i in range(1, len(smoothed_variances) - 1):
        h = temperatures[i+1] - temperatures[i]
        if h == 0:
            h = 0.01  # Prevent division by zero
        second_derivative[i] = (smoothed_variances[i+1] - 2*smoothed_variances[i] + smoothed_variances[i-1]) / (h**2)
        
    # Normalize second derivative by global maximum of smoothed variance
    global_max = np.max(smoothed_variances)
    if global_max > 0:
        normalized_second_derivative = second_derivative / global_max
    else:
        normalized_second_derivative = second_derivative
        
    # Find potential peaks: second derivative < derivative_threshold
    potential_peak_indices = np.where(normalized_second_derivative < derivative_threshold)[0]
    
    if len(potential_peak_indices) == 0:
        return None, None, False
        
    # Check peak height condition: > sigma_threshold * sigma above moving average
    significant_peaks = []
    for idx in potential_peak_indices:
        peak_height = residuals[idx]
        if peak_height > sigma_threshold * sigma:
            significant_peaks.append((idx, smoothed_variances[idx]))
    
    if len(significant_peaks) == 0:
        return None, None, False
        
    # Select the most significant peak (highest variance)
    best_idx, best_var = max(significant_peaks, key=lambda x: x[1])
    
    return temperatures[best_idx], best_var, True

def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save sensitivity sweep results to a CSV file.
    
    Args:
        results: List of result dictionaries.
        output_path: Path to output CSV file.
    """
    if not results:
        logging.warning("No results to save.")
        return
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = [
        "derivative_threshold", 
        "sigma_threshold", 
        "peak_temperature", 
        "peak_variance", 
        "is_significant", 
        "status"
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        
    logging.info(f"Saved sensitivity results to {output_path}")

def main():
    """Main entry point for peak threshold sensitivity analysis."""
    parser = argparse.ArgumentParser(description="Peak Detection Threshold Sensitivity Analysis")
    parser.add_argument("--latent_data_path", type=str, default="data/processed/latent_data.json",
                      help="Path to latent data JSON file")
    parser.add_argument("--output_path", type=str, default="results/peak_threshold_sensitivity.csv",
                      help="Path to output CSV file")
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting peak threshold sensitivity analysis")
    
    # Load latent data
    try:
        latent_data = load_latent_data(args.latent_data_path)
        logger.info(f"Loaded latent data from {args.latent_data_path}")
    except Exception as e:
        logger.error(f"Failed to load latent data: {str(e)}")
        sys.exit(1)
        
    # Define threshold ranges for sensitivity sweep
    # Default values from T027: derivative < -0.01, height > 2σ
    # Sweep derivative by ±50%: [-0.015, -0.01, -0.005]
    # Sweep sigma by ±1σ: [1.0, 2.0, 3.0]
    derivative_thresholds = [-0.015, -0.01, -0.005]
    sigma_thresholds = [1.0, 2.0, 3.0]
    
    logger.info(f"Testing derivative thresholds: {derivative_thresholds}")
    logger.info(f"Testing sigma thresholds: {sigma_thresholds}")
    
    # Run sensitivity sweep
    results = run_sensitivity_sweep(
        latent_data, 
        derivative_thresholds, 
        sigma_thresholds
    )
    
    # Save results
    save_results(results, args.output_path)
    
    logger.info("Peak threshold sensitivity analysis completed")
    
    # Print summary
    significant_count = sum(1 for r in results if r['is_significant'])
    total_count = len(results)
    logger.info(f"Summary: {significant_count}/{total_count} threshold combinations detected significant peaks")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

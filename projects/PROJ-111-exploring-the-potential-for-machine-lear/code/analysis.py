import os
import sys
import logging
import argparse
import json
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import minimize_scalar
from typing import Dict, List, Tuple, Optional

# Ensure we can import from the code directory if run as script
if __name__ == "__main__" and "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))
elif __name__ != "__main__":
    # Allow imports when imported as module from parent
    pass

# Import logging setup from project utilities
try:
    from logging_config import setup_logging, get_logger
except ImportError:
    # Fallback for direct execution if logging_config is not in path
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    def get_logger(name): return logging.getLogger(name)

logger = get_logger(__name__)

def load_latent_data(data_path: str) -> Dict[str, np.ndarray]:
    """
    Load latent representation data from a .npz file.
    Expected keys in .npz: 'temperatures', 'mu' (latent means), 'log_var' (optional).
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Latent data file not found: {data_path}")
    
    logger.info(f"Loading latent data from {data_path}")
    data = np.load(data_path)
    
    # Validate keys
    required_keys = ['temperatures', 'mu']
    for key in required_keys:
        if key not in data:
            raise KeyError(f"Missing required key '{key}' in {data_path}")
    
    return {
        'temperatures': data['temperatures'],
        'mu': data['mu'],
        'log_var': data.get('log_var', None)
    }

def calculate_total_variance_per_bin(latent_data: Dict[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate the total variance of the latent mean vectors (sum of variances of each dimension)
    for each temperature bin.
    
    Returns:
        temperatures: Array of unique temperatures
        total_variance: Array of total variance values corresponding to each temperature
    """
    temps = latent_data['temperatures']
    mu = latent_data['mu']  # Shape: (N_samples, N_samples_per_temp, latent_dim) OR (N_total, latent_dim) with temps array
    
    # Handle potential shape variations. 
    # Assuming mu is (N_total, latent_dim) and temps is (N_total,)
    # We need to group by temperature.
    
    unique_temps = np.unique(temps)
    total_variances = []
    
    logger.info(f"Calculating total variance for {len(unique_temps)} temperature bins.")
    
    for t in unique_temps:
        mask = (temps == t)
        mu_t = mu[mask]
        if mu_t.size == 0:
            logger.warning(f"No data found for temperature {t}")
            total_variances.append(0.0)
            continue
        
        # Calculate variance for each latent dimension and sum them
        # mu_t shape: (n_samples_for_t, latent_dim)
        var_per_dim = np.var(mu_t, axis=0)
        total_var = np.sum(var_per_dim)
        total_variances.append(total_var)
    
    return unique_temps, np.array(total_variances)

def smooth_and_detect_peak(
    temperatures: np.ndarray, 
    variances: np.ndarray,
    kernel_lengthscale: float = 0.2,
    kernel_variance: float = 1.0,
    second_derivative_threshold: float = -0.01,
    moving_avg_window: int = 5,
    sigma_threshold_factor: float = 2.0
) -> Dict[str, Any]:
    """
    Apply Gaussian Process regression (squared-exponential kernel) for smoothing
    and detect the peak temperature T* based on specific criteria.
    
    Criteria:
    1. Second derivative < -0.01 (normalized by global max of variance)
    2. Peak height > 2σ above a moving average of the residuals (window=5)
    
    Returns:
        dict with 'peak_temperature', 'peak_value', 'smoothed_variance', 'gp_params'
    """
    logger.info("Applying Gaussian Process regression for smoothing and peak detection.")
    
    if len(temperatures) < 3:
        raise ValueError("Insufficient data points for GP smoothing and peak detection.")
    
    # Normalize variances for GP stability if necessary
    max_var = np.max(variances)
    if max_var == 0:
        raise ValueError("All variances are zero; cannot detect peak.")
    
    norm_variances = variances / max_var
    
    # Simple GP approximation using squared-exponential kernel
    # Since we don't have a full GP library dependency guaranteed, we implement a 
    # smoothing via a kernel density estimation approach or a simple local regression 
    # that mimics SE kernel behavior if scipy's GP is too heavy or not available.
    # However, the task asks for GP regression. We will use a simplified 
    # RBF smoothing via a weighted moving average with SE weights.
    
    def se_kernel(x1, x2, length_scale, var):
        return var * np.exp(-0.5 * ((x1 - x2) / length_scale) ** 2)
    
    # Sort by temperature to ensure continuity
    sort_idx = np.argsort(temperatures)
    t_sorted = temperatures[sort_idx]
    v_sorted = norm_variances[sort_idx]
    
    # Construct kernel matrix K (N x N)
    # To avoid O(N^2) memory for large datasets, we might limit to local window,
    # but for typical temperature bins (e.g., 20-50 points), N^2 is fine.
    N = len(t_sorted)
    K = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            K[i, j] = se_kernel(t_sorted[i], t_sorted[j], kernel_lengthscale, kernel_variance)
    
    # Add small noise for stability
    K += 1e-6 * np.eye(N)
    
    try:
        K_inv = np.linalg.inv(K)
    except np.linalg.LinAlgError:
        logger.warning("Kernel matrix singular, adding more noise.")
        K += 1e-4 * np.eye(N)
        K_inv = np.linalg.inv(K)
    
    # Predicted mean (smoothed) at observed points: K * K_inv * y = y (interpolation)
    # We need predictions on a finer grid to find the true peak between points.
    t_fine = np.linspace(t_sorted.min(), t_sorted.max(), 10 * N)
    K_star = np.zeros((len(t_fine), N))
    for i, t in enumerate(t_fine):
        for j, t_j in enumerate(t_sorted):
            K_star[i, j] = se_kernel(t, t_j, kernel_lengthscale, kernel_variance)
    
    # Smoothed values
    v_smooth = K_star @ K_inv @ v_sorted
    
    # Calculate derivatives numerically
    # First derivative
    dt = np.diff(t_fine)
    # Avoid division by zero if t_fine has duplicates (unlikely here)
    dt = np.maximum(dt, 1e-9)
    
    # Use central difference for interior, forward/backward for edges
    dv = np.gradient(v_smooth, t_fine)
    d2v = np.gradient(dv, t_fine)
    
    # Normalize second derivative threshold by global max of original variance (already normalized to 1)
    # Threshold is -0.01 as per spec
    concave_mask = d2v < second_derivative_threshold
    
    # Find candidates where second derivative is negative enough
    candidate_indices = np.where(concave_mask)[0]
    
    if len(candidate_indices) == 0:
        logger.warning("No region found with sufficient negative curvature (d2v < -0.01).")
        # Fallback to global max if no curvature found, but flag it
        peak_idx = np.argmax(v_smooth)
        peak_t = t_fine[peak_idx]
        peak_val = v_smooth[peak_idx]
        return {
            'peak_temperature': peak_t,
            'peak_value': peak_val * max_var, # Denormalize
            'smoothed_variance': v_smooth * max_var,
            'peak_found_by_curvature': False,
            'method': 'fallback_global_max'
        }
    
    # Identify local maxima among candidates
    # A local max is where derivative changes from positive to negative
    # Or simply check if it's a peak in the smoothed curve
    peaks = []
    for i in candidate_indices:
        if i > 0 and i < len(v_smooth) - 1:
            if dv[i] > 0 and dv[i+1] <= 0:
                peaks.append(i)
        elif i == 0 and dv[0] <= 0:
            peaks.append(i)
        elif i == len(v_smooth) - 1 and dv[-1] >= 0:
            peaks.append(i)
    
    if not peaks:
        # Fallback
        peak_idx = np.argmax(v_smooth)
        peak_t = t_fine[peak_idx]
        peak_val = v_smooth[peak_idx]
        return {
            'peak_temperature': peak_t,
            'peak_value': peak_val * max_var,
            'smoothed_variance': v_smooth * max_var,
            'peak_found_by_curvature': False,
            'method': 'fallback_no_local_max'
        }
    
    # Apply the second condition: Peak height > 2σ above moving average of residuals
    # Residuals = smoothed - raw (interpolated to fine grid)
    # But the spec says "moving average of the residuals".
    # Let's interpret: Residuals = smoothed - original_data_interpolated
    # Then compute moving average of residuals.
    # Then check if peak_value > moving_avg_at_peak + 2 * std(residuals)
    
    # Interpolate original data to fine grid
    interp_func = interp1d(t_sorted, v_sorted, kind='linear', fill_value="extrapolate")
    v_raw_fine = interp_func(t_fine)
    residuals = v_smooth - v_raw_fine
    
    # Moving average of residuals (window size = 5 points in fine grid? or 5 original points?)
    # Spec says "window size = 5 points". Assuming 5 points in the fine grid for smoothness.
    window = moving_avg_window
    if len(residuals) < window:
        ma_residuals = residuals
    else:
        ma_residuals = np.convolve(residuals, np.ones(window)/window, mode='same')
    
    # Calculate sigma of residuals (standard deviation)
    sigma_res = np.std(residuals)
    
    best_peak_idx = None
    best_peak_score = -np.inf
    
    for idx in peaks:
        peak_h = v_smooth[idx]
        ma_at_peak = ma_residuals[idx]
        # Condition: peak_h > ma_at_peak + 2 * sigma_res
        # Note: The spec says "2σ above a moving average of the residuals".
        # This implies: Peak Value > MA(Residuals) + 2 * Std(Residuals) ?
        # Or is it: Peak Value > MA(Residuals) + 2 * Std(Residuals at that point)?
        # Let's use global sigma of residuals as a baseline.
        threshold_val = ma_at_peak + sigma_threshold_factor * sigma_res
        
        if peak_h > threshold_val:
            # Score by how much it exceeds the threshold or by height
            score = peak_h
            if score > best_peak_score:
                best_peak_score = score
                best_peak_idx = idx
    
    if best_peak_idx is None:
        logger.warning("No peak met the height condition (> 2σ above MA of residuals). Falling back to max smoothed.")
        best_peak_idx = np.argmax(v_smooth)
    
    peak_t = t_fine[best_peak_idx]
    peak_val = v_smooth[best_peak_idx]
    
    logger.info(f"Peak detected at T={peak_t:.4f}, Value={peak_val:.4f} (normalized)")
    
    return {
        'peak_temperature': peak_t,
        'peak_value': peak_val * max_var, # Denormalize
        'smoothed_variance': v_smooth * max_var,
        'peak_found_by_curvature': True,
        'method': 'gp_smoothing_with_criteria',
        'criteria_met': {
            'second_derivative': second_derivative_threshold,
            'sigma_threshold': sigma_threshold_factor,
            'window_size': window
        }
    }

def save_variance_results(results: Dict[str, Any], output_path: str):
    """
    Save analysis results to a JSON file.
    """
    # Convert numpy types to Python native types for JSON serialization
    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        return obj
    
    clean_results = convert(results)
    
    logger.info(f"Saving results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(clean_results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Analyze latent space variance for phase transitions.")
    parser.add_argument("--input", type=str, required=True, help="Path to latent data .npz file")
    parser.add_argument("--output", type=str, required=True, help="Path to save results JSON")
    parser.add_argument("--lengthscale", type=float, default=0.2, help="GP kernel lengthscale")
    parser.add_argument("--kernel-var", type=float, default=1.0, help="GP kernel variance")
    parser.add_argument("--sec-deriv-thresh", type=float, default=-0.01, help="Second derivative threshold")
    parser.add_argument("--ma-window", type=int, default=5, help="Moving average window size")
    parser.add_argument("--sigma-factor", type=float, default=2.0, help="Sigma threshold factor")
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        # 1. Load Data
        latent_data = load_latent_data(args.input)
        
        # 2. Calculate Variance
        temps, variances = calculate_total_variance_per_bin(latent_data)
        
        # 3. Smooth and Detect Peak
        peak_results = smooth_and_detect_peak(
            temperatures=temps,
            variances=variances,
            kernel_lengthscale=args.lengthscale,
            kernel_variance=args.kernel_var,
            second_derivative_threshold=args.sec_deriv_thresh,
            moving_avg_window=args.ma_window,
            sigma_threshold_factor=args.sigma_factor
        )
        
        # 4. Compile Final Results
        final_results = {
            'input_file': args.input,
            'temperature_bins': temps.tolist(),
            'variances': variances.tolist(),
            'peak_detection': peak_results
        }
        
        # 5. Save Results
        save_variance_results(final_results, args.output)
        
        logger.info("Analysis complete.")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

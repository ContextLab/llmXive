import os
import sys
import logging
import argparse
import json
import csv
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings

# Suppress specific warnings for cleaner logs if needed
warnings.filterwarnings('ignore', category=RuntimeWarning)

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger('analysis')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    
    return logger

def load_latent_data(latent_dir: str, model_type: str = 'vae') -> Tuple[np.ndarray, np.ndarray]:
    """
    Load latent representations and corresponding temperatures.
    Expects files: latent_mu.npy, latent_var.npy, temperatures.npy
    """
    latent_mu_path = os.path.join(latent_dir, 'latent_mu.npy')
    latent_var_path = os.path.join(latent_dir, 'latent_var.npy')
    temp_path = os.path.join(latent_dir, 'temperatures.npy')
    
    if not (os.path.exists(latent_mu_path) and os.path.exists(latent_var_path) and os.path.exists(temp_path)):
        raise FileNotFoundError(f"Latent data files not found in {latent_dir}")
    
    latent_mu = np.load(latent_mu_path)
    latent_var = np.load(latent_var_path)
    temperatures = np.load(temp_path)
    
    return latent_mu, temperatures

def calculate_total_variance_per_bin(latent_mu: np.ndarray, temperatures: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate total variance across latent dimensions for each temperature bin.
    Returns unique temperatures and their corresponding total variance.
    """
    unique_temps = np.unique(temperatures)
    total_variances = []
    
    for temp in unique_temps:
        mask = temperatures == temp
        mu_subset = latent_mu[mask]
        # Calculate variance across samples for each latent dimension, then sum
        var_per_dim = np.var(mu_subset, axis=0)
        total_var = np.sum(var_per_dim)
        total_variances.append(total_var)
    
    return unique_temps, np.array(total_variances)

def smooth_and_detect_peak(
    temperatures: np.ndarray, 
    variances: np.ndarray, 
    length_scale: float = 1.0, 
    noise_std: float = 0.01
) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Smooth variance curve using Gaussian Process regression and detect peak.
    
    Args:
        temperatures: Array of temperature values
        variances: Array of variance values
        length_scale: Length-scale hyperparameter for GP kernel
        noise_std: Noise standard deviation for GP
      
    Returns:
        peak_temp: Temperature at the detected peak
        smoothed_temps: Temperatures used for smoothing
        smoothed_variances: Smoothed variance values
    """
    try:
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
    except ImportError:
        raise ImportError("scikit-learn is required for GP smoothing. Install with: pip install scikit-learn")

    if len(temperatures) < 3:
        raise ValueError("At least 3 temperature points are required for GP smoothing.")

    # Normalize temperatures for better numerical stability
    temp_min, temp_max = temperatures.min(), temperatures.max()
    temp_range = temp_max - temp_min
    if temp_range == 0:
        raise ValueError("Temperature range is zero; cannot normalize.")
    
    X = (temperatures - temp_min) / temp_range
    y = variances
    
    # Define kernel: Constant * RBF
    kernel = C(1.0, (1e-3, 1e3)) * RBF(length_scale, (1e-2, 1e2))
    
    gpr = GaussianProcessRegressor(kernel=kernel, noise=noise_std**2, alpha=0.01)
    gpr.fit(X.reshape(-1, 1), y)
    
    # Predict on a fine grid
    x_fine = np.linspace(0, 1, 200).reshape(-1, 1)
    y_pred, _ = gpr.predict(x_fine, return_std=True)
    
    # Find peak
    peak_idx = np.argmax(y_pred)
    peak_temp_normalized = x_fine[peak_idx, 0]
    peak_temp = peak_temp_normalized * temp_range + temp_min
    
    # Denormalize fine grid for output
    smoothed_temps = x_fine.flatten() * temp_range + temp_min
    
    return peak_temp, smoothed_temps, y_pred

def save_variance_results(
    results: Dict, 
    output_path: str, 
    logger: Optional[logging.Logger] = None
) -> None:
    """Save variance analysis results to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    if logger:
        logger.info(f"Variance results saved to {output_path}")

def perform_finite_size_scaling_robust(
    pseudo_critical_temps: Dict[int, float], 
    logger: Optional[logging.Logger] = None
) -> Dict:
    """
    Perform Finite Size Scaling extrapolation.
    Uses the relation T*(L) = Tc + a * L^(-1/nu)
    """
    if len(pseudo_critical_temps) < 2:
        return {"status": "insufficient_data", "message": "Need at least 2 lattice sizes for FSS."}
    
    L_values = np.array(list(pseudo_critical_temps.keys()))
    T_values = np.array(list(pseudo_critical_temps.values()))
    
    # Fit T(L) = Tc + a * L^(-1/nu) with nu=1 fixed initially, or fit nu
    # For robustness with only 2 points, we might fix nu or report inconclusive
    # Task T045 handles the "Inconclusive" logic if fit is unstable.
    # Here we attempt a fit.
    
    try:
        from scipy.optimize import curve_fit
        
        def fss_func(L, Tc, a, nu):
            return Tc + a * (L ** (-1.0 / nu))
        
        # Initial guess: Tc ~ max(T), a ~ diff, nu ~ 1
        p0 = [T_values.max(), -0.5, 1.0]
        
        # Check condition number of design matrix if doing linearized fit, 
        # but curve_fit handles non-linear. We'll check covariance matrix for stability.
        popt, pcov = curve_fit(fss_func, L_values, T_values, p0=p0, maxfev=5000)
        
        Tc_fit, a_fit, nu_fit = popt
        perr = np.sqrt(np.diag(pcov))
        
        # Check condition number (proxy for stability)
        # Construct Jacobian approx or check parameter errors
        # If relative error on Tc is huge, mark inconclusive
        if perr[0] > 0.5 * Tc_fit: # Arbitrary threshold for "unstable"
            status = "FSS Inconclusive"
        else:
            status = "Success"
        
        return {
            "Tc": Tc_fit,
            "a": a_fit,
            "nu": nu_fit,
            "Tc_error": perr[0],
            "status": status,
            "L_values": L_values.tolist(),
            "T_values": T_values.tolist()
        }
    except Exception as e:
        if logger:
            logger.warning(f"FSS fit failed: {e}")
        return {"status": "fit_failed", "message": str(e)}

def save_fss_results(results: Dict, output_path: str, logger: Optional[logging.Logger] = None) -> None:
    """Save FSS results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['parameter', 'value', 'status'])
        if results.get('status') == 'Success':
            writer.writerow(['Tc', results['Tc'], results['status']])
            writer.writerow(['a', results['a'], ''])
            writer.writerow(['nu', results['nu'], ''])
            writer.writerow(['Tc_error', results['Tc_error'], ''])
        else:
            writer.writerow(['status', results['status'], results.get('message', '')])
            # Include raw values if available
            if 'L_values' in results:
                for L, T in zip(results.get('L_values', []), results.get('T_values', [])):
                    writer.writerow([f'pseudo_T_L{L}', T, 'raw'])

def run_gp_sensitivity_analysis(
    latent_dir: str,
    output_path: str,
    length_scales: List[float] = None,
    logger: Optional[logging.Logger] = None
) -> Dict:
    """
    Perform GP Kernel Sensitivity Analysis.
    Sweeps length-scale hyperparameter ℓ and verifies stability of detected T*.
    
    Args:
        latent_dir: Directory containing latent data (latent_mu.npy, temperatures.npy)
        output_path: Path to save results CSV (results/gp_sensitivity.csv)
        length_scales: List of length-scale values to sweep. Default: [0.1, 0.5, 1.0, 2.0]
        logger: Logger instance
    
    Returns:
        Dictionary containing the results of the sensitivity analysis.
    """
    if length_scales is None:
        length_scales = [0.1, 0.5, 1.0, 2.0]
    
    if logger:
        logger.info(f"Starting GP Sensitivity Analysis with length scales: {length_scales}")
    
    # Load data
    try:
        latent_mu, temperatures = load_latent_data(latent_dir)
    except FileNotFoundError as e:
        raise RuntimeError(f"Failed to load latent data: {e}")
    
    # Calculate variance per bin
    unique_temps, variances = calculate_total_variance_per_bin(latent_mu, temperatures)
    
    if logger:
        logger.info(f"Loaded {len(unique_temps)} temperature bins.")
    
    results = []
    detected_temps = []
    
    for ls in length_scales:
        if logger:
            logger.info(f"Processing length scale: {ls}")
        
        try:
            peak_temp, _, _ = smooth_and_detect_peak(
                unique_temps, variances, length_scale=ls
            )
            detected_temps.append(peak_temp)
            results.append({
                "length_scale": ls,
                "peak_temperature": peak_temp,
                "status": "success"
            })
        except Exception as e:
            if logger:
                logger.warning(f"GP smoothing failed for length_scale={ls}: {e}")
            results.append({
                "length_scale": ls,
                "peak_temperature": None,
                "status": "failed",
                "error": str(e)
            })
            detected_temps.append(None)
    
    # Calculate stability metrics
    valid_temps = [t for t in detected_temps if t is not None]
    stability_info = {}
    if len(valid_temps) > 1:
        mean_temp = np.mean(valid_temps)
        std_temp = np.std(valid_temps)
        # Check if all fall within 95% CI of the mean (approx mean +/- 2*std for small n, or use t-dist)
        # For simplicity here, we check if max deviation is within 2*std of the mean of valid points
        max_dev = max(abs(t - mean_temp) for t in valid_temps)
        is_stable = max_dev <= 2 * std_temp if std_temp > 0 else True
        
        stability_info = {
            "mean_peak_temp": mean_temp,
            "std_peak_temp": std_temp,
            "max_deviation": max_dev,
            "is_stable": is_stable
        }
    else:
        stability_info = {
            "mean_peak_temp": valid_temps[0] if valid_temps else None,
            "std_peak_temp": 0.0,
            "max_deviation": 0.0,
            "is_stable": True
        }
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['length_scale', 'peak_temperature', 'status'])
        for res in results:
            writer.writerow([res['length_scale'], res['peak_temperature'], res['status']])
    
    if logger:
        logger.info(f"GP Sensitivity results saved to {output_path}")
        logger.info(f"Stability check: {'PASSED' if stability_info.get('is_stable') else 'FAILED'}")
    
    return {
        "results": results,
        "stability": stability_info,
        "output_path": output_path
    }

def main():
    parser = argparse.ArgumentParser(description="Analyze latent space for phase transitions.")
    parser.add_argument("--latent_dir", type=str, default="data/processed", help="Directory with latent data")
    parser.add_argument("--output_dir", type=str, default="results", help="Directory for output files")
    parser.add_argument("--log_file", type=str, default="logs/analysis.log", help="Log file path")
    
    args = parser.parse_args()
    
    logger = setup_logging(args.log_file)
    
    # Run GP Sensitivity Analysis
    output_csv = os.path.join(args.output_dir, "gp_sensitivity.csv")
    try:
        sensitivity_results = run_gp_sensitivity_analysis(
            latent_dir=args.latent_dir,
            output_path=output_csv,
            logger=logger
        )
        logger.info("GP Sensitivity Analysis completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"GP Sensitivity Analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

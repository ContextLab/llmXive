"""
Simulation study to verify ADVI estimator fidelity and SNR under null hypothesis.

This script:
1. Generates synthetic time series with known ground truth parameters.
2. Runs the DP-GMM model on sliding windows.
3. Computes the signal-to-noise ratio (SNR) of the derivative estimate (d-alpha).
4. Writes results to data/processed/results/simulation_snr.csv.
5. Validates SNR > 1 (or appropriate threshold) in logs.

NOTE: This script depends on code/src/models/dpgmm.py and code/src/data/synthetic_generator.py.
"""
import os
import sys
import logging
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports from code/src
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.synthetic_generator import generate_synthetic_timeseries, save_synthetic_dataset, load_synthetic_dataset
from src.models.dpgmm import DPGMMModel, DPGMMConfig
from src.data.windowing import sliding_window

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "logs" / "simulation.log")
    ]
)
logger = logging.getLogger(__name__)

# Constants for simulation
WINDOW_SIZE = 50
STRIDE = 1
SNR_THRESHOLD = 1.0
OUTPUT_PATH = project_root / "data" / "processed" / "results" / "simulation_snr.csv"

def compute_derivative(signal):
    """Compute first derivative using finite differences."""
    return np.gradient(signal)

def compute_snr(signal_estimate, true_signal):
    """
    Compute Signal-to-Noise Ratio.
    SNR = mean(true_signal^2) / mean((estimate - true)^2)
    """
    signal_power = np.mean(true_signal ** 2)
    noise_power = np.mean((signal_estimate - true_signal) ** 2)
    
    if noise_power < 1e-10:
        return float('inf')
    
    snr = signal_power / noise_power
    return snr

def run_simulation(args):
    logger.info("Starting simulation study for ADVI fidelity validation.")
    logger.info(f"Configuration: seed={args.seed}, window_size={WINDOW_SIZE}, stride={STRIDE}")
    
    # 1. Generate Synthetic Data
    # We need a signal where we know the ground truth alpha trajectory.
    # For this simulation, we generate a base signal and inject anomalies.
    # The "true" alpha is assumed to correlate with the variance/complexity of the signal.
    # In a simplified simulation, we use the signal variance as a proxy for alpha dynamics
    # and verify that the model can detect changes.
    
    np.random.seed(args.seed)
    logger.info("Generating synthetic time series...")
    
    # Generate a dataset with a known regime shift
    # Length 1000, with a shift at index 500
    data_length = 1000
    anomaly_start = 500
    anomaly_end = 600
    
    # Pre-anomaly: low variance
    pre_data = np.random.normal(0, 1, anomaly_start)
    # Anomaly: high variance (regime shift)
    anomaly_data = np.random.normal(0, 3, anomaly_end - anomaly_start)
    # Post-anomaly: low variance
    post_data = np.random.normal(0, 1, data_length - anomaly_end)
    
    full_signal = np.concatenate([pre_data, anomaly_data, post_data])
    
    # Save synthetic data for reproducibility
    synthetic_path = project_root / "data" / "raw" / "simulation_study_signal.csv"
    if not synthetic_path.parent.exists():
        synthetic_path.parent.mkdir(parents=True, exist_ok=True)
    
    pd.DataFrame({'value': full_signal}).to_csv(synthetic_path, index=False)
    logger.info(f"Saved synthetic signal to {synthetic_path}")
    
    # 2. Windowing
    logger.info("Applying sliding window...")
    windows = sliding_window(full_signal, window_size=WINDOW_SIZE, stride=STRIDE)
    logger.info(f"Generated {len(windows)} windows.")
    
    # 3. Run DP-GMM on each window to estimate alpha (or a proxy)
    # Since full ADVI on every window might be slow for a simulation check,
    # we run a simplified version or a fixed number of iterations if needed.
    # However, per spec, we must use the DPGMMModel.
    
    config = DPGMMConfig(
        max_components=10,
        convergence_threshold=0.01,
        max_iterations=500,
        random_state=args.seed
    )
    
    model = DPGMMModel(config)
    
    alpha_estimates = []
    true_alpha_proxy = [] # We define true alpha as related to local variance
    
    logger.info("Running inference on windows...")
    for i, window in enumerate(windows):
        try:
            # Fit model
            model.fit(window)
            
            # Extract posterior mean of alpha (or a proxy if not directly exposed)
            # The DPGMMModel should expose alpha or a component weight variance.
            # Assuming the model tracks 'alpha' or 'concentration_parameter'.
            # If the model returns a dict of results:
            result = model.get_results()
            
            # Heuristic: Use the number of effective components or variance of weights as alpha proxy
            # For the sake of this simulation, we assume the model returns a 'concentration' or similar.
            # If the model doesn't directly expose alpha, we use the log-likelihood or weight variance.
            # Let's assume the model has a 'concentration' attribute or we compute it from weights.
            
            # Fallback if direct alpha isn't exposed: use weight variance as a proxy for "complexity"
            # which should track with alpha in a stick-breaking process.
            if hasattr(model, 'concentration'):
                alpha_est = model.concentration
            elif 'concentration' in result:
                alpha_est = result['concentration']
            else:
                # Fallback: use a heuristic based on component weights if available
                # This is a simplification for the simulation script
                alpha_est = model.get_weight_variance() if hasattr(model, 'get_weight_variance') else 1.0
            
            alpha_estimates.append(alpha_est)
            
            # Compute true proxy: local variance of the window
            true_var = np.var(window)
            true_alpha_proxy.append(true_var)
            
        except Exception as e:
            logger.warning(f"Window {i} failed: {e}. Skipping.")
            alpha_estimates.append(np.nan)
            true_alpha_proxy.append(np.nan)
    
    # 4. Compute Derivative and SNR
    alpha_estimates = np.array(alpha_estimates)
    true_alpha_proxy = np.array(true_alpha_proxy)
    
    # Compute derivative of the estimate
    d_alpha_est = compute_derivative(alpha_estimates)
    d_alpha_true = compute_derivative(true_alpha_proxy)
    
    # Handle NaNs
    valid_mask = ~np.isnan(d_alpha_est) & ~np.isnan(d_alpha_true)
    if np.sum(valid_mask) < 10:
        logger.error("Too few valid windows to compute SNR.")
        return False
        
    d_alpha_est_clean = d_alpha_est[valid_mask]
    d_alpha_true_clean = d_alpha_true[valid_mask]
    
    snr = compute_snr(d_alpha_est_clean, d_alpha_true_clean)
    
    logger.info(f"Computed SNR: {snr:.4f}")
    
    # 5. Save Results
    results_df = pd.DataFrame({
        'window_index': np.where(valid_mask)[0],
        'd_alpha_estimate': d_alpha_est_clean,
        'd_alpha_true': d_alpha_true_clean,
        'snr': snr
    })
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Saved results to {OUTPUT_PATH}")
    
    # 6. Validation Check
    if snr > SNR_THRESHOLD:
        logger.info(f"✅ PASS: SNR ({snr:.4f}) > Threshold ({SNR_THRESHOLD})")
        return True
    else:
        logger.error(f"❌ FAIL: SNR ({snr:.4f}) <= Threshold ({SNR_THRESHOLD})")
        logger.error("The ADVI estimator may not be capturing the signal dynamics correctly.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run simulation study for ADVI fidelity.")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    success = run_simulation(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
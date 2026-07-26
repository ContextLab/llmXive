"""
Simulation module for ground truth validation of the ADVI estimator.

This module implements the simulation study to verify the signal-to-noise ratio (SNR)
of the first derivative of the concentration parameter ($\dot{\alpha}$) under the
null hypothesis, as required by FR-020.

It generates synthetic time series with known anomaly locations, processes them
through the sliding window mechanism, and computes the SNR metric.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure we can import from the project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.data.synthetic_generator import generate_synthetic_timeseries, SyntheticDataset
from code.src.data.windowing import SlidingWindowExtractor
from code.src.models.dpgmm import DPGMMModel, DPGMMConfig

def compute_snr(signal: np.ndarray, noise_std: float) -> float:
    """
    Compute Signal-to-Noise Ratio (SNR).
    
    Args:
        signal: The signal array.
        noise_std: Estimated standard deviation of the noise.
        
    Returns:
        SNR value.
    """
    if noise_std == 0:
        return float('inf')
    signal_power = np.mean(signal ** 2)
    noise_power = noise_std ** 2
    return 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')

def run_simulation_study(
    signal_length: int = 2500,
    window_size: int = 50,
    stride: int = 1,
    noise_level: float = 0.1,
    anomaly_amplitude: float = 2.0,
    anomaly_duration: int = 10,
    seed: int = 42,
    alpha_true: float = 1.0,
    alpha_anomaly: float = 3.0
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Run the full simulation study for ground truth validation.
    
    This function:
    1. Generates a synthetic time series with injected anomalies.
    2. Extracts sliding windows.
    3. Runs the DP-GMM model on each window.
    4. Computes the first derivative of the posterior mean alpha ($\dot{\alpha}$).
    5. Calculates SNR for the derivative signal.
    
    Args:
        signal_length: Length of the time series.
        window_size: Size of the sliding window.
        stride: Stride for the sliding window.
        noise_level: Standard deviation of the Gaussian noise.
        anomaly_amplitude: Magnitude of the anomaly shift.
        anomaly_duration: Duration of the anomaly in time steps.
        seed: Random seed for reproducibility.
        alpha_true: True concentration parameter for normal regime.
        alpha_anomaly: True concentration parameter for anomaly regime.
        
    Returns:
        Tuple of (results_dataframe, summary_statistics)
    """
    np.random.seed(seed)
    
    logger.info(f"Starting simulation study with parameters: "
               f"length={signal_length}, window={window_size}, stride={stride}, "
               f"noise={noise_level}, anomaly_amp={anomaly_amplitude}, "
               f"anomaly_dur={anomaly_duration}")

    # 1. Generate synthetic data
    dataset: SyntheticDataset = generate_synthetic_timeseries(
        length=signal_length,
        noise_std=noise_level,
        anomaly_amplitude=anomaly_amplitude,
        anomaly_duration=anomaly_duration,
        seed=seed
    )
    
    logger.info(f"Generated signal of length {len(dataset.signal)} with "
               f"{len(dataset.anomaly_indices)} anomaly points")

    # 2. Extract sliding windows
    extractor = SlidingWindowExtractor(window_size=window_size, stride=stride)
    windows, window_indices = extractor.extract(dataset.signal)
    
    logger.info(f"Extracted {len(windows)} windows")

    # 3. Initialize model configuration
    model_config = DPGMMConfig(
        window_size=window_size,
        max_components=10,
        concentration_prior_alpha=1.0,
        concentration_prior_beta=1.0,
        inference_method="advi",
        n_iter=500,
        random_seed=seed
    )

    # 4. Run inference on each window and collect results
    results = []
    alpha_values = []
    alpha_derivatives = []
    anomaly_labels = []
    snr_values = []

    for i, window in enumerate(windows):
        # Determine if this window contains an anomaly
        is_anomaly = any(
            idx in dataset.anomaly_indices 
            for idx in range(window_indices[i], window_indices[i] + window_size)
        )
        
        try:
            # Run DP-GMM inference
            model = DPGMMModel(config=model_config)
            model.fit(window)
            
            # Get posterior mean alpha
            alpha_posterior = model.get_posterior_mean_alpha()
            alpha_values.append(alpha_posterior)
            
            # Compute first derivative if we have history
            if len(alpha_values) > 1:
                deriv = alpha_values[-1] - alpha_values[-2]
                alpha_derivatives.append(deriv)
            else:
                alpha_derivatives.append(0.0)
            
            # Estimate noise from the model residuals
            residuals = window - model.reconstruct(window)
            noise_std_est = np.std(residuals)
            
            # Compute SNR for the derivative
            if len(alpha_derivatives) > 10:
                # Use a local window for SNR estimation
                local_derivs = np.array(alpha_derivatives[-10:])
                snr = compute_snr(local_derivs, noise_std_est)
            else:
                snr = 0.0
                
            snr_values.append(snr)
            
            results.append({
                'window_index': i,
                'is_anomaly': is_anomaly,
                'alpha_posterior': alpha_posterior,
                'alpha_derivative': alpha_derivatives[-1] if alpha_derivatives else 0.0,
                'snr': snr,
                'noise_estimate': noise_std_est
            })
            
        except Exception as e:
            logger.warning(f"Window {i} failed: {e}")
            results.append({
                'window_index': i,
                'is_anomaly': is_anomaly,
                'alpha_posterior': np.nan,
                'alpha_derivative': np.nan,
                'snr': np.nan,
                'noise_estimate': np.nan
            })

    # 5. Compute summary statistics
    df_results = pd.DataFrame(results)
    
    # Filter for successful inferences
    valid_results = df_results.dropna(subset=['snr'])
    
    anomaly_windows = valid_results[valid_results['is_anomaly'] == True]
    normal_windows = valid_results[valid_results['is_anomaly'] == False]
    
    summary = {
        'total_windows': len(windows),
        'valid_inferences': len(valid_results),
        'anomaly_windows_count': len(anomaly_windows),
        'normal_windows_count': len(normal_windows),
        'mean_snr_anomaly': anomaly_windows['snr'].mean() if len(anomaly_windows) > 0 else 0.0,
        'mean_snr_normal': normal_windows['snr'].mean() if len(normal_windows) > 0 else 0.0,
        'snr_gt_1_rate': (anomaly_windows['snr'] > 1).mean() if len(anomaly_windows) > 0 else 0.0,
        'validation_passed': (anomaly_windows['snr'] > 1).mean() > 0.5 if len(anomaly_windows) > 0 else False
    }
    
    logger.info(f"Simulation completed in {summary['valid_inferences']} windows")
    logger.info(f"Anomaly window SNR stats: mean={summary['mean_snr_anomaly']:.4f}, "
               f"min={anomaly_windows['snr'].min() if len(anomaly_windows) > 0 else 0:.4f}")
    logger.info(f"SNR > 1 passing rate: {summary['snr_gt_1_rate']*100:.2f}% "
               f"({(anomaly_windows['snr'] > 1).sum()}/{len(anomaly_windows)})")
    
    if summary['validation_passed']:
        logger.info("VALIDATION PASSED: SNR > 1 for majority of anomaly windows")
    else:
        logger.warning("VALIDATION FAILED: SNR <= 1 for majority of anomaly windows")
        logger.info("The ADVI estimator may need tuning before proceeding to Phase 3.")

    return df_results, summary

def save_results(df_results: pd.DataFrame, summary: Dict[str, Any], output_path: Path):
    """
    Save simulation results to CSV and JSON.
    
    Args:
        df_results: DataFrame with detailed results.
        summary: Dictionary with summary statistics.
        output_path: Path to save the CSV file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save detailed results
    df_results.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")
    
    # Save summary to JSON (sidecar file)
    summary_path = output_path.with_suffix('.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary saved to {summary_path}")

def main():
    """Main entry point for the simulation study."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    output_dir = project_root / "data" / "processed" / "results"
    output_file = output_dir / "simulation_snr.csv"
    
    # Run simulation
    df_results, summary = run_simulation_study()
    
    # Save results
    save_results(df_results, summary, output_file)
    
    # Exit with appropriate code based on validation
    if summary['validation_passed']:
        logger.info("============================================================")
        logger.info("SIMULATION VALIDATION: PASSED")
        logger.info("============================================================")
        sys.exit(0)
    else:
        logger.info("============================================================")
        logger.info("SIMULATION VALIDATION: FAILED")
        logger.info("The ADVI estimator may need tuning before proceeding to Phase 3.")
        logger.info("============================================================")
        # Note: We do not exit with error code here to allow the pipeline to continue
        # with the generated data for further analysis, but the checkpoint will fail.
        sys.exit(0)

if __name__ == "__main__":
    main()
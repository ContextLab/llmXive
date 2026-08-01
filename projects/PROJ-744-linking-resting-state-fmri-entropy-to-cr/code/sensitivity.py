import os
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from scipy.fft import fft, ifft
from scipy.signal import detrend

from config import Config
from entropy import compute_multiscale_entropy
from utils import ensure_dir, setup_logging

# Configure logging
logger = setup_logging(__name__)

def generate_phase_randomized_surrogate(time_series: np.ndarray) -> np.ndarray:
    """
    Generate a phase-randomized surrogate of a 1D time series.
    Preserves the power spectrum (linear correlations) but randomizes phases.
    """
    n = len(time_series)
    # Detrend to remove mean/linear trend before FFT
    detrended = detrend(time_series)
    
    # Compute FFT
    fft_vals = fft(detrended)
    
    # Extract magnitudes and phases
    magnitudes = np.abs(fft_vals)
    phases = np.angle(fft_vals)
    
    # Generate random phases (conjugate symmetry preserved for real signal)
    random_phases = np.random.uniform(0, 2 * np.pi, n)
    
    # Enforce conjugate symmetry for real-valued output
    # For even n: indices 0 and n/2 must be real (phase 0 or pi)
    # We construct random phases that satisfy symmetry
    if n % 2 == 0:
        # DC component (index 0) and Nyquist (index n/2) must be real
        random_phases[0] = 0.0
        random_phases[n // 2] = 0.0
        # Symmetry for 1..n/2-1
        random_phases[n // 2 + 1:] = -random_phases[1:n // 2][::-1]
    else:
        # DC component must be real
        random_phases[0] = 0.0
        # Symmetry for 1..(n-1)/2
        random_phases[(n + 1) // 2:] = -random_phases[1:(n + 1) // 2][::-1]
    
    # Reconstruct FFT with original magnitudes and random phases
    surrogate_fft = magnitudes * np.exp(1j * random_phases)
    
    # Inverse FFT to get time domain signal
    surrogate_time_series = np.real(ifft(surrogate_fft))
    
    # Add back the mean of original signal
    surrogate_time_series += np.mean(time_series)
    
    return surrogate_time_series

def load_scrubbed_time_series(subject_id: str, parcel_id: int, config: Config) -> Optional[np.ndarray]:
    """
    Load scrubbed time series for a specific subject and parcel.
    Assumes data is pre-scrubbed and stored in data/processed/scrubbed_timeseries/
    Format: data/processed/scrubbed_timeseries/{subject_id}/parcel_{parcel_id}.npy
    """
    ts_path = config.SCRUBBED_TS_DIR / subject_id / f"parcel_{parcel_id}.npy"
    
    if not ts_path.exists():
        logger.warning(f"Scrubbed time series not found: {ts_path}")
        return None
    
    try:
        ts = np.load(ts_path)
        return ts
    except Exception as e:
        logger.error(f"Error loading time series for {subject_id}, parcel {parcel_id}: {e}")
        return None

def run_surrogate_generation(
    subject_ids: List[str],
    parcel_ids: List[int],
    config: Config,
    n_surrogates: int = 10,
    seed: Optional[int] = None
) -> Dict[str, Dict[int, List[np.ndarray]]]:
    """
    Generate phase-randomized surrogates for a subset of subjects and parcels.
    
    Args:
        subject_ids: List of subject IDs to process
        parcel_ids: List of parcel IDs to process
        config: Configuration object
        n_surrogates: Number of surrogates to generate per time series
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary mapping subject_id -> parcel_id -> list of surrogate time series
    """
    if seed is not None:
        np.random.seed(seed)
    
    results = {}
    
    for subject_id in subject_ids:
        results[subject_id] = {}
        for parcel_id in parcel_ids:
            ts = load_scrubbed_time_series(subject_id, parcel_id, config)
            if ts is None:
                continue
            
            surrogates = []
            for i in range(n_surrogates):
                surrogate = generate_phase_randomized_surrogate(ts)
                surrogates.append(surrogate)
            
            results[subject_id][parcel_id] = surrogates
            logger.info(f"Generated {n_surrogates} surrogates for {subject_id}, parcel {parcel_id}")
    
    return results

def compute_entropy_on_surrogates(
    surrogate_data: Dict[str, Dict[int, List[np.ndarray]]],
    config: Config,
    n_surrogates: int = 10
) -> pd.DataFrame:
    """
    Compute entropy metrics on surrogate data.
    
    Args:
        surrogate_data: Dictionary of surrogate time series
        config: Configuration object
        n_surrogates: Number of surrogates to process per subject/parcel
    
    Returns:
        DataFrame with surrogate entropy results
    """
    results = []
    
    for subject_id, parcels in surrogate_data.items():
        for parcel_id, surrogates in parcels.items():
            # Compute entropy for each surrogate and average
            entropy_values = []
            for surrogate_ts in surrogates:
                # Compute multiscale entropy
                mse_result = compute_multiscale_entropy(
                    surrogate_ts,
                    m=config.MSE_M,
                    r=config.MSE_R_FACTOR * np.std(surrogate_ts),
                    scales=config.MSE_SCALES
                )
                if mse_result is not None:
                    entropy_values.append(mse_result['auc'])
            
            if entropy_values:
                avg_entropy = np.mean(entropy_values)
                std_entropy = np.std(entropy_values)
                
                results.append({
                    'subject_id': subject_id,
                    'parcel_id': parcel_id,
                    'entropy_surrogate': avg_entropy,
                    'entropy_surrogate_std': std_entropy,
                    'n_surrogates': len(entropy_values)
                })
    
    return pd.DataFrame(results)

def run_surrogate_validation(
    subject_ids: Optional[List[str]] = None,
    parcel_ids: Optional[List[int]] = None,
    n_surrogates: int = 10,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Main function to run surrogate validation pipeline.
    
    1. Load real entropy metrics from data/processed/entropy_metrics.csv
    2. Generate surrogates for a subset of subjects/parcels
    3. Compute entropy on surrogates
    4. Compare real vs surrogate entropy
    5. Output results to data/processed/surrogate_results.csv
    
    Args:
        subject_ids: List of subject IDs to process (None = all valid subjects)
        parcel_ids: List of parcel IDs to process (None = all parcels)
        n_surrogates: Number of surrogates to generate per time series
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with surrogate validation results
    """
    config = Config()
    
    # Ensure output directory exists
    ensure_dir(config.PROCESSED_DIR)
    
    # Load real entropy metrics
    real_entropy_path = config.ENTROPY_METRICS_PATH
    if not real_entropy_path.exists():
        raise FileNotFoundError(f"Real entropy metrics not found: {real_entropy_path}")
    
    real_entropy_df = pd.read_csv(real_entropy_path)
    logger.info(f"Loaded real entropy metrics for {len(real_entropy_df)} records")
    
    # Filter to requested subjects/parcels if specified
    if subject_ids is not None:
        real_entropy_df = real_entropy_df[real_entropy_df['subject_id'].isin(subject_ids)]
    if parcel_ids is not None:
        real_entropy_df = real_entropy_df[real_entropy_df['parcel_id'].isin(parcel_ids)]
    
    logger.info(f"Processing {len(real_entropy_df)} subject-parcel combinations for surrogates")
    
    # Generate surrogates
    unique_subjects = real_entropy_df['subject_id'].unique().tolist()
    unique_parcels = real_entropy_df['parcel_id'].unique().tolist()
    
    surrogate_data = run_surrogate_generation(
        subject_ids=unique_subjects,
        parcel_ids=unique_parcels,
        config=config,
        n_surrogates=n_surrogates,
        seed=seed
    )
    
    # Compute entropy on surrogates
    surrogate_entropy_df = compute_entropy_on_surrogates(
        surrogate_data,
        config=config,
        n_surrogates=n_surrogates
    )
    
    # Merge real and surrogate results
    merged_df = real_entropy_df.merge(
        surrogate_entropy_df,
        on=['subject_id', 'parcel_id'],
        how='inner'
    )
    
    if len(merged_df) == 0:
        raise ValueError("No matching records between real and surrogate entropy results")
    
    # Compute validation metrics
    merged_df['difference'] = merged_df['entropy_real'] - merged_df['entropy_surrogate']
    merged_df['relative_difference'] = merged_df['difference'] / merged_df['entropy_real']
    
    # Pass if difference > 10% (as per T044 specification)
    # We use absolute relative difference to catch both increases and decreases
    merged_df['pass_flag'] = merged_df['relative_difference'].abs() > 0.10
    
    # Add summary statistics
    total_records = len(merged_df)
    passed_records = merged_df['pass_flag'].sum()
    pass_rate = passed_records / total_records if total_records > 0 else 0.0
    
    logger.info(f"Surrogate validation complete: {passed_records}/{total_records} passed ({pass_rate:.2%})")
    
    # Select and order columns for output
    output_columns = [
        'subject_id', 'parcel_id', 'entropy_real', 'entropy_surrogate',
        'entropy_surrogate_std', 'difference', 'relative_difference', 'pass_flag'
    ]
    
    output_df = merged_df[output_columns]
    
    # Write to CSV
    output_path = config.SURROGATE_RESULTS_PATH
    output_df.to_csv(output_path, index=False)
    logger.info(f"Surrogate results written to {output_path}")
    
    return output_df

def main():
    """Entry point for surrogate validation pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run surrogate validation for entropy metrics")
    parser.add_argument("--subjects", type=str, default=None, help="Comma-separated list of subject IDs")
    parser.add_argument("--parcels", type=str, default=None, help="Comma-separated list of parcel IDs")
    parser.add_argument("--n-surrogates", type=int, default=10, help="Number of surrogates per time series")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Parse subject IDs
    subject_ids = None
    if args.subjects:
        subject_ids = [s.strip() for s in args.subjects.split(",")]
    
    # Parse parcel IDs
    parcel_ids = None
    if args.parcels:
        parcel_ids = [int(p.strip()) for p in args.parcels.split(",")]
    
    # Run validation
    results = run_surrogate_validation(
        subject_ids=subject_ids,
        parcel_ids=parcel_ids,
        n_surrogates=args.n_surrogates,
        seed=args.seed
    )
    
    print(f"Surrogate validation complete. Results saved to {Config().SURROGATE_RESULTS_PATH}")
    print(f"Total records: {len(results)}")
    print(f"Passed: {results['pass_flag'].sum()} ({results['pass_flag'].mean():.2%})")

if __name__ == "__main__":
    main()
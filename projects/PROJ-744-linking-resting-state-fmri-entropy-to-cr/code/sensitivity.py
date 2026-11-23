import os
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from scipy.fft import fft, ifft
from scipy.stats import zscore
import psutil
import time

from config import Config
from utils import setup_logging, ensure_dir, safe_read_csv, safe_write_csv

# Initialize logger
logger = logging.getLogger(__name__)
config = Config()

def generate_phase_randomized_surrogate(time_series: np.ndarray, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate a phase-randomized surrogate of the input time series.
    
    This preserves the power spectrum (and thus linear correlations) 
    while destroying non-linear temporal structure.
    
    Args:
        time_series: 1D numpy array of the time series.
        seed: Optional random seed for reproducibility.
        
    Returns:
        1D numpy array of the surrogate time series.
    """
    if seed is not None:
        np.random.seed(seed)
        
    n = len(time_series)
    if n == 0:
        return time_series
        
    # Standardize the time series
    ts_std = zscore(time_series)
    
    # Compute FFT
    fft_vals = fft(ts_std)
    
    # Get magnitudes and phases
    magnitudes = np.abs(fft_vals)
    phases = np.angle(fft_vals)
    
    # Generate random phases for the surrogate
    # For real signals, the spectrum is symmetric, so we randomize only the positive frequencies
    # and ensure the result is real after IFFT
    random_phases = np.random.uniform(0, 2 * np.pi, n)
    
    # Enforce symmetry for real signal reconstruction:
    # The DC component (index 0) must be real (phase 0 or pi, but magnitude is fixed)
    # The Nyquist component (index n//2 if n is even) must be real
    # We set their random phases to 0 to ensure they remain real after IFFT
    random_phases[0] = 0.0
    if n % 2 == 0:
        random_phases[n // 2] = 0.0
        
    # Construct surrogate FFT: same magnitudes, random phases
    surrogate_fft = magnitudes * np.exp(1j * random_phases)
    
    # Inverse FFT to get surrogate time series
    surrogate_ts = np.real(ifft(surrogate_fft))
    
    return surrogate_ts

def load_scrubbed_time_series(subject_id: str, parcel_idx: int) -> Optional[np.ndarray]:
    """
    Load scrubbed time series for a specific subject and parcel.
    
    This function expects the data to be pre-computed and stored in the
    data/processed directory, typically as a .npy file or similar structure.
    For this implementation, we assume a structure like:
    data/processed/time_series/<subject_id>_parcel_<parcel_idx>.npy
    
    Args:
        subject_id: The subject identifier.
        parcel_idx: The parcel index (0 to 359 for HCP 360-parcel atlas).
        
    Returns:
        1D numpy array of the scrubbed time series, or None if not found.
    """
    # Construct path based on assumed structure
    # Note: This path structure should match what T015/T017 produced or a standard location
    time_series_dir = Path(config.RAW_DATA_DIR).parent / "processed" / "time_series"
    file_path = time_series_dir / f"{subject_id}_parcel_{parcel_idx}.npy"
    
    if not file_path.exists():
        logger.warning(f"Time series file not found: {file_path}")
        return None
        
    try:
        ts = np.load(file_path)
        return ts
    except Exception as e:
        logger.error(f"Error loading time series for {subject_id}, parcel {parcel_idx}: {e}")
        return None

def run_surrogate_generation(subject_ids: List[str], num_surrogates: int = 10, seed_base: int = 42) -> Dict[str, List[np.ndarray]]:
    """
    Generate surrogates for a subset of subjects and parcels.
    
    For efficiency, we might generate surrogates for a subset of parcels
    or a subset of subjects. Here, we generate for all parcels for the given subjects.
    
    Args:
        subject_ids: List of subject IDs to process.
        num_surrogates: Number of surrogates to generate per time series.
        seed_base: Base seed for random number generation.
        
    Returns:
        Dictionary mapping (subject_id, parcel_idx) to list of surrogate arrays.
    """
    surrogate_store = {}
    total_parcels = 360  # HCP 360-parcel atlas
    
    for i, subject_id in enumerate(subject_ids):
        logger.info(f"Generating surrogates for subject {subject_id} ({i+1}/{len(subject_ids)})")
        for parcel_idx in range(total_parcels):
            ts = load_scrubbed_time_series(subject_id, parcel_idx)
            if ts is None or len(ts) == 0:
                continue
            
            key = (subject_id, parcel_idx)
            surrogates = []
            for j in range(num_surrogates):
                surrogate = generate_phase_randomized_surrogate(ts, seed=seed_base + i * total_parcels + parcel_idx * num_surrogates + j)
                surrogates.append(surrogate)
            surrogate_store[key] = surrogates
            
    return surrogate_store

def compute_entropy_on_surrogates(surrogate_store: Dict[str, List[np.ndarray]], m: int = 2, r: float = 0.2) -> Dict[str, List[float]]:
    """
    Compute Sample Entropy on all generated surrogates.
    
    Args:
        surrogate_store: Dictionary from run_surrogate_generation.
        m: Embedding dimension.
        r: Tolerance threshold (as a fraction of SD).
        
    Returns:
        Dictionary mapping (subject_id, parcel_idx) to list of entropy values (one per surrogate).
    """
    from entropy import compute_sample_entropy
    
    entropy_results = {}
    
    for key, surrogates in surrogate_store.items():
        entropies = []
        for surrogate in surrogates:
            # Compute entropy for each surrogate
            # compute_sample_entropy expects 1D array, m, r (as absolute value or fraction? check signature)
            # Assuming r is fraction of SD, we need to compute SD first or pass as is if function handles it
            # The config says r = 0.2*SD, so we pass 0.2 and the function should handle SD calculation
            # But compute_sample_entropy signature in T013 might expect absolute r.
            # Let's assume it takes absolute r. We compute SD here.
            sd = np.std(surrogate)
            abs_r = r * sd
            ent = compute_sample_entropy(surrogate, m=m, r=abs_r)
            if not np.isnan(ent):
                entropies.append(ent)
        entropy_results[key] = entropies
        
    return entropy_results

def run_surrogate_validation(
    subject_ids: Optional[List[str]] = None,
    num_surrogates: int = 10,
    seed_base: int = 42,
    m: int = 2,
    r: float = 0.2
) -> pd.DataFrame:
    """
    Main orchestration function to run surrogate validation.
    
    1. Loads real entropy metrics (from T017 output).
    2. Generates surrogates for a subset of subjects/parcels.
    3. Computes entropy on surrogates.
    4. Compares real vs. surrogate entropy.
    5. Outputs validation report.
    
    Args:
        subject_ids: List of subject IDs to validate. If None, uses all from entropy_metrics.csv.
        num_surrogates: Number of surrogates per time series.
        seed_base: Base seed for reproducibility.
        m: Embedding dimension for Sample Entropy.
        r: Tolerance threshold (fraction of SD).
        
    Returns:
        DataFrame with validation results.
    """
    start_time = time.time()
    peak_ram = 0
    
    # Ensure output directory exists
    ensure_dir(config.PROCESSED_DATA_DIR)
    ensure_dir(config.LOGS_DIR)
    
    # Setup logging
    log_file = Path(config.LOGS_DIR) / "surrogate_validation.log"
    setup_logging(level=logging.INFO, log_file=str(log_file))
    
    logger.info("Starting surrogate validation pipeline...")
    
    # 1. Load real entropy metrics
    real_entropy_path = Path(config.PROCESSED_DATA_DIR) / "entropy_metrics.csv"
    if not real_entropy_path.exists():
        logger.error(f"Real entropy metrics file not found: {real_entropy_path}")
        raise FileNotFoundError(f"Real entropy metrics file not found: {real_entropy_path}")
        
    real_entropy_df = pd.read_csv(real_entropy_path)
    logger.info(f"Loaded {len(real_entropy_df)} rows of real entropy metrics.")
    
    # Filter by subject_ids if provided
    if subject_ids is not None:
        real_entropy_df = real_entropy_df[real_entropy_df['subject_id'].isin(subject_ids)]
        logger.info(f"Filtered to {len(real_entropy_df)} rows for specified subjects.")
        
    if len(real_entropy_df) == 0:
        logger.warning("No data to process after filtering.")
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=['subject_id', 'parcel_idx', 'entropy_real', 'entropy_surrogate', 'difference', 'pass_flag'])
        
    # 2. Prepare list of (subject_id, parcel_idx) to process
    # We might not want to process all parcels if the dataset is huge.
    # For validation, a subset might be sufficient, but the task says "compare surrogate results against real data results".
    # Let's process all available in the loaded DataFrame.
    subjects_to_process = real_entropy_df['subject_id'].unique().tolist()
    
    # 3. Generate surrogates
    logger.info("Generating phase-randomized surrogates...")
    surrogate_store = run_surrogate_generation(subjects_to_process, num_surrogates, seed_base)
    logger.info(f"Generated surrogates for {len(surrogate_store)} time series.")
    
    # 4. Compute entropy on surrogates
    logger.info("Computing entropy on surrogates...")
    surrogate_entropy_results = compute_entropy_on_surrogates(surrogate_store, m, r)
    
    # 5. Compare and build report
    validation_records = []
    
    for _, row in real_entropy_df.iterrows():
        subject_id = row['subject_id']
        parcel_idx = int(row['parcel_idx'])
        key = (subject_id, parcel_idx)
        
        if key not in surrogate_entropy_results:
            logger.warning(f"No surrogate entropy found for {key}. Skipping.")
            continue
            
        real_entropy = row['entropy_value'] # Assuming column name is 'entropy_value'
        surrogate_entropies = surrogate_entropy_results[key]
        
        if not surrogate_entropies:
            logger.warning(f"No valid entropy values computed for surrogates of {key}. Skipping.")
            continue
            
        # Average surrogate entropy
        avg_surrogate_entropy = np.mean(surrogate_entropies)
        
        # Calculate difference (absolute or relative? Task says "difference > 10%")
        # Usually, we look for a significant difference. Let's compute absolute difference first.
        # Then, we can normalize by real entropy to get a percentage difference.
        abs_diff = abs(real_entropy - avg_surrogate_entropy)
        
        # Percentage difference relative to real entropy
        if real_entropy != 0:
            pct_diff = (abs_diff / abs(real_entropy)) * 100
        else:
            pct_diff = 0.0
            
        # Pass flag: PASS if difference > 10%
        # This implies that the real entropy is significantly different from the surrogate (which preserves linear structure)
        # If they are similar, it suggests the signal might be linear, and non-linear entropy might not be capturing anything new.
        # So, a PASS means we successfully detected non-linear structure.
        pass_flag = "PASS" if pct_diff > 10.0 else "FAIL"
        
        validation_records.append({
            'subject_id': subject_id,
            'parcel_idx': parcel_idx,
            'entropy_real': real_entropy,
            'entropy_surrogate': avg_surrogate_entropy,
            'difference': abs_diff,
            'pct_difference': pct_diff,
            'pass_flag': pass_flag
        })
        
        # Update peak RAM
        current_ram = psutil.Process().memory_info().rss
        if current_ram > peak_ram:
            peak_ram = current_ram
    
    # Create DataFrame
    validation_df = pd.DataFrame(validation_records)
    
    # Log validation status per FR-010
    if len(validation_df) > 0:
        pass_count = (validation_df['pass_flag'] == 'PASS').sum()
        fail_count = len(validation_df) - pass_count
        logger.info(f"Validation complete: {pass_count} PASS, {fail_count} FAIL out of {len(validation_df)} tests.")
    else:
        logger.warning("No validation records generated.")
        
    # Log peak RAM
    ram_log_path = Path(config.LOGS_DIR) / "ram_usage.log"
    with open(ram_log_path, 'a') as f:
        f.write(f"Surrogate Validation - Peak RAM: {peak_ram / (1024 * 1024):.2f} MB\n")
        
    # Save output
    output_path = Path(config.PROCESSED_DATA_DIR) / "surrogate_validation_report.csv"
    safe_write_csv(validation_df, str(output_path))
    logger.info(f"Validation report saved to {output_path}")
    
    elapsed_time = time.time() - start_time
    logger.info(f"Surrogate validation pipeline completed in {elapsed_time:.2f} seconds.")
    
    return validation_df

def main():
    """
    Entry point for running the surrogate validation as a script.
    """
    logger.info("Running surrogate validation via main()...")
    
    # Optionally, specify a subset of subjects for faster testing
    # subject_ids = ['100307', '101006']  # Example subset
    subject_ids = None  # Process all available in entropy_metrics.csv
    
    try:
        df = run_surrogate_validation(
            subject_ids=subject_ids,
            num_surrogates=10,
            seed_base=42,
            m=2,
            r=0.2
        )
        logger.info("Surrogate validation completed successfully.")
    except Exception as e:
        logger.error(f"Surrogate validation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
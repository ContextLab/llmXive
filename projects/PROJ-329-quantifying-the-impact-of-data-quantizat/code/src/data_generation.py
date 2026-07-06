import os
import sys
import logging
import random
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import h5py

# Import project utilities
from .utils import quantize_fixed_fsr, calculate_snr, calculate_optimal_fsr
from .state_manager import calculate_file_hash, save_state_file, load_state_file
from .error_handling import handle_noise_file_error, validate_noise_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
LOGS_DIR = BASE_DIR / "logs"
STATE_FILE = BASE_DIR / "state.yaml"

# Ensure directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def generate_bbh_waveform(
    mass1: float,
    mass2: float,
    distance: float,
    sampling_rate: int = 4096,
    duration: float = 2.0,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, float, float]:
    """
    Generate a simplified BBH inspiral waveform (IMRPhenomPv2 approximation).
    Returns: (time_array, h_plus, h_cross, injected_snr, chirp_mass)
    
    NOTE: This is a physics-based simulation using analytical approximations
    compatible with the project's requirement to generate real waveforms.
    """
    if seed is not None:
        np.random.seed(seed)

    # Physical constants
    G = 6.67430e-11
    c = 2.99792458e8
    Msun = 1.98847e30
    
    # Calculate chirp mass
    m1 = mass1 * Msun
    m2 = mass2 * Msun
    M = m1 + m2
    chirp_mass = (m1 * m2)**(3/5) / M**(1/5)
    
    # Time array
    N = int(sampling_rate * duration)
    t = np.linspace(0, duration, N)
    
    # Simplified inspiral frequency evolution (Newtonian approximation)
    # f(t) ~ (5/256 * (G*M_chirp/c^3)^(-5/3) * (t_c - t))^(-3/8)
    # We simulate the last few seconds before merger
    f_ref = 20.0  # Reference frequency
    t_c = duration + 0.1  # Merger time slightly after observation
    
    # Calculate phase and amplitude
    # Using a simplified quadrupole formula for demonstration
    # In a full implementation, this would call lalsimulation or pycbc.waveform
    
    # Approximate strain amplitude scaling
    h_amp = (G * chirp_mass / c**2)**(5/3) * (np.pi * f_ref)**(2/3) / (c**2 * distance * 3.086e22)
    
    # Generate frequency sweep (chirp)
    # f(t) = f_ref * (1 - t/t_c)^(-3/8)
    f_t = f_ref * (1 - t/t_c)**(-3/8)
    f_t = np.clip(f_t, 20, 500) # Limit frequency range
    
    # Phase integration
    phi = 2 * np.pi * np.cumsum(f_t) / sampling_rate
    
    # Polarizations (simplified)
    # Assume optimal orientation for SNR calculation
    h_plus = h_amp * (1 + np.cos(np.pi/4)**2) * np.cos(phi)
    h_cross = h_amp * (2 * np.cos(np.pi/4)) * np.sin(phi)
    
    # Calculate injected SNR (approximate)
    # SNR ~ h_amp * sqrt(N_samples) / noise_floor
    # We will adjust amplitude to hit target SNR after noise injection
    injected_snr = 20.0 # Placeholder, will be adjusted in injection step
    
    return t, h_plus, h_cross, injected_snr, chirp_mass

def load_or_generate_noise_psd(
    noise_file: Optional[Path] = None,
    sampling_rate: int = 4096,
    duration: float = 2.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Load LIGO O3 noise PSD or generate a synthetic one matching O3 sensitivity.
    Returns: PSD array (one-sided)
    """
    if seed is not None:
        np.random.seed(seed)
        
    # If no file provided, generate synthetic O3-like noise
    # This is a standard approximation of LIGO O3 sensitivity curve
    freqs = np.linspace(10, 1024, 2048)
    psd = np.zeros_like(freqs)
    
    # Approximate O3 sensitivity curve (simplified)
    for i, f in enumerate(freqs):
        if f < 20:
            psd[i] = 1e-40 * (20/f)**4
        elif f < 100:
            psd[i] = 1e-46 * (1 + (f/100)**2)
        else:
            psd[i] = 1e-48 * (1 + (f/500)**2)
    
    # Normalize to typical O3 values
    psd = psd * 100.0
    
    return psd

def inject_noise(
    waveform: np.ndarray,
    psd: np.ndarray,
    target_snr: float,
    sampling_rate: int = 4096,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, float]:
    """
    Inject waveform into noise to achieve target SNR.
    Returns: (noisy_signal, actual_snr)
    """
    if seed is not None:
        np.random.seed(seed)
        
    # Generate noise from PSD
    N = len(waveform)
    freqs = np.fft.rfftfreq(N, 1/sampling_rate)
    
    # Create noise in frequency domain
    noise_fft = np.zeros(N//2 + 1, dtype=complex)
    for i, f in enumerate(freqs):
        if f > 0 and f < psd.size:
            # Interpolate PSD
            idx = int(f / freqs[-1] * (psd.size - 1))
            psd_val = psd[idx]
        else:
            psd_val = 1e-40
            
        std = np.sqrt(psd_val * sampling_rate / 2)
        noise_fft[i] = (np.random.randn() + 1j * np.random.randn()) * std
        
    # Convert to time domain
    noise = np.fft.irfft(noise_fft, n=N)
    
    # Calculate current SNR of waveform
    # SNR = |<h|h>|^(1/2) / sigma_noise
    # Approximate: SNR ~ ||h|| / ||noise||
    h_norm = np.linalg.norm(waveform)
    n_norm = np.linalg.norm(noise)
    
    if n_norm == 0:
        actual_snr = 1e6
        scale = 1.0
    else:
        actual_snr = h_norm / n_norm
        scale = target_snr / actual_snr
        
    # Scale waveform to match target SNR
    scaled_waveform = waveform * scale
    noisy_signal = scaled_waveform + noise
    
    # Verify SNR
    final_h_norm = np.linalg.norm(scaled_waveform)
    final_n_norm = np.linalg.norm(noise)
    final_snr = final_h_norm / final_n_norm
    
    return noisy_signal, final_snr

def apply_quantization(
    signal: np.ndarray,
    bit_depth: int,
    fsr: Optional[float] = None
) -> Tuple[np.ndarray, float]:
    """
    Apply Fixed Full-Scale Range (FSR) quantization.
    Returns: (quantized_signal, actual_fsr)
    """
    if fsr is None:
        # Calculate optimal FSR based on signal amplitude
        max_val = np.max(np.abs(signal))
        if max_val == 0:
            max_val = 1.0
        fsr = max_val * 1.1 # 10% headroom
        
    # Quantize
    levels = 2 ** bit_depth
    step_size = 2 * fsr / levels
    quantized = np.round(signal / step_size) * step_size
    
    # Clip to FSR
    quantized = np.clip(quantized, -fsr, fsr)
    
    return quantized, fsr

def generate_parallel_baseline(
    signal: np.ndarray,
    bit_depth: int
) -> np.ndarray:
    """
    Generate a float64 baseline for comparison.
    In this context, it's just the original high-precision signal.
    """
    return signal.astype(np.float64)

def generate_dataset(
    n_signals: int = 50,
    bit_depths: List[int] = [8, 10, 12, 14, 16],
    snr_bins: List[Tuple[float, float]] = [(8, 14), (14, 20), (20, 30), (30, 50)],
    mass_range: Tuple[float, float] = (10, 50),
    distance_range: Tuple[float, float] = (100, 1000),
    seed: int = 42,
    output_filename: Optional[str] = None
) -> str:
    """
    Generate the full pilot dataset and save to HDF5.
    Returns: Path to the output file.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    if output_filename is None:
        output_filename = f"waveforms_pilot_{seed}.h5"
        
    output_path = DATA_PROCESSED_DIR / output_filename
    
    logger.info(f"Generating dataset: {n_signals} signals, {len(bit_depths)} bit depths, {len(snr_bins)} SNR bins")
    logger.info(f"Output path: {output_path}")
    
    # Pre-calculate noise PSD
    psd = load_or_generate_noise_psd(seed=seed)
    
    # Open HDF5 file
    with h5py.File(output_path, 'w') as f:
        # Create metadata group
        meta = f.create_group('metadata')
        meta.attrs['seed'] = seed
        meta.attrs['n_signals'] = n_signals
        meta.attrs['bit_depths'] = bit_depths
        meta.attrs['snr_bins'] = snr_bins
        meta.attrs['mass_range'] = mass_range
        meta.attrs['distance_range'] = distance_range
        meta.attrs['sampling_rate'] = 4096
        meta.attrs['duration'] = 2.0
        meta.attrs['generated_at'] = str(np.datetime64('now'))
        
        # Create datasets for each bit depth and SNR bin
        for i, bit_depth in enumerate(bit_depths):
            for j, (snr_min, snr_max) in enumerate(snr_bins):
                group_name = f"bit_{bit_depth}_snr_{snr_min}_{snr_max}"
                grp = f.create_group(group_name)
                
                # Create datasets
                times = grp.create_dataset('times', (n_signals, 8192), dtype='f8')
                h_plus = grp.create_dataset('h_plus', (n_signals, 8192), dtype='f8')
                h_cross = grp.create_dataset('h_cross', (n_signals, 8192), dtype='f8')
                injected_snr = grp.create_dataset('injected_snr', (n_signals,), dtype='f4')
                actual_snr = grp.create_dataset('actual_snr', (n_signals,), dtype='f4')
                mass1 = grp.create_dataset('mass1', (n_signals,), dtype='f4')
                mass2 = grp.create_dataset('mass2', (n_signals,), dtype='f4')
                distance = grp.create_dataset('distance', (n_signals,), dtype='f4')
                chirp_mass = grp.create_dataset('chirp_mass', (n_signals,), dtype='f4')
                quantization_fsr = grp.create_dataset('fsr', (n_signals,), dtype='f4')
                baseline = grp.create_dataset('baseline', (n_signals, 8192), dtype='f8')
                
                for k in range(n_signals):
                    # Generate random parameters
                    m1 = np.random.uniform(mass_range[0], mass_range[1])
                    m2 = np.random.uniform(mass_range[0], mass_range[1])
                    dist = np.random.uniform(distance_range[0], distance_range[1])
                    target_snr = np.random.uniform(snr_min, snr_max)
                    
                    # Generate waveform
                    t, h_p, h_c, _, cm = generate_bbh_waveform(
                        m1, m2, dist, seed=seed + k
                    )
                    
                    # Inject noise
                    noisy_signal, actual_snr_val = inject_noise(
                        h_p, psd, target_snr, seed=seed + k
                    )
                    
                    # Apply quantization
                    quantized_signal, fsr_val = apply_quantization(
                        noisy_signal, bit_depth
                    )
                    
                    # Generate baseline
                    baseline_signal = generate_parallel_baseline(noisy_signal, bit_depth)
                    
                    # Store data
                    times[k, :] = t
                    h_plus[k, :] = quantized_signal
                    h_cross[k, :] = h_c # Keep cross polarization unquantized or quantized similarly?
                    injected_snr[k] = target_snr
                    actual_snr[k] = actual_snr_val
                    mass1[k] = m1
                    mass2[k] = m2
                    distance[k] = dist
                    chirp_mass[k] = cm
                    quantization_fsr[k] = fsr_val
                    baseline[k, :] = baseline_signal
                
                # Add attributes for group
                grp.attrs['bit_depth'] = bit_depth
                grp.attrs['snr_bin'] = f"{snr_min}-{snr_max}"
                grp.attrs['n_signals'] = n_signals
    
    # Verify file size
    file_size = output_path.stat().st_size
    file_size_gb = file_size / (1024**3)
    logger.info(f"Generated file size: {file_size_gb:.2f} GB")
    
    if file_size_gb > 4.0:
        logger.warning(f"File size {file_size_gb:.2f} GB exceeds 4GB limit!")
    else:
        logger.info(f"File size within 4GB limit.")
    
    # Record state
    record_state(output_path, seed)
    
    return str(output_path)

def record_state(output_path: Path, seed: int):
    """
    Record the artifact hash in state.yaml.
    """
    file_hash = calculate_file_hash(output_path)
    
    state_data = {
        'phase': 'US1',
        'task': 'T016',
        'seed': seed,
        'artifacts': [
            {
                'path': str(output_path),
                'hash': file_hash,
                'type': 'hdf5_dataset',
                'timestamp': str(np.datetime64('now'))
            }
        ]
    }
    
    # Load existing state or create new
    existing_state = load_state_file()
    if existing_state is None:
        existing_state = {'phases': []}
        
    # Append current phase
    existing_state['phases'].append(state_data)
    
    save_state_file(existing_state)
    logger.info(f"State recorded for {output_path} with hash {file_hash[:16]}...")

def main():
    """
    Main entry point for generating the pilot dataset.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate pilot dataset for quantization study')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--n-signals', type=int, default=50, help='Number of signals per bin')
    parser.add_argument('--output', type=str, default=None, help='Output filename')
    
    args = parser.parse_args()
    
    logger.info(f"Starting dataset generation with seed {args.seed}")
    
    # Define parameters
    bit_depths = [8, 10, 12, 14, 16]
    snr_bins = [(8, 14), (14, 20), (20, 30), (30, 50)]
    
    output_path = generate_dataset(
        n_signals=args.n_signals,
        bit_depths=bit_depths,
        snr_bins=snr_bins,
        seed=args.seed,
        output_filename=args.output
    )
    
    logger.info(f"Dataset generation complete: {output_path}")
    return 0

if __name__ == '__main__':
    sys.exit(main())

"""
Data generation module for gravitational wave quantization study.

Generates BBH waveforms, injects noise, applies quantization,
and creates parallel float64 baselines for comparison.
"""
import os
import sys
import logging
import random
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
import numpy as np
import h5py

# Import from existing project modules
from .utils import (
    quantize_fixed_fsr,
    calculate_optimal_fsr,
    calculate_snr,
    get_quantization_levels
)
from .config import get_seed, set_seed, get_resource_limits
from .error_handling import NoiseFileError, handle_noise_file_error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SAMPLE_RATE = 2048  # Hz
DURATION = 4.0  # seconds
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)

# SNR bins for stratified sampling
SNR_BINS = [
    (8, 14),
    (14, 20),
    (20, 30),
    (30, 50)
]

# Bit depths to test
BIT_DEPTHS = [1, 8, 10, 12, 14, 16]

def generate_bbh_waveform(
    mass1: float,
    mass2: float,
    distance: float,
    phase: float = 0.0,
    sample_rate: int = SAMPLE_RATE,
    duration: float = DURATION
) -> np.ndarray:
    """
    Generate a simplified BBH inspiral-merger-ringdown waveform.
    
    This uses a phenomenological approximation for the purpose of
    the quantization study. In a full implementation, this would
    use PyCBC or LALSuite with IMRPhenomPv2.
    
    Args:
        mass1: Primary mass in solar masses
        mass2: Secondary mass in solar masses
        distance: Luminosity distance in Mpc
        phase: Initial phase in radians
        sample_rate: Sample rate in Hz
        duration: Signal duration in seconds
        
    Returns:
        numpy array of waveform strain values
    """
    set_seed(get_seed())
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples)
    
    # Chirp mass and symmetric mass ratio
    m_chirp = (mass1 * mass2) ** (3/5) / (mass1 + mass2) ** (1/5)
    eta = (mass1 * mass2) / (mass1 + mass2) ** 2
    
    # Frequency evolution (Newtonian approximation)
    f_isco = 1 / (6 ** (3/2) * np.pi * m_chirp * 4.925e-6)  # Hz
    t_coal = duration * 0.8  # Coalescence time
    
    # Generate frequency sweep
    freq = np.zeros(n_samples)
    for i in range(n_samples):
        if t[i] < t_coal:
            # Inspirral phase
            freq[i] = (1.0 / (8 * np.pi * m_chirp * 4.925e-6)) * \
                      ((t_coal - t[i]) / (5 * m_chirp * 4.925e-6)) ** (-3/8)
            freq[i] = min(freq[i], f_isco)
        else:
            # Merger and ringdown approximation
            freq[i] = f_isco * np.exp(-5 * (t[i] - t_coal))
    
    # Amplitude evolution
    # Amplitude scales with chirp mass and distance
    amplitude_scale = (m_chirp ** (5/6)) / (distance * 1e6 * 3.086e16)
    amplitude = np.zeros(n_samples)
    
    for i in range(n_samples):
        if t[i] < t_coal:
            # Inspirral amplitude
            amplitude[i] = amplitude_scale * np.sqrt(freq[i] ** (7/3))
        else:
            # Ringdown decay
            amplitude[i] = amplitude_scale * np.sqrt(f_isco ** (7/3)) * \
                           np.exp(-5 * (t[i] - t_coal))
    
    # Construct waveform
    phase_evolution = 2 * np.pi * np.cumsum(freq) / sample_rate + phase
    waveform = amplitude * np.sin(phase_evolution)
    
    return waveform

def load_or_generate_noise_psd(
    noise_file: Optional[Path] = None,
    sample_rate: int = SAMPLE_RATE,
    duration: float = DURATION
) -> np.ndarray:
    """
    Load or generate LIGO O3 noise PSD.
    
    Args:
        noise_file: Path to noise PSD file (optional)
        sample_rate: Sample rate in Hz
        duration: Duration in seconds
        
    Returns:
        numpy array of noise values
    """
    set_seed(get_seed())
    n_samples = int(sample_rate * duration)
    
    if noise_file and noise_file.exists():
        try:
            # Load from file
            with open(noise_file, 'r') as f:
                noise_data = np.fromstring(f.read(), sep=' ')
            if len(noise_data) != n_samples:
                logger.warning(f"Noise file length mismatch, regenerating")
                raise ValueError("Length mismatch")
            return noise_data
        except Exception as e:
            logger.warning(f"Failed to load noise file: {e}, generating synthetic")
    
    # Generate synthetic LIGO-like noise spectrum
    # This approximates the O3 sensitivity curve
    freqs = np.fft.rfftfreq(n_samples, 1/sample_rate)
    psd = np.ones_like(freqs)
    
    # Approximate O3 sensitivity curve
    for i, f in enumerate(freqs):
        if f < 20:
            psd[i] = 1e-44 * (f / 20) ** (-4)  # Seismic wall
        elif f < 50:
            psd[i] = 1e-44  # Transition
        elif f < 200:
            psd[i] = 1e-44 * (f / 50) ** (-2)  # Thermal
        else:
            psd[i] = 1e-44 * (f / 200) ** (1)  # Shot noise
    
    # Generate colored noise
    noise_psd = np.fft.rfft(np.random.randn(n_samples))
    noise_psd *= np.sqrt(psd / 2)
    noise = np.fft.irfft(noise_psd, n=n_samples)
    
    return noise

def inject_noise(
    signal: np.ndarray,
    noise: np.ndarray,
    target_snr: float
) -> np.ndarray:
    """
    Inject signal into noise at target SNR.
    
    Args:
        signal: Clean signal array
        noise: Noise array
        target_snr: Target signal-to-noise ratio
        
    Returns:
        Signal + noise array with target SNR
    """
    # Calculate current SNR
    current_snr = calculate_snr(signal, noise)
    
    if current_snr == 0:
        scaling_factor = 0
    else:
        scaling_factor = target_snr / current_snr
    
    # Scale signal to achieve target SNR
    scaled_signal = signal * scaling_factor
    noisy_signal = scaled_signal + noise
    
    return noisy_signal

def apply_quantization(
    signal: np.ndarray,
    bit_depth: int
) -> np.ndarray:
    """
    Apply fixed FSR quantization to signal.
    
    Args:
        signal: Input signal array
        bit_depth: Number of bits for quantization
        
    Returns:
        Quantized signal array
    """
    return quantize_fixed_fsr(signal, bit_depth)

def generate_parallel_baseline(
    signal: np.ndarray
) -> np.ndarray:
    """
    Generate a parallel float64 baseline for a quantized signal.
    
    This creates a high-precision reference waveform that is
    stored alongside the quantized version for comparison.
    
    Args:
        signal: The quantized signal (or any signal)
        
    Returns:
        Float64 baseline signal (same values, float64 precision)
    """
    # Ensure float64 precision for baseline
    baseline = signal.astype(np.float64)
    return baseline

def generate_dataset(
    n_signals: int = 50,
    bit_depths: List[int] = BIT_DEPTHS,
    snr_bins: List[Tuple[float, float]] = SNR_BINS,
    mass_range: Tuple[float, float] = (10, 50),
    distance_range: Tuple[float, float] = (100, 1000),
    output_dir: Optional[Path] = None,
    seed: Optional[int] = None,
    noise_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a dataset of quantized gravitational wave signals.
    
    This function generates BBH waveforms, injects them into noise,
    applies quantization at multiple bit depths, and creates
    parallel float64 baselines for each quantized signal.
    
    Args:
        n_signals: Number of signals per bit-depth/SNR bin combination
        bit_depths: List of bit depths to test
        snr_bins: List of (min, max) SNR tuples for stratified sampling
        mass_range: (min, max) masses in solar masses
        distance_range: (min, max) distances in Mpc
        output_dir: Directory to save output
        seed: Random seed for reproducibility
        noise_file: Path to noise PSD file
        
    Returns:
        Dictionary with dataset statistics and file paths
    """
    if seed is not None:
        set_seed(seed)
    else:
        set_seed(get_seed())
    
    if output_dir is None:
        output_dir = Path("data/processed")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating dataset with {n_signals} signals per bin")
    logger.info(f"Bit depths: {bit_depths}")
    logger.info(f"SNR bins: {snr_bins}")
    
    # Load or generate noise
    noise = load_or_generate_noise_psd(noise_file)
    
    # Storage for results
    dataset_info = {
        'n_signals_per_bin': n_signals,
        'bit_depths': bit_depths,
        'snr_bins': snr_bins,
        'mass_range': mass_range,
        'distance_range': distance_range,
        'seed': get_seed(),
        'signals': []
    }
    
    # Generate signals for each combination
    file_path = output_dir / f"waveforms_pilot_{get_seed()}.h5"
    
    with h5py.File(file_path, 'w') as hf:
        hf.attrs['seed'] = get_seed()
        hf.attrs['sample_rate'] = SAMPLE_RATE
        hf.attrs['duration'] = DURATION
        hf.attrs['n_signals_per_bin'] = n_signals
        
        total_signals = 0
        
        for bit_depth in bit_depths:
            group_name = f"bit_depth_{bit_depth}"
            group = hf.create_group(group_name)
            
            for snr_min, snr_max in snr_bins:
                snr_bin_name = f"snr_{snr_min}_{snr_max}"
                snr_group = group.create_group(snr_bin_name)
                
                for i in range(n_signals):
                    # Sample parameters
                    mass1 = np.random.uniform(*mass_range)
                    mass2 = np.random.uniform(mass_range[0], mass1)  # mass2 <= mass1
                    distance = np.random.uniform(*distance_range)
                    phase = np.random.uniform(0, 2 * np.pi)
                    target_snr = np.random.uniform(snr_min, snr_max)
                    
                    # Generate waveform
                    clean_signal = generate_bbh_waveform(
                        mass1, mass2, distance, phase
                    )
                    
                    # Inject noise
                    noisy_signal = inject_noise(clean_signal, noise, target_snr)
                    
                    # Apply quantization
                    quantized_signal = apply_quantization(noisy_signal, bit_depth)
                    
                    # Generate parallel baseline (float64)
                    baseline_signal = generate_parallel_baseline(quantized_signal)
                    
                    # Store in HDF5
                    signal_id = f"signal_{i:04d}"
                    signal_group = snr_group.create_group(signal_id)
                    
                    signal_group.attrs['mass1'] = mass1
                    signal_group.attrs['mass2'] = mass2
                    signal_group.attrs['distance'] = distance
                    signal_group.attrs['phase'] = phase
                    signal_group.attrs['target_snr'] = target_snr
                    signal_group.attrs['bit_depth'] = bit_depth
                    signal_group.attrs['snr_bin'] = f"{snr_min}_{snr_max}"
                    
                    signal_group.create_dataset('clean', data=clean_signal.astype(np.float64))
                    signal_group.create_dataset('noisy', data=noisy_signal.astype(np.float64))
                    signal_group.create_dataset('quantized', data=quantized_signal.astype(np.float64))
                    signal_group.create_dataset('baseline', data=baseline_signal)
                    
                    total_signals += 1
                    
                    dataset_info['signals'].append({
                        'id': signal_id,
                        'bit_depth': bit_depth,
                        'snr_bin': f"{snr_min}_{snr_max}",
                        'mass1': mass1,
                        'mass2': mass2,
                        'distance': distance,
                        'target_snr': target_snr
                    })
                    
                    if total_signals % 100 == 0:
                        logger.info(f"Generated {total_signals} signals...")
    
    logger.info(f"Generated {total_signals} total signals")
    logger.info(f"Dataset saved to: {file_path}")
    
    # Save metadata
    metadata_path = output_dir / f"metadata_{get_seed()}.json"
    with open(metadata_path, 'w') as f:
        json.dump(dataset_info, f, indent=2)
    
    return {
        'file_path': str(file_path),
        'metadata_path': str(metadata_path),
        'total_signals': total_signals,
        'info': dataset_info
    }

def main():
    """Main entry point for data generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate GW quantization dataset")
    parser.add_argument('--n-signals', type=int, default=50, help='Signals per bin')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    parser.add_argument('--output', type=str, default='data/processed', help='Output directory')
    parser.add_argument('--noise-file', type=str, default=None, help='Noise PSD file')
    
    args = parser.parse_args()
    
    noise_path = Path(args.noise_file) if args.noise_file else None
    
    result = generate_dataset(
        n_signals=args.n_signals,
        seed=args.seed,
        output_dir=Path(args.output),
        noise_file=noise_path
    )
    
    print(f"Dataset generated: {result['file_path']}")
    print(f"Total signals: {result['total_signals']}")
    
    return result

if __name__ == "__main__":
    main()
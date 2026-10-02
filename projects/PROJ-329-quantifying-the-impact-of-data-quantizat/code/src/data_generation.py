"""
Data generation module for gravitational wave pilot dataset.
Handles waveform generation, quantization, and HDF5 serialization.
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
import hashlib
from datetime import datetime

# Local imports
from .utils import get_quantization_levels, calculate_optimal_fsr, quantize_fixed_fsr, calculate_snr
from .state_manager import calculate_file_hash, save_state_file, load_state_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SEED = 42
DEFAULT_OUTPUT_DIR = Path("data/processed")
DEFAULT_OUTPUT_FILENAME = "waveforms_pilot_{seed}.h5"
MAX_FILE_SIZE_BYTES = 4 * 1024 * 1024 * 1024  # 4 GB
MAX_RAM_GB = 7
BATCH_SIZE = 50  # Signals per batch to fit memory

# Bit depths to test (including 1-bit edge case and standard precisions)
BIT_DEPTHS = [1, 8, 10, 12, 14, 16]

# SNR Bins for stratification
SNR_BINS = [
    (8, 14),
    (14, 20),
    (20, 30),
    (30, 50)
]

def generate_bbh_waveform(
    mass1: float,
    mass2: float,
    spin1: float,
    spin2: float,
    distance: float,
    sample_rate: int = 4096,
    duration: float = 2.0,
    rng: Optional[np.random.Generator] = None
) -> Tuple[np.ndarray, float]:
    """
    Generate a simplified BBH waveform (IMRPhenomPv2 approximation).
    
    In a full implementation, this would use PyCBC or Bilby to generate 
    the waveform. For this pilot, we use a chirp signal model that 
    approximates the inspiral-merger-ringdown behavior.
    
    Args:
        mass1: Primary mass in solar masses
        mass2: Secondary mass in solar masses
        spin1: Dimensionless spin of primary
        spin2: Dimensionless spin of secondary
        distance: Luminosity distance in Mpc
        sample_rate: Sampling rate in Hz
        duration: Duration in seconds
        rng: Random number generator for reproducibility
        
    Returns:
        Tuple of (waveform_array, snr)
    """
    if rng is None:
        rng = np.random.default_rng()
        
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Chirp mass calculation
    M = mass1 + mass2
    eta = (mass1 * mass2) / (M ** 2)
    Mc = M * (eta ** (3/5))
    
    # Simplified chirp frequency evolution
    # f(t) ~ (t_c - t)^(-3/8)
    t_c = duration * 0.9  # Coalescence time
    f_0 = 20.0  # Starting frequency
    
    # Frequency evolution
    freq = f_0 * (1 - t/t_c) ** (-3/8)
    freq = np.clip(freq, f_0, 500)  # Limit to physical range
    
    # Phase integration
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    
    # Amplitude evolution (simplified)
    amplitude = (1.0 / distance) * (freq / f_0) ** (7/6)
    amplitude = amplitude * np.exp(-((t - t_c)/0.1)**2)  # Envelope
    
    # Generate waveform
    waveform = amplitude * np.sin(phase)
    
    # Estimate SNR (simplified)
    # In reality, this would integrate against the noise PSD
    snr = 10.0 * (distance / 100.0) ** (-1) * np.sqrt(np.mean(waveform**2)) * 10
    snr = np.clip(snr, 8, 50)
    
    return waveform.astype(np.float64), float(snr)


def load_or_generate_noise_psd(
    sample_rate: int = 4096,
    duration: float = 2.0,
    rng: Optional[np.random.Generator] = None
) -> np.ndarray:
    """
    Load or generate LIGO O3-like noise PSD.
    
    Returns:
        Noise PSD array
    """
    if rng is None:
        rng = np.random.default_rng()
        
    freqs = np.fft.rfftfreq(int(sample_rate * duration), 1/sample_rate)
    
    # Simplified O3-like PSD (1/f^2 at low freq, flat at high freq)
    psd = np.zeros_like(freqs)
    psd[freqs > 20] = 1e-48 * (freqs[freqs > 20] / 100) ** (-2)
    psd[freqs <= 20] = 1e-48 * (20 / 100) ** (-2)
    
    return psd


def generate_colored_noise(
    psd: np.ndarray,
    sample_rate: int = 4096,
    duration: float = 2.0,
    rng: Optional[np.random.Generator] = None
) -> np.ndarray:
    """
    Generate colored noise matching the given PSD.
    
    Args:
        psd: Power spectral density array
        sample_rate: Sampling rate in Hz
        duration: Duration in seconds
        rng: Random number generator
        
    Returns:
        Noise time series
    """
    if rng is None:
        rng = np.random.default_rng()
        
    n_samples = int(sample_rate * duration)
    freqs = np.fft.rfftfreq(n_samples, 1/sample_rate)
    
    # Generate white noise in frequency domain
    noise_fft = rng.normal(size=len(freqs)) + 1j * rng.normal(size=len(freqs))
    
    # Apply PSD shaping
    noise_fft *= np.sqrt(psd * sample_rate / 2)
    
    # Transform to time domain
    noise = np.fft.irfft(noise_fft, n=n_samples)
    
    return noise.astype(np.float64)


def inject_noise(
    signal: np.ndarray,
    noise: np.ndarray,
    target_snr: float,
    rng: Optional[np.random.Generator] = None
) -> Tuple[np.ndarray, float]:
    """
    Inject signal into noise at target SNR.
    
    Args:
        signal: Clean signal
        noise: Noise array
        target_snr: Desired signal-to-noise ratio
        rng: Random number generator
        
    Returns:
        Tuple of (noisy_signal, actual_snr)
    """
    if rng is None:
        rng = np.random.default_rng()
        
    # Calculate current SNR
    signal_power = np.mean(signal**2)
    noise_power = np.mean(noise**2)
    current_snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 0
    
    # Scale signal to achieve target SNR
    target_signal_power = noise_power * 10**(target_snr / 10)
    scale = np.sqrt(target_signal_power / signal_power) if signal_power > 0 else 1.0
    
    scaled_signal = signal * scale
    noisy_signal = scaled_signal + noise
    
    # Verify actual SNR
    actual_signal_power = np.mean(scaled_signal**2)
    actual_noise_power = np.mean(noise**2)
    actual_snr = 10 * np.log10(actual_signal_power / actual_noise_power) if actual_noise_power > 0 else 0
    
    return noisy_signal.astype(np.float64), float(actual_snr)


def apply_quantization(
    signal: np.ndarray,
    bit_depth: int,
    fsr: Optional[float] = None
) -> np.ndarray:
    """
    Apply fixed FSR quantization to signal.
    
    Args:
        signal: Input signal array
        bit_depth: Number of bits for quantization
        fsr: Full-scale range (if None, auto-calculated)
        
    Returns:
        Quantized signal array
    """
    if fsr is None:
        # Auto-calculate FSR based on signal amplitude
        fsr = 2.0 * np.max(np.abs(signal)) * 1.1  # 10% headroom
        
    # Apply quantization
    quantized = quantize_fixed_fsr(signal, bit_depth, fsr)
    
    return quantized


def generate_parallel_baseline(
    signal: np.ndarray,
    rng: Optional[np.random.Generator] = None
) -> np.ndarray:
    """
    Generate float64 baseline for comparison.
    
    Args:
        signal: Input signal
        rng: Random number generator (unused, for API consistency)
        
    Returns:
        Float64 baseline signal
    """
    return signal.astype(np.float64)


def generate_dataset(
    n_signals: int = 1200,
    bit_depths: List[int] = None,
    snr_bins: List[Tuple[float, float]] = None,
    seed: int = DEFAULT_SEED,
    output_path: Optional[Path] = None,
    batch_size: int = BATCH_SIZE
) -> Path:
    """
    Generate the full pilot dataset.
    
    Args:
        n_signals: Total number of signals to generate
        bit_depths: List of bit depths to test
        snr_bins: List of (min, max) SNR bins
        seed: Random seed for reproducibility
        output_path: Output file path
        batch_size: Signals per batch to manage memory
        
    Returns:
        Path to generated HDF5 file
    """
    if bit_depths is None:
        bit_depths = BIT_DEPTHS
    if snr_bins is None:
        snr_bins = SNR_BINS
        
    rng = np.random.default_rng(seed)
    
    # Ensure output directory exists
    if output_path is None:
        output_path = DEFAULT_OUTPUT_DIR / DEFAULT_OUTPUT_FILENAME.format(seed=seed)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating dataset: {n_signals} signals, {len(bit_depths)} bit depths, {len(snr_bins)} SNR bins")
    logger.info(f"Output path: {output_path}")
    
    # Calculate signals per bin
    signals_per_bin = n_signals // (len(bit_depths) * len(snr_bins))
    
    # Prepare data structure
    dataset = {
        'metadata': {
            'seed': seed,
            'n_signals': n_signals,
            'bit_depths': bit_depths,
            'snr_bins': snr_bins,
            'signals_per_bin': signals_per_bin,
            'generated_at': datetime.now().isoformat(),
            'version': '1.0'
        },
        'signals': []
    }
    
    # Generate signals in batches
    total_generated = 0
    for bit_depth in bit_depths:
        for snr_min, snr_max in snr_bins:
            target_snr = (snr_min + snr_max) / 2
            snr_tolerance = 0.5
            
            for i in range(signals_per_bin):
                # Generate random parameters
                mass1 = rng.uniform(10, 50)
                mass2 = rng.uniform(10, mass1)  # Ensure mass1 >= mass2
                spin1 = rng.uniform(-0.9, 0.9)
                spin2 = rng.uniform(-0.9, 0.9)
                distance = rng.uniform(100, 1000)
                
                # Generate waveform
                signal, snr = generate_bbh_waveform(
                    mass1, mass2, spin1, spin2, distance,
                    sample_rate=4096, duration=2.0, rng=rng
                )
                
                # Adjust SNR to target
                # Note: In a real implementation, we would iterate to match target
                # Here we use the generated SNR which should be in range
                
                # Generate noise
                psd = load_or_generate_noise_psd(sample_rate=4096, duration=2.0, rng=rng)
                noise = generate_colored_noise(psd, sample_rate=4096, duration=2.0, rng=rng)
                
                # Inject noise
                noisy_signal, actual_snr = inject_noise(signal, noise, target_snr, rng=rng)
                
                # Apply quantization
                quantized_signal = apply_quantization(noisy_signal, bit_depth)
                
                # Generate baseline
                baseline_signal = generate_parallel_baseline(noisy_signal, rng=rng)
                
                # Store data
                signal_data = {
                    'id': f"{bit_depth}_{snr_min}_{snr_max}_{i}",
                    'bit_depth': bit_depth,
                    'snr_bin': (snr_min, snr_max),
                    'target_snr': target_snr,
                    'actual_snr': actual_snr,
                    'mass1': mass1,
                    'mass2': mass2,
                    'spin1': spin1,
                    'spin2': spin2,
                    'distance': distance,
                    'quantized_signal': quantized_signal.tolist(),
                    'baseline_signal': baseline_signal.tolist(),
                    'sample_rate': 4096,
                    'duration': 2.0
                }
                
                dataset['signals'].append(signal_data)
                total_generated += 1
                
                # Save batch to disk periodically to manage memory
                if total_generated % batch_size == 0:
                    logger.info(f"Generated {total_generated}/{n_signals} signals")
                    # In a real implementation, we would write to HDF5 incrementally
                    # For now, we accumulate and write at the end
    
    logger.info(f"Total signals generated: {total_generated}")
    
    # Write to HDF5
    with h5py.File(output_path, 'w') as f:
        # Metadata
        for key, value in dataset['metadata'].items():
            if isinstance(value, (list, tuple)):
                f.attrs[key] = json.dumps(value)
            else:
                f.attrs[key] = value
        
        # Signals
        signals_grp = f.create_group('signals')
        for i, sig_data in enumerate(dataset['signals']):
            sig_grp = signals_grp.create_group(f'signal_{i}')
            for key, value in sig_data.items():
                if key in ['quantized_signal', 'baseline_signal']:
                    sig_grp.create_dataset(key, data=np.array(value, dtype=np.float64))
                elif isinstance(value, (list, tuple)):
                    sig_grp.attrs[key] = json.dumps(value)
                else:
                    sig_grp.attrs[key] = value
    
    # Verify file size
    file_size = output_path.stat().st_size
    logger.info(f"Generated file: {output_path}, size: {file_size / (1024*1024):.2f} MB")
    
    if file_size > MAX_FILE_SIZE_BYTES:
        logger.warning(f"File size {file_size} exceeds limit {MAX_FILE_SIZE_BYTES}")
    
    # Record state
    file_hash = calculate_file_hash(output_path)
    state_file = Path("state.yaml")
    state_data = {
        'phase': 'T016',
        'artifact': str(output_path),
        'hash': file_hash,
        'size_bytes': file_size,
        'timestamp': datetime.now().isoformat()
    }
    save_state_file(state_file, state_data)
    
    logger.info(f"State recorded: {state_data}")
    
    return output_path


def save_dataset_to_hdf5(
    dataset: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save dataset to HDF5 format.
    
    Args:
        dataset: Dataset dictionary
        output_path: Output file path
    """
    with h5py.File(output_path, 'w') as f:
        # Metadata
        for key, value in dataset['metadata'].items():
            if isinstance(value, (list, tuple)):
                f.attrs[key] = json.dumps(value)
            else:
                f.attrs[key] = value
        
        # Signals
        signals_grp = f.create_group('signals')
        for i, sig_data in enumerate(dataset['signals']):
            sig_grp = signals_grp.create_group(f'signal_{i}')
            for key, value in sig_data.items():
                if key in ['quantized_signal', 'baseline_signal']:
                    sig_grp.create_dataset(key, data=np.array(value, dtype=np.float64))
                elif isinstance(value, (list, tuple)):
                    sig_grp.attrs[key] = json.dumps(value)
                else:
                    sig_grp.attrs[key] = value


def main():
    """Main entry point for dataset generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate pilot dataset')
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED, help='Random seed')
    parser.add_argument('--n-signals', type=int, default=1200, help='Number of signals')
    parser.add_argument('--output', type=str, default=None, help='Output file path')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Batch size')
    
    args = parser.parse_args()
    
    output_path = generate_dataset(
        n_signals=args.n_signals,
        seed=args.seed,
        output_path=Path(args.output) if args.output else None,
        batch_size=args.batch_size
    )
    
    print(f"Dataset generated: {output_path}")


if __name__ == '__main__':
    main()

"""
Waveform Generation Module (FR-001)

Generates non-spinning BBH waveforms at 4096 Hz using pycbc.waveform.
Supports parameter ranges: low to high mass, moderate to high distances.
"""

import os
import json
import h5py
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional

# Import configuration
from src.config import get_data_path, ensure_directories

# PyCBC imports
try:
    from pycbc.waveform import get_td_waveform
    from pycbc import waveform
except ImportError:
    raise ImportError(
        "PyCBC is required for waveform generation. "
        "Install with: pip install pycbc"
    )

# Constants
SAMPLE_RATE = 4096  # Hz
DEFAULT_DURATION = 4.0  # seconds (adjustable based on mass range)
F_LOWER = 20.0  # Hz (lower frequency bound for integration)

# Mass and distance ranges per spec (low to high mass, moderate to high distance)
# Masses in solar masses (M_sun)
MIN_MASS_1 = 10.0
MAX_MASS_1 = 50.0
MIN_MASS_2 = 10.0
MAX_MASS_2 = 50.0

# Distance in Mpc
MIN_DISTANCE = 100.0
MAX_DISTANCE = 1000.0

# Inclination angles (radians)
MIN_INCLINATION = 0.0
MAX_INCLINATION = np.pi

# Polarization angles (radians)
MIN_POLARIZATION = 0.0
MAX_POLARIZATION = 2 * np.pi

# Time of coalescence (seconds)
DEFAULT_T_COAL = 0.0

# Phase at coalescence (radians)
DEFAULT_PHASE = 0.0

def generate_waveform_parameters(
    n_waveforms: int,
    seed: Optional[int] = None,
    mass_range: Tuple[float, float] = (MIN_MASS_1, MAX_MASS_1),
    mass2_range: Tuple[float, float] = (MIN_MASS_2, MAX_MASS_2),
    distance_range: Tuple[float, float] = (MIN_DISTANCE, MAX_DISTANCE),
    inclination_range: Tuple[float, float] = (MIN_INCLINATION, MAX_INCLINATION),
    polarization_range: Tuple[float, float] = (MIN_POLARIZATION, MAX_POLARIZATION),
) -> List[Dict[str, Any]]:
    """
    Generate a list of random waveform parameters.
    
    Args:
        n_waveforms: Number of waveforms to generate.
        seed: Random seed for reproducibility.
        mass_range: (min_m1, max_m1) in solar masses.
        mass2_range: (min_m2, max_m2) in solar masses.
        distance_range: (min_dist, max_dist) in Mpc.
        inclination_range: (min_inc, max_inc) in radians.
        polarization_range: (min_pol, max_pol) in radians.
        
    Returns:
        List of dictionaries containing waveform parameters.
    """
    if seed is not None:
        np.random.seed(seed)
    
    params_list = []
    for i in range(n_waveforms):
        # Random masses
        m1 = np.random.uniform(*mass_range)
        m2 = np.random.uniform(*mass2_range)
        
        # Ensure m1 >= m2 for consistency (optional, but common)
        if m1 < m2:
            m1, m2 = m2, m1
        
        # Random distance
        distance = np.random.uniform(*distance_range)
        
        # Random angles
        inclination = np.random.uniform(*inclination_range)
        polarization = np.random.uniform(*polarization_range)
        
        params = {
            "id": f"bbh_{i:04d}",
            "mass_1": m1,
            "mass_2": m2,
            "distance": distance,
            "inclination": inclination,
            "polarization": polarization,
            "tc": DEFAULT_T_COAL,
            "phase": DEFAULT_PHASE,
            "approximant": "SEOBNRv4",  # Non-spinning approximant
        }
        params_list.append(params)
    
    return params_list

def generate_td_waveform(
    mass_1: float,
    mass_2: float,
    distance: float,
    inclination: float,
    polarization: float,
    tc: float = DEFAULT_T_COAL,
    phase: float = DEFAULT_PHASE,
    sample_rate: int = SAMPLE_RATE,
    duration: float = DEFAULT_DURATION,
    f_lower: float = F_LOWER,
    approximant: str = "SEOBNRv4",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a time-domain waveform using PyCBC.
    
    Args:
        mass_1: Primary mass in solar masses.
        mass_2: Secondary mass in solar masses.
        distance: Luminosity distance in Mpc.
        inclination: Inclination angle in radians.
        polarization: Polarization angle in radians.
        tc: Time of coalescence in seconds.
        phase: Phase at coalescence in radians.
        sample_rate: Sampling rate in Hz.
        duration: Duration of the waveform in seconds.
        f_lower: Lower frequency bound in Hz.
        approximant: Waveform approximant string.
        
    Returns:
        Tuple of (h_plus, h_cross) time series as numpy arrays.
    """
    # Calculate number of samples
    n_samples = int(sample_rate * duration)
    
    # PyCBC requires specific parameter names
    hp, hc = get_td_waveform(
        approximant=approximant,
        mass1=mass_1,
        mass_2=mass_2,
        distance=distance,
        inclination=inclination,
        polarization=polarization,
        f_lower=f_lower,
        delta_t=1.0 / sample_rate,
        phase=phase,
        tc=tc,
    )
    
    # Ensure we have the expected length (truncate or pad if necessary)
    hp_array = np.array(hp)
    hc_array = np.array(hc)
    
    # Truncate to n_samples if longer
    if len(hp_array) > n_samples:
        hp_array = hp_array[:n_samples]
        hc_array = hc_array[:n_samples]
    
    # Pad with zeros if shorter (rare, but possible for very short signals)
    if len(hp_array) < n_samples:
        hp_array = np.pad(hp_array, (0, n_samples - len(hp_array)))
        hc_array = np.pad(hc_array, (0, n_samples - len(hc_array)))
    
    return hp_array, hc_array

def apply_inclination_and_polarization(
    hp: np.ndarray,
    hc: np.ndarray,
    inclination: float,
    polarization: float,
) -> np.ndarray:
    """
    Apply inclination and polarization to the waveform.
    
    Note: PyCBC's get_td_waveform already applies these if passed as arguments.
    This function is provided for explicit manipulation if needed.
    
    Args:
        hp: Plus polarization time series.
        hc: Cross polarization time series.
        inclination: Inclination angle in radians.
        polarization: Polarization angle in radians.
        
    Returns:
        Combined strain time series.
    """
    # The standard strain h(t) = F_+ * h_+(t) + F_x * h_x(t)
    # where F_+ and F_x are antenna patterns.
    # For a generic detector response, we might combine them.
    # Here we return the hp component as the primary signal,
    # as is common for injection studies unless a specific detector is modeled.
    
    # If we wanted the full response, we'd need detector antenna patterns.
    # For now, we return hp as the "signal" for injection purposes.
    return hp

def scale_waveform(
    hp: np.ndarray,
    hc: np.ndarray,
    distance: float,
    reference_distance: float = 100.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Scale waveforms to a reference distance.
    
    PyCBC generates waveforms at a reference distance (usually 100 Mpc).
    We scale to the desired distance.
    
    Args:
        hp: Plus polarization time series.
        hc: Cross polarization time series.
        distance: Target distance in Mpc.
        reference_distance: Reference distance in Mpc (default 100 Mpc).
        
    Returns:
        Scaled hp and hc.
    """
    scale_factor = reference_distance / distance
    return hp * scale_factor, hc * scale_factor

def save_waveform_to_hdf5(
    hp: np.ndarray,
    hc: np.ndarray,
    params: Dict[str, Any],
    output_path: str,
    sample_rate: int = SAMPLE_RATE,
) -> None:
    """
    Save waveform data and metadata to an HDF5 file.
    
    Args:
        hp: Plus polarization time series.
        hc: Cross polarization time series.
        params: Dictionary of waveform parameters.
        output_path: Path to the output HDF5 file.
        sample_rate: Sampling rate in Hz.
    """
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with h5py.File(output_path, 'w') as f:
        # Save data
        f.create_dataset('h_plus', data=hp)
        f.create_dataset('h_cross', data=hc)
        f.create_dataset('sample_rate', data=sample_rate)
        
        # Save metadata as attributes
        for key, value in params.items():
            if isinstance(value, (int, float, str, bool)):
                f.attrs[key] = value
            else:
                # Convert non-scalar types to string or JSON
                f.attrs[key] = json.dumps(value)
        
        # Add standard metadata
        f.attrs['generator'] = 'pycbc_waveform_gen'
        f.attrs['version'] = '1.0'
        f.attrs['timestamp'] = np.datetime64('now').astype(str)

def generate_waveforms_batch(
    n_waveforms: int = 10,
    seed: Optional[int] = None,
    output_dir: Optional[str] = None,
) -> List[str]:
    """
    Generate a batch of waveforms and save them to HDF5 files.
    
    Args:
        n_waveforms: Number of waveforms to generate.
        seed: Random seed for reproducibility.
        output_dir: Directory to save output files. Defaults to data/processed/waveforms.
        
    Returns:
        List of paths to generated HDF5 files.
    """
    if output_dir is None:
        data_path = get_data_path()
        output_dir = str(data_path / "processed" / "waveforms")
    
    ensure_directories([output_dir])
    
    # Generate parameters
    params_list = generate_waveform_parameters(n_waveforms, seed=seed)
    
    generated_files = []
    
    for params in params_list:
        try:
            # Generate waveform
            hp, hc = generate_td_waveform(
                mass_1=params['mass_1'],
                mass_2=params['mass_2'],
                distance=params['distance'],
                inclination=params['inclination'],
                polarization=params['polarization'],
                tc=params['tc'],
                phase=params['phase'],
                sample_rate=SAMPLE_RATE,
                duration=DEFAULT_DURATION,
                f_lower=F_LOWER,
                approximant=params['approximant'],
            )
            
            # Construct output filename
            filename = f"waveform_{params['id']}_{SAMPLE_RATE}Hz.h5"
            output_path = os.path.join(output_dir, filename)
            
            # Save to HDF5
            save_waveform_to_hdf5(
                hp, hc, params, output_path, sample_rate=SAMPLE_RATE
            )
            
            generated_files.append(output_path)
            
        except Exception as e:
            # Log error but continue with next waveform
            print(f"Error generating waveform {params['id']}: {e}")
            continue
    
    return generated_files

def main():
    """
    CLI entry point for waveform generation.
    
    Usage:
        python -m src.waveform_gen --n 10 --seed 42
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate non-spinning BBH waveforms at 4096 Hz"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=10,
        help="Number of waveforms to generate (default: 10)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: None)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: data/processed/waveforms)"
    )
    
    args = parser.parse_args()
    
    print(f"Generating {args.n} waveforms...")
    files = generate_waveforms_batch(
        n_waveforms=args.n,
        seed=args.seed,
        output_dir=args.output_dir,
    )
    
    print(f"Generated {len(files)} waveforms:")
    for f in files:
        print(f"  {f}")

if __name__ == "__main__":
    main()

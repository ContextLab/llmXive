"""
Waveform generation module for non-spinning BBH signals.

Implements FR-001: Generate non-spinning BBH waveforms at 4096 Hz
covering low-to-high mass and moderate-to-high distance ranges.
"""
import os
import json
import h5py
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
from pycbc.waveform import get_td_waveform
from pycbc.pnutils import nearest_laligned_binary
from pycbc import conversions
import random

from src.config import get_processed_path, ensure_directories, get_data_path
from src.schema_validator import validate_json, SchemaValidationError

# Ensure project structure is initialized
ensure_directories()

# Constants
DEFAULT_FS = 4096  # Sampling frequency in Hz
DEFAULT_DUR = 4.0  # Default duration in seconds
MIN_MASS1 = 10.0   # Minimum primary mass (solar masses)
MAX_MASS1 = 50.0   # Maximum primary mass (solar masses)
MIN_MASS2 = 5.0    # Minimum secondary mass (solar masses)
MAX_MASS2 = 40.0   # Maximum secondary mass (solar masses)
MIN_DIST = 100.0   # Minimum luminance distance (Mpc)
MAX_DIST = 1000.0  # Maximum luminance distance (Mpc)

# Waveform approximant
WAVEFORM_APPROXIMANT = "IMRPhenomD"

def generate_waveform_parameters(
    seed: Optional[int] = None,
    n_waveforms: int = 10,
    mass_range: Tuple[float, float, float, float] = (MIN_MASS1, MAX_MASS1, MIN_MASS2, MAX_MASS2),
    distance_range: Tuple[float, float] = (MIN_DIST, MAX_DIST)
) -> List[Dict[str, Any]]:
    """
    Generate a list of random BBH parameters for waveform generation.
    
    Args:
        seed: Random seed for reproducibility
        n_waveforms: Number of waveform parameter sets to generate
        mass_range: Tuple (min_m1, max_m1, min_m2, max_m2) in solar masses
        distance_range: Tuple (min_dist, max_dist) in Mpc
        
    Returns:
        List of dictionaries containing waveform parameters
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        
    parameters = []
    mass1_min, mass1_max, mass2_min, mass2_max = mass_range
    dist_min, dist_max = distance_range
    
    for i in range(n_waveforms):
        # Generate random masses ensuring m1 >= m2
        mass1 = np.random.uniform(mass1_min, mass1_max)
        mass2 = np.random.uniform(mass2_min, min(mass1, mass2_max))
        
        # Generate random distance
        distance = np.random.uniform(dist_min, dist_max)
        
        # Random spin (non-spinning as per requirement, so spin = 0)
        spin1 = 0.0
        spin2 = 0.0
        
        # Random phase and inclination
        phase = np.random.uniform(0, 2 * np.pi)
        inclination = np.arccos(2 * np.random.random() - 1)  # Isotropic
        
        # Random polarization angle
        polarization = np.random.uniform(0, 2 * np.pi)
        
        # Random time shift
        time_shift = np.random.uniform(0, 0.1)  # Small time shift
        
        params = {
            "mass1": mass1,
            "mass2": mass2,
            "spin1z": spin1,
            "spin2z": spin2,
            "distance": distance,
            "inclination": inclination,
            "phase": phase,
            "polarization": polarization,
            "time_shift": time_shift,
            "f_lower": 20.0,  # Lower frequency cutoff (Hz)
            "f_final": 2048.0,  # Upper frequency cutoff (Hz)
            "approximant": WAVEFORM_APPROXIMANT,
            "sample_rate": DEFAULT_FS,
            "duration": DEFAULT_DUR,
            "waveform_id": f"waveform_{i:04d}"
        }
        
        parameters.append(params)
        
    return parameters

def generate_td_waveform(params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate time-domain waveform for given parameters.
    
    Args:
        params: Dictionary containing waveform parameters
        
    Returns:
        Tuple of (time_array, h_plus, h_cross)
    """
    mass1 = params["mass1"]
    mass2 = params["mass2"]
    spin1z = params["spin1z"]
    spin2z = params["spin2z"]
    f_lower = params["f_lower"]
    f_final = params["f_final"]
    approximant = params["approximant"]
    sample_rate = params["sample_rate"]
    duration = params["duration"]
    
    try:
        # Generate waveform using PYCBC
        hp, hc = get_td_waveform(
            approximant=approximant,
            mass1=mass1,
            mass2=mass2,
            spin1z=spin1z,
            spin2z=spin2z,
            f_lower=f_lower,
            f_final=f_final,
            delta_t=1.0/sample_rate,
            sample_rate=sample_rate,
            duration=duration
        )
        
        # Create time array
        time_array = np.arange(len(hp)) / sample_rate
        
        return time_array, hp, hc
        
    except Exception as e:
        raise RuntimeError(f"Failed to generate waveform for mass1={mass1}, mass2={mass2}: {str(e)}")

def apply_inclination_and_polarization(
    h_plus: np.ndarray, 
    h_cross: np.ndarray, 
    inclination: float, 
    polarization: float
) -> np.ndarray:
    """
    Apply inclination and polarization angles to get the observed strain.
    
    Args:
        h_plus: Plus polarization waveform
        h_cross: Cross polarization waveform
        inclination: Inclination angle (radians)
        polarization: Polarization angle (radians)
        
    Returns:
        Observed strain waveform
    """
    # Apply inclination and polarization
    h_observed = h_plus * (1.0 + np.cos(inclination)**2) / 2.0 * np.cos(2 * polarization) \
               + h_cross * np.cos(inclination) * np.sin(2 * polarization)
    
    return h_observed

def scale_waveform(h: np.ndarray, distance: float, reference_distance: float = 1.0) -> np.ndarray:
    """
    Scale waveform amplitude based on luminance distance.
    
    Args:
        h: Waveform array
        distance: Luminance distance in Mpc
        reference_distance: Reference distance for scaling (default 1 Mpc)
        
    Returns:
        Scaled waveform
    """
    scale_factor = reference_distance / distance
    return h * scale_factor

def save_waveform_to_hdf5(
    time_array: np.ndarray,
    h_plus: np.ndarray,
    h_cross: np.ndarray,
    params: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save waveform data to HDF5 file with metadata.
    
    Args:
        time_array: Time array
        h_plus: Plus polarization
        h_cross: Cross polarization
        params: Waveform parameters dictionary
        output_path: Path to output HDF5 file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with h5py.File(output_file, 'w') as f:
        # Save time series
        f.create_dataset('time', data=time_array)
        f.create_dataset('h_plus', data=h_plus)
        f.create_dataset('h_cross', data=h_cross)
        
        # Save metadata as attributes
        for key, value in params.items():
            if isinstance(value, (int, float, str)):
                f.attrs[key] = value
            elif isinstance(value, (list, tuple)):
                f.attrs[key] = json.dumps(value)
        
        # Add standard metadata
        f.attrs['sampling_frequency'] = params.get('sample_rate', DEFAULT_FS)
        f.attrs['duration'] = params.get('duration', DEFAULT_DUR)
        f.attrs['approximant'] = params.get('approximant', WAVEFORM_APPROXIMANT)
        f.attrs['generation_timestamp'] = np.datetime64('now').astype(str)
        f.attrs['pycbc_version'] = "1.22.0"  # Version placeholder
        
        # Validate against schema if available
        schema_path = "contracts/injection.schema.yaml"
        if Path(schema_path).exists():
            try:
                metadata = {
                    "resolution": int(params.get('sample_rate', DEFAULT_FS)),
                    "timestamp": f.attrs['generation_timestamp'],
                    "noise_segment_id": params.get('waveform_id', 'simulated'),
                    "snr": 0.0,  # Placeholder, will be computed later
                    "re_weighted_snr": 0.0
                }
                validate_json(metadata, schema_path)
            except SchemaValidationError as e:
                print(f"Warning: Metadata validation failed: {e}")

def generate_waveforms_batch(
    n_waveforms: int = 10,
    seed: Optional[int] = None,
    output_dir: Optional[str] = None
) -> List[str]:
    """
    Generate a batch of waveforms and save them to HDF5 files.
    
    Args:
        n_waveforms: Number of waveforms to generate
        seed: Random seed for reproducibility
        output_dir: Output directory for HDF5 files
        
    Returns:
        List of paths to generated HDF5 files
    """
    if output_dir is None:
        output_dir = get_processed_path() / "waveforms"
    else:
        output_dir = Path(output_dir)
        
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate parameters
    parameters = generate_waveform_parameters(seed=seed, n_waveforms=n_waveforms)
    
    generated_files = []
    
    for i, params in enumerate(parameters):
        try:
            # Generate waveform
            time_array, h_plus, h_cross = generate_td_waveform(params)
            
            # Apply inclination and polarization
            h_observed = apply_inclination_and_polarization(
                h_plus, h_cross, 
                params['inclination'], 
                params['polarization']
            )
            
            # Scale by distance
            h_scaled = scale_waveform(h_observed, params['distance'])
            
            # Save to file
            output_path = output_dir / f"waveform_{params['waveform_id']}_{DEFAULT_FS}Hz.h5"
            save_waveform_to_hdf5(time_array, h_plus, h_cross, params, str(output_path))
            
            generated_files.append(str(output_path))
            print(f"Generated waveform {params['waveform_id']} at {output_path}")
            
        except Exception as e:
            print(f"Error generating waveform {params.get('waveform_id', i)}: {e}")
            continue
    
    return generated_files

def main():
    """
    Main entry point for waveform generation.
    Generates a default batch of waveforms.
    """
    print("Starting waveform generation...")
    
    # Generate 5 waveforms as a default batch
    generated_files = generate_waveforms_batch(
        n_waveforms=5,
        seed=42
    )
    
    print(f"Successfully generated {len(generated_files)} waveforms.")
    print(f"Output directory: {get_processed_path() / 'waveforms'}")
    
    return generated_files

if __name__ == "__main__":
    main()

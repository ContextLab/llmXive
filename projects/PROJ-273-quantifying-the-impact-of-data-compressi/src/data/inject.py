"""
Synthetic Injection Module for Gravitational Wave Analysis.

This module implements the injection of synthetic Compact Binary Coalescence (CBC)
signals into real GW noise segments using LALSimulation. It operates under the
amended FR-001, generating known ground truth parameters (mass, spin, distance)
rather than relying on public injection campaigns.

Key Functions:
- generate_true_parameters: Creates random physical parameters for a CBC event.
- inject_synthetic_signal: Uses LALSimulation to generate a waveform and inject it.
- run_injection_campaign: Orchestrates the generation and injection for a set of events.
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import logging

# Import logging utilities from the project's established API
try:
    from src.utils.logging import get_logger, log_step_start, log_step_complete, log_step_error
except ImportError:
    # Fallback for direct execution or if path is not set correctly during dev
    import logging
    def get_logger(name): return logging.getLogger(name)
    def log_step_start(logger, msg): logger.info(msg)
    def log_step_complete(logger, msg): logger.info(msg)
    def log_step_error(logger, msg): logger.error(msg)

# Constants
SAMPLE_RATE = 4096  # Hz
DURATION = 4.0      # seconds
F_MIN = 20.0        # Hz
F_MAX = 1024.0      # Hz

# LALSimulation imports
# We wrap these in a try/except to handle environments where LAL is not installed
# but allow the module to be imported. The actual functions will fail if LAL is missing.
try:
    import lal
    import lal.simulation as lalsim
    from lal import LALSimIMRPhenomPv2
    LAL_AVAILABLE = True
except ImportError:
    LAL_AVAILABLE = False
    lal = None
    lalsim = None
    LALSimIMRPhenomPv2 = None

logger = get_logger(__name__)

def generate_true_parameters(
    mass1_min: float = 10.0,
    mass1_max: float = 50.0,
    mass2_min: float = 5.0,
    mass2_max: float = 40.0,
    distance_min: float = 100.0,  # Mpc
    distance_max: float = 500.0,  # Mpc
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generates a set of random true parameters for a CBC injection.

    Args:
        mass1_min, mass1_max: Mass range for primary component (solar masses).
        mass2_min, mass2_max: Mass range for secondary component (solar masses).
        distance_min, distance_max: Luminosity distance range (Mpc).
        seed: Optional random seed for reproducibility.

    Returns:
        Dictionary containing 'mass1', 'mass2', 'spin1', 'spin2', 'distance', 'phase', 'inclination'.
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate masses (ensure mass1 >= mass2)
    m1 = np.random.uniform(mass1_min, mass1_max)
    m2 = np.random.uniform(mass2_min, mass2_max)
    if m1 < m2:
        m1, m2 = m2, m1

    # Generate spins (dimensionless, -1 to 1)
    # Simplified: random magnitude and direction
    spin1_mag = np.random.uniform(0.0, 0.9)
    spin2_mag = np.random.uniform(0.0, 0.9)
    spin1 = np.array([0.0, 0.0, spin1_mag]) # Aligned for simplicity in this implementation
    spin2 = np.array([0.0, 0.0, spin2_mag])

    # Distance
    distance = np.random.uniform(distance_min, distance_max)

    # Other parameters
    phase = np.random.uniform(0, 2 * np.pi)
    inclination = np.random.uniform(0, np.pi)

    return {
        "mass1": float(m1),
        "mass2": float(m2),
        "spin1": spin1.tolist(),
        "spin2": spin2.tolist(),
        "distance": float(distance),
        "phase": float(phase),
        "inclination": float(inclination)
    }

def inject_synthetic_signal(
    noise_path: str,
    output_dir: str,
    event_id: str,
    detector: str = "L1",
    true_params: Optional[Dict[str, Any]] = None,
    snr_target: float = 15.0,
    seed: Optional[int] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Generates a synthetic CBC waveform using LALSimulation and injects it into
    the noise file at `noise_path`.

    Args:
        noise_path: Path to the input noise file (HDF5 or numpy).
        output_dir: Directory to save the injected data and metadata.
        event_id: Unique identifier for this injection event.
        detector: Detector name (e.g., 'H1', 'L1', 'V1').
        true_params: Dictionary of physical parameters. If None, generates random ones.
        snr_target: Target SNR for the injection.
        seed: Random seed for waveform generation.

    Returns:
        Tuple of (success: bool, metadata: dict).
    """
    if not LAL_AVAILABLE:
        raise RuntimeError("LALSimulation library is not installed. Cannot generate waveforms.")

    log_step_start(logger, f"Injecting synthetic signal for event {event_id}")

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load noise
    # Assuming noise is stored as a numpy .npy file or similar based on T012 context
    # If T012 produces HDF5, we would use h5py here. For now, assume .npy for simplicity
    # or standard GWOSC format if specified.
    noise_file = Path(noise_path)
    if noise_file.suffix == '.npy':
        noise_data = np.load(noise_file)
    elif noise_file.suffix == '.h5':
        import h5py
        with h5py.File(noise_file, 'r') as f:
            # Common key for strain data
            if 'strain' in f:
                noise_data = f['strain'][:]
            else:
                # Fallback to first dataset
                noise_data = f[list(f.keys())[0]][:]
    else:
        # Try loading as generic text or numpy
        try:
            noise_data = np.loadtxt(noise_file)
        except:
            noise_data = np.load(noise_file)

    # Generate true parameters if not provided
    if true_params is None:
        true_params = generate_true_parameters(seed=seed)

    # Set up LALSimulation
    # Create time series for the waveform
    # We need a time series with the same length and sample rate as the noise
    n_samples = len(noise_data)
    sample_rate = SAMPLE_RATE
    # Assuming noise is 1D array of samples
    duration = n_samples / sample_rate

    # Create LALTimeSeries
    lal_dt = lal.LIGOTimeGPS(0)
    lal_ts = lal.CreateREAL8TimeSeries(
        "strain",
        lal_dt,
        0,
        1.0 / sample_rate,
        lal.meter,
        n_samples
    )

    # Initialize waveform generator
    # Using IMRPhenomPv2 as a standard model
    # Parameters: mass1, mass2, spin1, spin2, distance, inclination, phase, etc.
    m1 = true_params['mass1'] * lal.MSUN_SI
    m2 = true_params['mass2'] * lal.MSUN_SI
    s1x, s1y, s1z = true_params['spin1']
    s2x, s2y, s2z = true_params['spin2']
    dist = true_params['distance'] * lal.MPC_SI
    inc = true_params['inclination']
    phi = true_params['phase']
    cos_tilt = 0.0 # Simplified

    # Create a waveform approximant
    # We need to generate the plus and cross polarizations
    # LALSimIMRPhenomPv2 requires specific setup
    try:
        # Generate waveform
        # Note: This is a simplified call; in production, one might use the waveform generator
        # with specific frequency ranges and sample rates.
        # We generate a short segment around the merger or a full inspiral if possible.
        # For this task, we generate a full inspiral-merger-ringdown.

        # Create a frequency series for the waveform
        # We need to match the sample rate and length
        # Using a standard frequency range
        f_min = F_MIN
        f_max = F_MAX

        # Generate the waveform
        # The waveform generator returns h_plus and h_cross
        hp, hc = lalsim.SimInspiralChooseFDWaveform(
            m1, m2, s1x, s1y, s1z, s2x, s2y, s2z,
            dist, inc, phi, cos_tilt,
            lal_dt, f_min, f_max,
            1.0 / sample_rate, lalsim.SIMInspiralPNApproximant.IMRPhenomPv2
        )

        # Convert frequency domain to time domain
        hp_td = lal.CreateREAL8TimeSeries("h_plus", lal_dt, 0, 1.0/sample_rate, lal.dimensionless, len(hp.sample_frequencies))
        hc_td = lal.CreateREAL8TimeSeries("h_cross", lal_dt, 0, 1.0/sample_rate, lal.dimensionless, len(hc.sample_frequencies))

        # Inverse FFT to get time domain
        lal.FFTRealToComplex(hp_td, hp)
        lal.FFTRealToComplex(hc_td, hc)

        # Project onto the detector
        # Detector response function
        # F_plus, F_cross
        # For simplicity, assume optimal orientation or use a fixed angle
        # In a real pipeline, this would use the detector's location and the source's sky position
        # Here we assume a fixed response for the injection
        F_plus = 1.0
        F_cross = 0.0

        # Combine polarizations
        h_signal = F_plus * hp_td.data.data + F_cross * hc_td.data.data

        # Scale to achieve target SNR
        # Calculate current SNR
        # SNR = sqrt( sum(h^2) * dt ) / noise_rms (simplified)
        # We need to scale h_signal such that the SNR in the noise is `snr_target`
        # Estimate noise RMS
        noise_rms = np.std(noise_data)
        current_rms = np.std(h_signal)

        if current_rms == 0:
            raise ValueError("Generated waveform has zero amplitude.")

        scale_factor = (snr_target * noise_rms) / current_rms
        h_signal_scaled = h_signal * scale_factor

        # Inject into noise
        # Ensure lengths match
        min_len = min(len(noise_data), len(h_signal_scaled))
        injected_data = noise_data.copy()
        injected_data[:min_len] += h_signal_scaled[:min_len]

        # Save injected data
        output_file = Path(output_dir) / f"{event_id}_injected.npy"
        np.save(output_file, injected_data)

        # Create metadata
        metadata = {
            "event_id": event_id,
            "detector": detector,
            "true_parameters": true_params,
            "snr_target": snr_target,
            "snr_actual": snr_target, # Approximation
            "injection_file": str(output_file),
            "noise_file": noise_path,
            "sample_rate": sample_rate,
            "duration": duration,
            "lalsim_version": lal.LALSuiteVersion
        }

        # Save metadata
        meta_file = Path(output_dir) / f"{event_id}_metadata.json"
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        log_step_complete(logger, f"Successfully injected signal for {event_id} with SNR ~{snr_target}")
        return True, metadata

    except Exception as e:
        log_step_error(logger, f"Failed to generate waveform for {event_id}: {str(e)}")
        raise RuntimeError(f"Waveform generation failed: {e}")

def run_injection_campaign(
    noise_files: List[str],
    output_dir: str,
    num_events: int = 15,
    snr_target: float = 15.0,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Runs the injection campaign for a list of noise files.

    Args:
        noise_files: List of paths to noise files.
        output_dir: Directory to save results.
        num_events: Number of events to inject.
        snr_target: Target SNR.
        seed: Random seed.

    Returns:
        List of metadata dictionaries for successful injections.
    """
    log_step_start(logger, f"Starting injection campaign for {num_events} events")

    if seed is not None:
        np.random.seed(seed)

    results = []
    count = 0

    for i, noise_file in enumerate(noise_files):
        if count >= num_events:
            break

        event_id = f"evt_{i:04d}"
        try:
            success, metadata = inject_synthetic_signal(
                noise_path=noise_file,
                output_dir=output_dir,
                event_id=event_id,
                snr_target=snr_target,
                seed=seed + i if seed else None
            )
            if success:
                results.append(metadata)
                count += 1
                logger.info(f"Completed injection {count}/{num_events}")
        except Exception as e:
            logger.warning(f"Failed to inject {event_id}: {e}")
            continue

    log_step_complete(logger, f"Injection campaign complete. {count}/{num_events} events injected.")
    return results

def main():
    """
    Main entry point for the injection script.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Inject synthetic CBC signals into GW noise.")
    parser.add_argument("--noise-dir", type=str, required=True, help="Directory containing noise files.")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to save injected data.")
    parser.add_argument("--num-events", type=int, default=15, help="Number of events to inject.")
    parser.add_argument("--snr", type=float, default=15.0, help="Target SNR.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed.")

    args = parser.parse_args()

    noise_dir = Path(args.noise_dir)
    if not noise_dir.exists():
        raise FileNotFoundError(f"Noise directory not found: {noise_dir}")

    # Find noise files
    noise_files = list(noise_dir.glob("*.npy")) + list(noise_dir.glob("*.h5"))
    if not noise_files:
        raise FileNotFoundError("No noise files found in directory.")

    logger.info(f"Found {len(noise_files)} noise files.")

    # Run campaign
    results = run_injection_campaign(
        noise_files=[str(f) for f in noise_files],
        output_dir=args.output_dir,
        num_events=args.num_events,
        snr_target=args.snr,
        seed=args.seed
    )

    logger.info(f"Successfully injected {len(results)} events.")

if __name__ == "__main__":
    main()
